"""Trim verbose tool outputs BEFORE accumulation — context grows fast otherwise.

CCA-F trap: agent gets slower / loses focus after ~10 tool calls. The naive
fix is "increase max_tokens" or "use a bigger model". The real fix is to
truncate or summarize tool output AT THE BOUNDARY — before it ever enters
the conversation.

This script runs the same query twice:
  ❌ verbose tool — returns the full DB row dump (kitchen sink)
  ✅ trimmed tool — returns only the columns the caller needs

We track input_token usage across iterations to make the bloat visible.

Run: uv run domain-5-context/examples/02-trim-tool-outputs.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _shared.client import client


# Pretend orders DB. Each row is fat: 30+ columns, JSON metadata blobs.
ORDERS = [
    {
        "order_id": f"ord_{1000 + i}",
        "customer_id": f"cust_{(i % 5) + 1}",
        "status": ["shipped", "pending", "delivered", "cancelled"][i % 4],
        "total": 50.0 + i * 7.3,
        "items": [{"sku": f"SKU{j}", "qty": j + 1, "price": 10.0 * (j + 1)} for j in range(5)],
        # Verbose noise — useful for some workflows, useless for "list orders by status".
        "raw_payment_blob": "x" * 800,
        "carrier_metadata": {"tracking_url": "https://example.com/" + "y" * 200, "events": [{"ts": k, "msg": "z" * 100} for k in range(8)]},
        "audit_log": [f"event_{j}" for j in range(20)],
    }
    for i in range(40)
]


def list_orders_verbose(status: str) -> str:
    """❌ Returns the WHOLE row for every match. ~5 KB per row."""
    rows = [o for o in ORDERS if o["status"] == status]
    return json.dumps(rows)


def list_orders_trimmed(status: str) -> str:
    """✅ Returns only what the agent actually needs. ~80 bytes per row."""
    rows = [
        {"order_id": o["order_id"], "customer_id": o["customer_id"], "total": o["total"]}
        for o in ORDERS
        if o["status"] == status
    ]
    return json.dumps(rows)


TOOLS = [
    {
        "name": "list_orders",
        "description": "List orders filtered by status. Returns id, customer, total per row.",
        "input_schema": {
            "type": "object",
            "properties": {"status": {"type": "string"}},
            "required": ["status"],
        },
    }
]


def run(label: str, handler) -> None:
    print(f"\n=== {label} ===")
    messages = [{"role": "user", "content": "Show me all shipped, pending, and cancelled orders. Group totals by customer."}]
    cum_input = 0
    for it in range(5):
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=600,
            tools=TOOLS,
            messages=messages,
        )
        cum_input += resp.usage.input_tokens
        print(f"  iter {it + 1}: input_tokens={resp.usage.input_tokens:>5}  cumulative={cum_input:>6}  stop={resp.stop_reason}")
        if resp.stop_reason == "end_turn":
            break
        if resp.stop_reason != "tool_use":
            break
        messages.append({"role": "assistant", "content": resp.content})
        results = []
        for b in resp.content:
            if b.type == "tool_use":
                out = handler(**b.input)
                results.append({"type": "tool_result", "tool_use_id": b.id, "content": out})
        messages.append({"role": "user", "content": results})
    print(f"  TOTAL input tokens consumed: {cum_input}")


run("❌ verbose handler", list_orders_verbose)
run("✅ trimmed handler", list_orders_trimmed)
print(
    "\n=== Takeaway ===\n"
    "Same query, same model, same prompt. The trimmed handler keeps the agent "
    "operating on minimal data — input tokens grow more slowly across iterations, "
    "and the model has less noise to ignore."
)
