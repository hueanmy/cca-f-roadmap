"""Agentic loop — handle every stop_reason correctly.

CCA-F trap: students think the loop ends on `tool_use`. It doesn't.
- `tool_use`   → execute tools, append results, CONTINUE
- `end_turn`   → done, break
- `max_tokens` → response was cut off; for code agents, tell Claude to finalize
- `stop_sequence` → user-supplied stop matched; treat as done

Run: uv run domain-1-agentic/examples/01-agentic-loop.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _shared.client import client


def get_weather(city: str) -> str:
    fake = {"Hanoi": "29°C, humid", "Tokyo": "18°C, clear", "Berlin": "7°C, rain"}
    return json.dumps({"city": city, "report": fake.get(city, "no data")})


TOOLS = [
    {
        "name": "get_weather",
        "description": "Get current weather for a single city by name.",
        "input_schema": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    }
]

messages = [
    {"role": "user", "content": "Compare weather in Hanoi, Tokyo and Berlin. Be concise."}
]

MAX_ITERATIONS = 8

for iteration in range(MAX_ITERATIONS):
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        tools=TOOLS,
        messages=messages,
    )

    print(f"\n--- iter {iteration + 1} | stop_reason={response.stop_reason} ---")
    for block in response.content:
        if block.type == "text" and block.text.strip():
            print(f"Claude: {block.text}")

    # The four stop reasons — branch on each one explicitly.
    if response.stop_reason == "end_turn":
        break

    if response.stop_reason == "stop_sequence":
        # User-supplied stop sequence matched. Treat as done.
        break

    if response.stop_reason == "max_tokens":
        # Response was truncated. For most flows you'd ask Claude to continue,
        # but here we surface it so the loop doesn't silently keep churning.
        print("⚠️  hit max_tokens — increase budget or ask Claude to summarize")
        break

    if response.stop_reason == "tool_use":
        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"  → {block.name}({block.input})")
                if block.name == "get_weather":
                    result = get_weather(**block.input)
                else:
                    result = json.dumps({"error": f"unknown tool: {block.name}"})
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    }
                )

        messages.append({"role": "user", "content": tool_results})
        continue

    # Unknown stop_reason — fail fast rather than loop forever.
    raise RuntimeError(f"unhandled stop_reason: {response.stop_reason}")
else:
    print(f"\n⚠️  hit MAX_ITERATIONS={MAX_ITERATIONS} — possible infinite tool loop")
