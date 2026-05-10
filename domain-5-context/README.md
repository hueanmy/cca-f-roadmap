# Domain 5 — Context Management & Reliability

> **15% đề thi.** Smallest domain by weight, but its traps appear inside questions from other domains too — long-context handling shows up everywhere.

## Mental models cần nắm

- **M4** Lost-in-the-middle là constraint thật — key info ở đầu/cuối, không ở giữa
- **M5** Batch API vs real-time là **latency decision**, không phải cost decision

## Sub-topics

### - [ ] Lost-in-the-middle

> Model attention to information in the middle of long context degrades. Empirical, not theoretical.

**Tại sao matter:** Trap: "increase context window from 200k to 1M to fix recall." Sai. Bigger context ≠ better attention. Đáp án đúng: **chunk it**, put key context at start/end, use section headers, do per-chunk passes.

**Học gì cụ thể:**
- Place key context at **beginning** (best) or **end** (second best) of input
- Section headers (`## Customer info`, `## Order history`) help model navigate
- Per-file passes for codebase analysis — don't dump 50 files in one call
- "Needle in a haystack" benchmark ≠ realistic — synthesize, don't just retrieve

**Refs:** example: [`examples/01-lost-in-the-middle.py`](./examples/01-lost-in-the-middle.py)

---

### - [ ] Trim verbose tool outputs BEFORE accumulation

> Tool that returns 50 KB → after 10 calls = 500 KB → context bloat → degraded reasoning.

**Tại sao matter:** Đề: "agent slowing down after multiple tool calls." → answer is **trim tool outputs**, not "increase max_tokens".

**Học gì cụ thể:**
- Pattern: tool returns full payload to caller code; caller summarizes/truncates before sending to Claude
- Strategies: top-N rows, schema only (not full data), summary fields only, drop fields by allow-list
- Where to trim: **at the tool result boundary**, not later via summarization

**Refs:** example: [`examples/02-trim-tool-outputs.py`](./examples/02-trim-tool-outputs.py)

---

### - [ ] Handoff summary (mandatory fields)

> Subagent → coordinator handoff must include: customer ID, root cause, refund amount, recommended action.

**Tại sao matter:** Đề: subagent returned a paragraph; coordinator missed the action item. Fix = **structured handoff with required fields**, not "make subagent more verbose".

**Học gì cụ thể:**
- Force structure: subagent returns JSON object, not free-form text
- Required fields contract: missing = retry the subagent
- Same M3 mental model — subagent has no shared memory; the handoff IS the contract

---

### - [ ] Confidence calibration — external validation

> Same trap as Domain 4. Reinforced here from a context-management angle: don't ask the model "did you summarize correctly?" Use a separate validator.

**Học gì cụ thể:**
- LLM-as-judge ≠ ground truth. Useful as one signal, not the deciding signal
- Pattern: summarize → re-extract entities from summary → compare with entities from original → escalate if mismatch
- Cheaper: rule-based check (every required field present?)

---

### - [ ] Batch API vs real-time

> Batch: **50% cheaper**, **up-to-24h SLA**, no streaming. Use only for non-blocking jobs.

**🚨 CCA-F trap:** "Route ALL workflows through Batch API to save 50% cost."
Sai because:
- Customer-facing chat → real-time (sub-second response expected)
- Code agent → real-time (developer is waiting at the keyboard)
- Overnight enrichment → batch ✅
- Weekly report generation → batch ✅
- Bulk classification of historical data → batch ✅

**Tại sao matter:** Latency budget is the deciding question, not the cost question. If user/agent is blocking on the response, real-time is mandatory.

**Học gì cụ thể:**
- Batch endpoint: `client.messages.batches.create(...)` — submit a list of requests, poll for completion
- Status: `in_progress` → `ended` (success/failure per request)
- Use cases: bulk eval runs, historical data backfill, async report pipelines

**Refs:** [Batch API](https://docs.claude.com/en/docs/build-with-claude/batch-processing) · example: [`examples/03-batch-vs-realtime.py`](./examples/03-batch-vs-realtime.py)

---

### - [ ] Long context strategy

| Strategy | When |
|---|---|
| Per-file passes | Codebase analysis, multi-file refactor |
| Section headers | Composite documents (contract, RFC) |
| Explicit summary at top | Agent handoff, conversation continuation |
| Compaction | Long-running session, > 50% context used |
| Context editing | Pruning old turns surgically |

---

## Examples

- [01-lost-in-the-middle.py](./examples/01-lost-in-the-middle.py) — same info at beginning vs middle vs end → recall accuracy
- [02-trim-tool-outputs.py](./examples/02-trim-tool-outputs.py) — verbose-tool vs trimmed-tool, see context budget growth
- [03-batch-vs-realtime.py](./examples/03-batch-vs-realtime.py) — when to choose which

## Notes của tôi

> Học ngày: ___ · Insight: ___ · Confused: ___
