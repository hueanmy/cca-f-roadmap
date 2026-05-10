"""Tool budget — what happens when one agent has 18 tools vs 5.

CCA-F trap: "give one agent every tool for max flexibility."
Reality: tool selection accuracy degrades with tool count, especially when
descriptions overlap. The fix is not 'add few-shot' — it's split into
role-scoped agents (or just trim tools to 4-5).

This example sets up:
  ❌ FAT_AGENT  — 18 tools spanning 4 unrelated domains
  ✅ LEAN_AGENT — 5 tools, one domain (the one the query is in)

Same query, same model, different setup. Watch for missed/wrong selections.

Run: uv run domain-2-tools-mcp/examples/02-tool-budget.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _shared.client import client


def _t(name: str, desc: str) -> dict:
    return {
        "name": name,
        "description": desc,
        "input_schema": {"type": "object", "properties": {}},
    }


# Only the FIRST 5 tools are relevant to our test query (customer support).
# The rest are noise from unrelated domains: billing, code, infra.
LEAN_AGENT = [
    _t("get_customer", "Look up customer by email or phone."),
    _t("get_order_history", "Return last N orders for a verified customer."),
    _t("create_support_ticket", "File a support ticket with priority and category."),
    _t("escalate_to_human", "Page on-call human agent with current context."),
    _t("send_apology_email", "Send a templated apology email to a verified customer."),
]

FAT_AGENT = LEAN_AGENT + [
    # Unrelated billing tools
    _t("invoice_create", "Create a new invoice."),
    _t("invoice_void", "Void an existing invoice."),
    _t("payment_capture", "Capture an authorized payment."),
    _t("refund_partial", "Issue a partial refund."),
    # Unrelated code tools — descriptions intentionally similar to support tools
    _t("get_pull_request", "Look up a pull request."),
    _t("create_issue", "Open a new issue ticket."),
    _t("assign_reviewer", "Assign a code reviewer."),
    _t("merge_pr", "Merge an approved pull request."),
    # Unrelated infra
    _t("scale_service", "Scale a service replica count."),
    _t("rollback_deploy", "Roll back the last deployment."),
    _t("read_logs", "Read logs from a service."),
    _t("page_oncall", "Page the on-call engineer for an incident."),
    _t("restart_pod", "Restart a Kubernetes pod."),
]

QUERY = "alice@example.com is angry — her last 3 orders were late. Get her history and file a high-priority ticket."

# Expected: get_customer → get_order_history → create_support_ticket
# Plausible bad picks (in fat agent): create_issue, page_oncall, escalate_to_human (without context)


def run(label: str, tools: list[dict]) -> None:
    print(f"\n=== {label} ({len(tools)} tools) ===")
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        tools=tools,
        tool_choice={"type": "any"},
        messages=[{"role": "user", "content": QUERY}],
    )
    chosen = [b.name for b in resp.content if b.type == "tool_use"]
    print(f"  first turn picks: {chosen}")
    ideal = {"get_customer"}
    bad_signals = [t for t in chosen if t in {"create_issue", "page_oncall", "rollback_deploy", "merge_pr"}]
    print(f"  expected first call ∈ {ideal}: {'✅' if any(t in ideal for t in chosen) else '❌'}")
    if bad_signals:
        print(f"  ⚠️  unrelated picks: {bad_signals}  ← this is the failure mode")


run("✅ LEAN agent", LEAN_AGENT)
run("❌ FAT agent", FAT_AGENT)
print(
    "\nTakeaway: selection accuracy isn't only about description quality — it also "
    "scales inversely with tool count. The fix is fewer tools per agent, not "
    "longer system prompts."
)
