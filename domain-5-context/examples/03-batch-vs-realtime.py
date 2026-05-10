"""Batch vs real-time — how to make the latency decision.

CCA-F mental model M5: this is a LATENCY decision, not a cost decision.
The exam will give you a workflow and ask which API to use; the seductive
wrong answer is always "Batch — it's 50% cheaper."

The decision tree:
  Is a human or agent BLOCKING on this response?
    YES → real-time. End of decision.
    NO  → can the work tolerate up to 24h? YES → Batch (50% off).

This script demonstrates the Batch API surface for the second case
(historical data backfill) and also marks workflows that LOOK batchable
but are actually blocking.

Run: uv run domain-5-context/examples/03-batch-vs-realtime.py
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _shared.client import client


# Sample workflow descriptions — categorize each before reading the answer.
WORKFLOWS = [
    ("Customer-facing chat support agent", "real-time", "user is waiting"),
    ("IDE code completion", "real-time", "developer is blocking"),
    ("Nightly classification of yesterday's tickets for a dashboard", "batch", "no one waiting"),
    ("Weekly compliance scan over historical chat logs", "batch", "scheduled job, async"),
    ("Bulk re-embedding of a 2M-row product catalog", "batch", "offline pipeline"),
    ("Slack bot answering @mentions", "real-time", "user blocking on response"),
    ("Generating cover letters in a 'review queue' the user opens later", "batch", "user is decoupled — they read the queue when ready"),
    ("Triggering a payment based on Claude's classification", "real-time", "blocking the payment flow — and compliance: Domain 1 says use code, Domain 5 says don't put it in batch"),
]

print("=== Decide: batch or real-time? ===\n")
for desc, choice, why in WORKFLOWS:
    icon = "🟢" if choice == "real-time" else "🔵"
    print(f"  {icon} {choice:<10}  {desc}")
    print(f"      └─ {why}")


# ---------------------------------------------------------------------------
# A real Batch API call. Submit 5 classification requests, poll until done.
# Comment out / set DEMO=False if you don't want to actually spend the tokens.
# ---------------------------------------------------------------------------

DEMO = False

if DEMO:
    print("\n=== Submitting a real batch (DEMO=True) ===")
    requests = [
        {
            "custom_id": f"cls-{i}",
            "params": {
                "model": "claude-haiku-4-5",
                "max_tokens": 60,
                "messages": [
                    {"role": "user", "content": f"Classify the sentiment of: '{text}'. One word: positive/neutral/negative."}
                ],
            },
        }
        for i, text in enumerate(
            [
                "I love this product, would buy again",
                "It works fine I guess",
                "Worst experience of my life",
                "Solid value for the price",
                "Disappointed but support was helpful",
            ]
        )
    ]

    batch = client.messages.batches.create(requests=requests)
    print(f"  submitted batch: {batch.id}, processing_status={batch.processing_status}")

    # Poll. In real pipelines this is a separate scheduled worker, not a hot loop.
    while True:
        b = client.messages.batches.retrieve(batch.id)
        print(f"  status={b.processing_status}  counts={b.request_counts}")
        if b.processing_status == "ended":
            break
        time.sleep(5)

    # Stream results.
    for line in client.messages.batches.results(batch.id):
        print(f"  {line.custom_id}: {line.result}")
else:
    print("\n=== Skipping real batch submission (DEMO=False) ===")
    print("  Set DEMO=True at top of file to actually submit. Costs ~$0.0001 of Haiku tokens.")


print(
    "\n=== Recap ===\n"
    "- Batch is ~50% cheaper, async, up-to-24h SLA, no streaming.\n"
    "- Real-time has a sub-second p50 and supports streaming.\n"
    "- The exam will give you scenarios where Batch's cost saving is tempting\n"
    "  but the workflow is blocking. Always start from the latency question."
)
