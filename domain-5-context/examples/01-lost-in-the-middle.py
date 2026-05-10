"""Lost-in-the-middle — same key fact, three positions, three accuracy levels.

CCA-F mental model M4. We embed the same target fact ("project codename is
Hyperion-7") inside ~20 KB of distractor text at three different positions:
beginning, middle, end. Then we ask the same question and measure recall.

Result tends to be:
  beginning  ✅ recalled
  end        ✅ recalled
  middle     ❌ often missed or hallucinated

Run: uv run domain-5-context/examples/01-lost-in-the-middle.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _shared.client import client


# ~250 short distractor sentences. We splice the needle in at different indices.
DISTRACTORS = [
    f"Sentence {i}: routine project status — schedules updated, budgets reviewed, "
    f"no blockers reported in standup, follow-ups documented for engineering "
    f"team review on the next cycle."
    for i in range(250)
]
NEEDLE = "IMPORTANT FACT: The project codename is Hyperion-7."

QUESTION = "What is the project codename mentioned in the document?"


def make_doc(position: str) -> str:
    if position == "beginning":
        return NEEDLE + "\n\n" + "\n".join(DISTRACTORS)
    if position == "end":
        return "\n".join(DISTRACTORS) + "\n\n" + NEEDLE
    if position == "middle":
        mid = len(DISTRACTORS) // 2
        return "\n".join(DISTRACTORS[:mid]) + "\n\n" + NEEDLE + "\n\n" + "\n".join(DISTRACTORS[mid:])
    raise ValueError(position)


def ask(doc: str) -> str:
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=80,
        messages=[
            {
                "role": "user",
                "content": f"{doc}\n\n---\n\nQuestion: {QUESTION}\nAnswer in 1 short sentence.",
            }
        ],
    )
    return "".join(b.text for b in resp.content if b.type == "text").strip()


for pos in ("beginning", "middle", "end"):
    doc = make_doc(pos)
    print(f"\n--- needle position: {pos} (doc ≈ {len(doc):,} chars) ---")
    answer = ask(doc)
    correct = "Hyperion-7" in answer
    mark = "✅" if correct else "❌"
    print(f"  {mark} {answer}")

print(
    "\n=== Takeaway ===\n"
    "When you have to fit a long context in one call, put key facts at the "
    "BEGINNING or END. Better still: chunk and run per-chunk passes, then "
    "synthesize. The fix for missed-recall is structure, not bigger context."
)
