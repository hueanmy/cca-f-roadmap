"""Tool description quality — the single biggest factor in tool selection accuracy.

CCA-F mental model M2: tool description IS the routing mechanism.
This example runs 5 ambiguous queries against TWO sets of tools that have
identical NAMES and SCHEMAS but different DESCRIPTIONS — and shows how
selection accuracy changes.

Run: uv run domain-2-tools-mcp/examples/02-tool-description-quality.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _shared.client import client


# ❌ BAD — vague descriptions, lots of overlap
BAD_TOOLS = [
    {
        "name": "analyze_code",
        "description": "Analyzes code.",
        "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
    },
    {
        "name": "check_code",
        "description": "Checks code for issues.",
        "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
    },
    {
        "name": "inspect_code",
        "description": "Inspects code in detail.",
        "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
    },
]

# ✅ GOOD — explicit purpose, examples, boundaries vs siblings
GOOD_TOOLS = [
    {
        "name": "analyze_code",
        "description": (
            "Analyze STRUCTURE of a source file: imports, call graph, function/class "
            "list, cyclomatic complexity. Returns structural data only — does NOT "
            "evaluate quality or security. Use when the user asks 'what does this "
            "module do', 'list functions', 'how complex is X'. "
            "For style/lint issues use check_code. For security use inspect_code."
        ),
        "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
    },
    {
        "name": "check_code",
        "description": (
            "Check code QUALITY: linting, formatting, style violations, dead code, "
            "naming conventions. Returns a list of warnings with line numbers. Use "
            "when the user asks 'is this clean', 'find lint issues', 'review style'. "
            "For structural questions use analyze_code. For security use inspect_code."
        ),
        "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
    },
    {
        "name": "inspect_code",
        "description": (
            "Inspect code for SECURITY issues: hardcoded secrets, unsafe deserialization, "
            "SQL injection, CVE-tagged dependencies. Returns severity-ranked findings. "
            "Use when user asks 'is this safe', 'audit for vulnerabilities', 'check for "
            "secrets'. For style use check_code. For structure use analyze_code."
        ),
        "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
    },
]


QUERIES = [
    ("Are there any leaked API keys in handlers/auth.py?", "inspect_code"),
    ("List the public functions in services/billing.py.", "analyze_code"),
    ("Is the formatting in utils/parse.py up to our style guide?", "check_code"),
    ("Find any unsafe deserialization in api/upload.py.", "inspect_code"),
    ("How complex is the request_router function in router.py?", "analyze_code"),
]


def selection_accuracy(tools: list[dict]) -> tuple[int, int]:
    correct = 0
    for query, expected in QUERIES:
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=200,
            tools=tools,
            tool_choice={"type": "any"},  # force tool use to isolate selection
            messages=[{"role": "user", "content": query}],
        )
        chosen = next((b.name for b in resp.content if b.type == "tool_use"), None)
        ok = chosen == expected
        mark = "✅" if ok else "❌"
        print(f"  {mark} q={query[:55]!r:<60} → {chosen} (expected {expected})")
        if ok:
            correct += 1
    return correct, len(QUERIES)


print("=== BAD descriptions ===")
b_correct, b_total = selection_accuracy(BAD_TOOLS)
print(f"\nBad: {b_correct}/{b_total} correct\n")

print("=== GOOD descriptions ===")
g_correct, g_total = selection_accuracy(GOOD_TOOLS)
print(f"\nGood: {g_correct}/{g_total} correct\n")

print(f"Improvement: {b_correct}/{b_total} → {g_correct}/{g_total}")
print("Same names. Same schemas. Same model. Different routing accuracy.")
