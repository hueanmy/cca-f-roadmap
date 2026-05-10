"""Escalation routing — external signals beat self-reported confidence.

CCA-F trap: "ask the model 'how confident are you?' and route to a human
if confidence < 0.8." LLMs are mis-calibrated — confidence is least reliable
exactly when it most matters. The exam expects you to know two correct
patterns:

  ✅ Two-model agreement — run the task on a second model; disagreement = escalate
  ✅ External rule check — verify the answer against a deterministic rule
  ❌ Self-reported confidence number

This script runs the same classification task three ways on a known-hard
input and prints which routing decision each method makes.

Run: uv run domain-4-prompting/examples/03-escalation-routing.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _shared.client import client


# Deliberately ambiguous: could plausibly be billing OR shipping OR product_defect.
# A miscalibrated model may answer one of them with high stated confidence.
HARD_TICKET = (
    "I was charged $89 for an item that arrived dented. The shipping label "
    "shows it was tossed by the carrier. I'm tired of dealing with this."
)
LABELS = ["billing", "shipping", "product_defect", "other"]


def classify(model: str, ticket: str, ask_confidence: bool = False) -> dict:
    if ask_confidence:
        prompt = (
            f"Classify this ticket into one of {LABELS}. Also return your "
            f"confidence (0.0-1.0). JSON only: {{\"label\": ..., \"confidence\": ...}}\n\n"
            f"Ticket: {ticket}"
        )
    else:
        prompt = f"Classify this ticket into one of {LABELS}. Reply with the label only.\n\nTicket: {ticket}"

    resp = client.messages.create(
        model=model,
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text").strip()
    return text


# ---------------------------------------------------------------------------
# ❌ Pattern 1: Self-reported confidence
# ---------------------------------------------------------------------------
print("--- ❌ Self-reported confidence ---")
import json as _j
raw = classify("claude-sonnet-4-6", HARD_TICKET, ask_confidence=True)
print(f"  raw: {raw}")
try:
    parsed = _j.loads(raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip())
    decision = "auto-resolve" if parsed.get("confidence", 0) >= 0.8 else "escalate"
    print(f"  parsed: {parsed} → {decision}")
    print(f"  problem: even when this answer is wrong, the confidence is often ≥0.8")
except Exception as e:
    print(f"  parse failure: {e}")


# ---------------------------------------------------------------------------
# ✅ Pattern 2: Two-model agreement (Sonnet + Haiku)
# ---------------------------------------------------------------------------
print("\n--- ✅ Two-model agreement ---")
a = classify("claude-sonnet-4-6", HARD_TICKET).lower()
b = classify("claude-haiku-4-5", HARD_TICKET).lower()
print(f"  sonnet: {a!r}")
print(f"  haiku:  {b!r}")
agree = a == b
decision = "auto-resolve" if agree else "escalate"
print(f"  agree={agree} → {decision}")


# ---------------------------------------------------------------------------
# ✅ Pattern 3: External rule check (regex/keyword based)
# ---------------------------------------------------------------------------
print("\n--- ✅ External rule check ---")
# Simple rule set — in production you'd build this from labeled hard cases.
rules = {
    "billing": ["charge", "refund", "invoice", "payment", "$"],
    "shipping": ["arrived", "delivery", "carrier", "shipping label", "package", "delayed"],
    "product_defect": ["broken", "defective", "dented", "tampered", "damaged"],
}
predicted = classify("claude-sonnet-4-6", HARD_TICKET).lower().strip().strip('"')
print(f"  model said:   {predicted!r}")

ticket_lower = HARD_TICKET.lower()
matched_categories = [
    cat for cat, kws in rules.items() if any(kw in ticket_lower for kw in kws)
]
print(f"  rule signals: {matched_categories}")
ambiguous = len(matched_categories) > 1
decision = "escalate" if ambiguous else "auto-resolve"
print(f"  multiple rule signals → {decision} (the ticket touches multiple domains)")

print(
    "\n=== Takeaway ===\n"
    "The bad pattern *feels* like it works because Claude returns high-confidence "
    "numbers. The correct patterns escalate this ambiguous ticket — which is exactly "
    "what we want. External signals stay calibrated even when the model doesn't."
)
