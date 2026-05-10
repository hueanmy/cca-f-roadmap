# 6 Exam Scenarios

> Đề thi rút **4 trong 6** scenario này (random). Học cả 6 — không skip cái nào.

Mỗi scenario combine 2-3 domains. Cách học hiệu quả:

1. Đọc scenario summary
2. Tự liệt kê: domain nào liên quan? trap nào dễ rơi?
3. Mở đáp án, so sánh với guess của mình
4. Code lại pattern bằng examples ở các domain folder

---

## 1. Customer Support Resolution Agent

**Setup:** Production support chatbot phải triage ticket, look up customer, take refund action.

**Domains chính:** D1 (agentic loop, prerequisites), D4 (escalation routing), D5 (handoff, real-time vs batch)

**Traps phổ biến:**
- ❌ Few-shot để enforce `get_customer` → `process_refund` ordering
- ❌ Self-reported confidence cho human escalation
- ❌ Batch API cho "save 50% cost"
- ❌ Return empty khi tool fail im lặng

**Patterns đáp án thường thấy:**
- ✅ Programmatic prerequisites trong tool handler
- ✅ External signal cho escalation (không phải `confidence` field)
- ✅ Real-time API (user blocking)
- ✅ Structured error context

**Examples liên quan:** [`domain-1/02-programmatic-prerequisites.py`](../domain-1-agentic/examples/02-programmatic-prerequisites.py), [`domain-4/03-escalation-routing.py`](../domain-4-prompting/examples/03-escalation-routing.py)

---

## 2. Code Generation with Claude Code

**Setup:** Dev team adopt Claude Code, set up CLAUDE.md, custom commands, hooks cho test/format.

**Domains chính:** D3 (CLAUDE.md, commands, hooks), D2 (tool budget for the agent)

**Traps phổ biến:**
- ❌ Dump all 18 MCP tools cho code-writing agent
- ❌ CLAUDE.md 2000 dòng (waste context budget mỗi turn)
- ❌ Trust Claude phải nhớ format → quên khi long session
- ❌ Slash command vs Skill confusion

**Patterns đáp án:**
- ✅ Format-on-edit hook (deterministic)
- ✅ Project-level CLAUDE.md ngắn + `.claude/rules/` folder cho detail
- ✅ Slash command cho explicit user intent (`/cf-deploy`)
- ✅ Skill cho reactive workflows (skill description = trigger)

**Examples liên quan:** [`domain-3/CLAUDE.md.example`](../domain-3-claude-code/examples/CLAUDE.md.example), [`domain-3/hook-format-on-edit.json`](../domain-3-claude-code/examples/hook-format-on-edit.json)

---

## 3. Multi-Agent Research System

**Setup:** Research orchestrator spawns specialist agents (web search, doc reader, summarizer).

**Domains chính:** D1 (hub-and-spoke, subagent context), D2 (tool scoping per agent), D5 (handoff format)

**Traps phổ biến:**
- ❌ "Subagent inherits coordinator context" — sai
- ❌ Tăng context window thay vì split per-doc
- ❌ Lost-in-the-middle khi merge findings
- ❌ Subagent return paragraph thay vì JSON

**Patterns đáp án:**
- ✅ Explicit context passing trong prompt
- ✅ Per-doc / per-source subagent (parallel)
- ✅ Required-fields contract cho handoff
- ✅ Place key summaries at start of merged input

**Examples liên quan:** [`domain-1/03-multi-agent-handoff.py`](../domain-1-agentic/examples/03-multi-agent-handoff.py), [`domain-5/01-lost-in-the-middle.py`](../domain-5-context/examples/01-lost-in-the-middle.py)

---

## 4. Developer Productivity with Claude

**Setup:** Internal devtools team rolls out Claude wrappers — chat assistant, PR reviewer, refactor helper.

**Domains chính:** D3 (skills, slash commands, agents), D2 (tool boundaries between roles)

**Traps phổ biến:**
- ❌ One mega-agent với 30 tools "for flexibility"
- ❌ Skill description quá vague → load sai context
- ❌ Sharing CLAUDE.md/skill globally khi nên project-scoped

**Patterns đáp án:**
- ✅ Multi-agent: chat agent + reviewer agent + refactor agent, mỗi agent 4-5 tools
- ✅ Skill description theo perspective user ("Use when user asks for...")
- ✅ Project-level overrides user-level

**Examples liên quan:** [`domain-2/02-tool-budget.py`](../domain-2-tools-mcp/examples/02-tool-budget.py), [`domain-3/skill-example/SKILL.md`](../domain-3-claude-code/examples/skill-example/SKILL.md)

---

## 5. Claude Code for CI/CD

**Setup:** GitHub Actions runs Claude Code cho PR review, security scan, docs generation.

**Domains chính:** D3 (non-interactive mode, --allowedTools), D1 (hooks for safety)

**Traps phổ biến:**
- ❌ Plain `claude "review the PR"` → CI hangs
- ❌ `--dangerously-skip-permissions` cho mọi job
- ❌ Inject ANTHROPIC_API_KEY vào step env without secret rotation
- ❌ Allow `Bash(curl:*)` cho review job (data exfil risk)

**Patterns đáp án:**
- ✅ `claude -p "..." --output-format json`
- ✅ Scoped `--allowedTools` per job role
- ✅ Hook PreToolUse để block dangerous bash patterns
- ✅ storageState pattern cho automated browser tests

**Examples liên quan:** [`domain-3/ci-pipeline.sh`](../domain-3-claude-code/examples/ci-pipeline.sh), [`domain-3/hook-format-on-edit.json`](../domain-3-claude-code/examples/hook-format-on-edit.json)

---

## 6. Structured Data Extraction

**Setup:** Pipeline extract clinical/legal/financial data từ unstructured documents → DB.

**Domains chính:** D4 (schema enforcement, prompt chaining), D5 (long context strategy)

**Traps phổ biến:**
- ❌ "Just put 'return JSON with these fields' in prompt"
- ❌ Stuff entire 100-page doc into one call
- ❌ Few-shot để enforce field validation rules
- ❌ Trust Claude's `confidence` field for QA gating

**Patterns đáp án:**
- ✅ Defense in depth: schema (tool_use forced) + few-shot for distribution + retry on validation fail
- ✅ Per-section pass with section headers
- ✅ Code does deterministic parts (regex date, dict lookup) — LLM does the hard parts
- ✅ External validation re-extracts entities from summary

**Examples liên quan:** [`domain-4/01-structured-output.py`](../domain-4-prompting/examples/01-structured-output.py), [`domain-4/02-prompt-chaining.py`](../domain-4-prompting/examples/02-prompt-chaining.py)

---

## Mock exam strategy

1. Set timer 120 phút, làm full 60-câu mock (Udemy / claudecertifications.com / exampro)
2. Aim ≥ 750/1000 trước khi register thi thật
3. Đáp án **SAI** quan trọng hơn đáp án đúng — đọc explanation kỹ
4. Note xuống pattern: "câu này tôi rơi trap X vì lý do Y" → review trước hôm thi
