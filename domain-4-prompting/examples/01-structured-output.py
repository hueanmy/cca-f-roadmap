"""Defense in depth for structured output: schema + few-shot + retry.

CCA-F trap: "just put 'return JSON with these fields' in the prompt."
That works ~85% of the time, which means 15% production failures. Defense in
depth means three layers, each catching a different failure mode:

  1. SCHEMA via tool_use   — model is forced to produce a tool call matching
                             the schema shape. Drift caught at the protocol layer.
  2. FEW-SHOT (1-2 ex.)    — biases distribution toward your enum values and
                             field naming. Cheaper than rerunning.
  3. VALIDATION + RETRY    — catches semantic drift (wrong enum value, missing
                             cross-field invariant) and asks Claude to fix.

Run: uv run domain-4-prompting/examples/01-structured-output.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _shared.client import client


SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string", "maxLength": 200},
        "sentiment": {"type": "string", "enum": ["positive", "neutral", "negative"]},
        "urgency": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
        "category": {
            "type": "string",
            "enum": ["billing", "shipping", "product_defect", "feature_request", "other"],
        },
        "action_required": {"type": "boolean"},
    },
    "required": ["summary", "sentiment", "urgency", "category", "action_required"],
}


# We expose the SCHEMA as a fake "tool". Forcing tool_choice on this tool
# guarantees the model returns matching JSON — no parse-the-text-and-pray.
EXTRACT_TOOL = {
    "name": "record_ticket",
    "description": "Record a customer support ticket with structured fields.",
    "input_schema": SCHEMA,
}


# Layer 2: a single canonical example to bias the enum choices.
# (Style: not enforcing values, but anchoring the distribution.)
FEW_SHOT_USER = "I waited 2 weeks for my package and it arrived broken. I want a refund."
FEW_SHOT_ASSISTANT_TOOL_USE = {
    "summary": "Customer received a broken package after a 2-week shipping delay; requesting refund.",
    "sentiment": "negative",
    "urgency": "high",
    "category": "shipping",
    "action_required": True,
}


def extract(complaint: str, max_retries: int = 2) -> dict:
    messages = [
        {"role": "user", "content": FEW_SHOT_USER},
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_demo",
                    "name": "record_ticket",
                    "input": FEW_SHOT_ASSISTANT_TOOL_USE,
                }
            ],
        },
        {
            "role": "user",
            "content": [{"type": "tool_result", "tool_use_id": "toolu_demo", "content": "ok"}],
        },
        {"role": "user", "content": complaint},
    ]

    for attempt in range(max_retries + 1):
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            tools=[EXTRACT_TOOL],
            tool_choice={"type": "tool", "name": "record_ticket"},  # FORCE the schema
            messages=messages,
        )
        tool_use = next((b for b in resp.content if b.type == "tool_use"), None)
        if not tool_use:
            raise RuntimeError("model failed to emit tool_use even when forced")

        data = tool_use.input

        # Layer 3: semantic validation that schema can't catch.
        errors = []
        if data["urgency"] == "critical" and not data["action_required"]:
            errors.append("urgency=critical implies action_required=True")
        if len(data["summary"]) < 20:
            errors.append("summary is suspiciously short — please expand")

        if not errors:
            return data

        if attempt == max_retries:
            print(f"⚠️  validation still failing after {max_retries + 1} tries: {errors}")
            return data

        # Send the validation errors back so Claude can fix them on retry.
        print(f"   retry {attempt + 1}: {errors}")
        messages.append({"role": "assistant", "content": resp.content})
        messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": f"Validation failed: {'; '.join(errors)}. Re-emit with corrections.",
                        "is_error": True,
                    }
                ],
            }
        )


COMPLAINTS = [
    "My credit card was charged twice for the same order #4421. Need a refund ASAP.",
    "The new dark mode feature would be great if it actually persisted across reloads. Just a suggestion.",
    "Item 'A23' arrived but the seal was broken and contents leaking. Possibly tampered with.",
]

for c in COMPLAINTS:
    print(f"\n📨 {c[:70]}...")
    result = extract(c)
    print(json.dumps(result, indent=2, ensure_ascii=False))
