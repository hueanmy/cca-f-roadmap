"""Multi-agent hub-and-spoke — subagents do NOT inherit context.

CCA-F mental model M3: "Subagent không kế thừa context."
Trap: thinking the subagent automatically sees the coordinator's conversation.
It doesn't. You MUST pass everything explicitly in the subagent's prompt.

Pattern:
  1. Coordinator decides what to delegate
  2. Coordinator calls a NEW client.messages.create() with a self-contained prompt
  3. Subagent returns a summary
  4. Coordinator merges summaries

The subagent here is a separate API call — not a Task tool — so the isolation
is concrete and visible. (In Claude Code, the Task tool implements the same
pattern under the hood.)

Run: uv run domain-1-agentic/examples/03-multi-agent-handoff.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _shared.client import client


def research_subagent(topic: str, focus: str) -> dict:
    """A spoke agent. Cheaper model, narrow scope, isolated context.

    Note: it receives `topic` and `focus` as arguments — there's no magic
    inheritance from the coordinator. If we forgot to pass `focus`, the
    subagent would have no idea what we want.
    """
    prompt = (
        f"You are a research subagent. Investigate this topic in 3 bullet points.\n"
        f"Topic: {topic}\n"
        f"Focus on: {focus}\n"
        f"Return: bullets only, max 50 words total. No preamble."
    )
    resp = client.messages.create(
        model="claude-haiku-4-5",  # cheap model for narrow tasks
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text")
    return {
        "topic": topic,
        "focus": focus,
        "findings": text.strip(),
        # Structured error contract: if research failed, the spoke MUST surface it.
        # Returning empty would silently corrupt the coordinator's summary.
        "error": None,
    }


def coordinator(question: str) -> str:
    # Coordinator (Opus) plans which spokes to spawn.
    plan_resp = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=400,
        system=(
            "You are a research coordinator. Given a question, output 2-3 sub-topics "
            "to delegate, one per line, in the format `TOPIC | FOCUS`. No prose."
        ),
        messages=[{"role": "user", "content": question}],
    )
    plan_text = "".join(b.text for b in plan_resp.content if b.type == "text")
    print(f"📋 Coordinator plan:\n{plan_text}\n")

    # Spawn spokes. In a real app we'd use asyncio.gather for parallelism.
    findings = []
    for line in plan_text.strip().splitlines():
        if "|" not in line:
            continue
        topic, focus = (s.strip() for s in line.split("|", 1))
        topic = topic.lstrip("- ").lstrip("* ")
        print(f"🔎 spawn subagent — {topic} :: {focus}")
        result = research_subagent(topic, focus)
        if result["error"]:
            # Surface the error to the coordinator instead of dropping it.
            print(f"   ⚠️  spoke error: {result['error']}")
        findings.append(result)

    # Coordinator merges. We pass findings as STRUCTURED context — the merger
    # has no memory of the spokes either; everything it needs is in the prompt.
    merger_input = "\n\n".join(
        f"### {f['topic']} (focus: {f['focus']})\n{f['findings']}" for f in findings
    )
    merge_resp = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=600,
        system="Synthesize the research findings into a tight 4-bullet answer to the user's question.",
        messages=[
            {
                "role": "user",
                "content": f"Question: {question}\n\nFindings:\n{merger_input}",
            }
        ],
    )
    return "".join(b.text for b in merge_resp.content if b.type == "text")


answer = coordinator(
    "What are the main differences between Anthropic's Agent SDK and OpenAI's Assistants API?"
)
print("\n=== final answer ===\n")
print(answer)
