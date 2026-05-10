"""Structured error context — never return empty when a tool fails.

CCA-F trap: "subagent failed → coordinator returns empty result silently."
That's a compliance/observability disaster. The correct pattern is to return
a STRUCTURED error block so the parent agent (or the user) can decide what
to do — retry, escalate, or surface the failure.

Two contrasts demonstrated:
  ❌ silent_fetch     — swallows errors, returns ""
  ✅ structured_fetch — returns {"error": ..., "retryable": bool, "context": ...}

Run: uv run domain-1-agentic/examples/04-tool-error-handling.py
"""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _shared.client import client


# Simulated flaky upstream — fails ~50% of the time.
def flaky_upstream(order_id: str) -> dict:
    if random.random() < 0.5:
        raise TimeoutError(f"upstream timed out fetching {order_id}")
    return {"order_id": order_id, "status": "shipped", "total": 129.99}


def silent_fetch(order_id: str) -> str:
    """ANTI-PATTERN — what the trap answer looks like."""
    try:
        data = flaky_upstream(order_id)
        return json.dumps(data)
    except Exception:
        return ""  # 🚨 silent — coordinator now thinks "no data found"


def structured_fetch(order_id: str) -> str:
    """CORRECT pattern — return a typed error block."""
    try:
        data = flaky_upstream(order_id)
        return json.dumps({"ok": True, "data": data})
    except TimeoutError as e:
        return json.dumps(
            {
                "ok": False,
                "error": "UpstreamTimeout",
                "message": str(e),
                "retryable": True,
                "context": {"order_id": order_id},
            }
        )
    except Exception as e:
        return json.dumps(
            {
                "ok": False,
                "error": type(e).__name__,
                "message": str(e),
                "retryable": False,
                "context": {"order_id": order_id},
            }
        )


TOOLS = [
    {
        "name": "fetch_order",
        "description": "Fetch order details by ID. Returns {ok: bool, data | error}.",
        "input_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string"}},
            "required": ["order_id"],
        },
    }
]


def run_with_handler(handler, label: str) -> None:
    print(f"\n=== {label} ===")
    messages = [
        {"role": "user", "content": "What's the status of order ord_42? Try once. If it fails, tell me what happened."}
    ]
    for _ in range(4):
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
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
                out = handler(**b.input)
                print(f"  tool returned: {out!r}")
                results.append({"type": "tool_result", "tool_use_id": b.id, "content": out})
        messages.append({"role": "user", "content": results})


# Force the same RNG outcome for both runs so we can compare apples-to-apples.
random.seed(7)
run_with_handler(silent_fetch, "❌ silent handler — Claude is left guessing")
random.seed(7)
run_with_handler(structured_fetch, "✅ structured handler — Claude can reason about the failure")
