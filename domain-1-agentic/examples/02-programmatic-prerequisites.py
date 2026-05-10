"""Programmatic prerequisites — why few-shot CANNOT enforce ordering.

CCA-F trap (showed up multiple times in practice exams):
"How do you ensure `process_refund` is only called after `get_customer` verifies the ID?"
- ❌ "Add few-shot examples showing the correct ordering"      ← SEDUCTIVE WRONG ANSWER
- ❌ "Add a strong system prompt: 'always verify first'"       ← also wrong (probabilistic)
- ✅ "Block process_refund at the tool handler until state shows verified ID"

The correct answer is DETERMINISTIC code, because financial actions have
real-world consequence. Prompts are probabilistic — they fail occasionally,
which is unacceptable for compliance.

Run: uv run domain-1-agentic/examples/02-programmatic-prerequisites.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _shared.client import client


# Per-session state. In real systems this lives in a DB row keyed by session_id.
SESSION_STATE: dict[str, dict] = {}


def get_customer(session_id: str, email: str) -> str:
    """Verify a customer by email and stamp the session as verified."""
    # Pretend we hit a DB. Real systems would also rate-limit / log.
    customer = {"id": "cust_42", "email": email, "name": "Alice", "tier": "gold"}
    SESSION_STATE.setdefault(session_id, {})["verified_customer"] = customer
    return json.dumps(customer)


def process_refund(session_id: str, amount: float) -> str:
    """Process a refund — but ONLY if the session has a verified customer."""
    state = SESSION_STATE.get(session_id, {})
    if "verified_customer" not in state:
        # Hard block — return a structured error, not a friendly text message.
        # Claude reads this and learns to call get_customer first. Deterministic.
        return json.dumps(
            {
                "error": "PrerequisiteError",
                "message": "process_refund requires a verified customer; call get_customer first",
                "required_tool": "get_customer",
            }
        )
    return json.dumps(
        {"refund_id": "rf_99", "amount": amount, "customer_id": state["verified_customer"]["id"]}
    )


TOOLS = [
    {
        "name": "get_customer",
        "description": "Look up and verify a customer by their email address.",
        "input_schema": {
            "type": "object",
            "properties": {"email": {"type": "string"}},
            "required": ["email"],
        },
    },
    {
        "name": "process_refund",
        "description": "Issue a refund to the verified customer. Requires get_customer to have run first in this session.",
        "input_schema": {
            "type": "object",
            "properties": {"amount": {"type": "number"}},
            "required": ["amount"],
        },
    },
]


def run(session_id: str, user_msg: str) -> None:
    messages = [{"role": "user", "content": user_msg}]
    for _ in range(8):
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            # Note: NO few-shot examples, NO system prompt about ordering.
            # The prerequisite is enforced by the tool handler, not by Claude.
            tools=TOOLS,
            messages=messages,
        )
        for b in resp.content:
            if b.type == "text" and b.text.strip():
                print(f"Claude: {b.text}")

        if resp.stop_reason == "end_turn":
            return
        if resp.stop_reason != "tool_use":
            return

        messages.append({"role": "assistant", "content": resp.content})
        results = []
        for b in resp.content:
            if b.type == "tool_use":
                print(f"  → {b.name}({b.input})")
                if b.name == "get_customer":
                    out = get_customer(session_id, **b.input)
                elif b.name == "process_refund":
                    out = process_refund(session_id, **b.input)
                else:
                    out = json.dumps({"error": "unknown tool"})
                print(f"    ← {out}")
                results.append({"type": "tool_result", "tool_use_id": b.id, "content": out})
        messages.append({"role": "user", "content": results})


print("=== Run 1: user asks for refund WITHOUT giving an email ===")
print("Watch Claude attempt process_refund first; the tool blocks it; Claude self-corrects.\n")
run("sess_1", "Refund $50 for the last order please.")

print("\n=== Run 2: user gives email up front ===")
print("Claude verifies first, then refunds. Same code, different prompt — both work.\n")
run("sess_2", "I'm alice@example.com — please refund $50 for my last order.")
