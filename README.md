# CCA-F Study Roadmap

> Lộ trình ôn thi **Claude Certified Architect — Foundations (CCA-F)** trong **30h · 4 tuần**, kèm working examples chạy được cho mọi trap và mental model.
> Companion repo của [hueanmy.github.io/cca-f-roadmap.html](https://hueanmy.github.io/cca-f-roadmap.html).

[Tiếng Việt](#tiếng-việt) · [English](#english)

---

## Tiếng Việt

Repo này là **journal ôn thi public** — code mọi trap & pattern thật sự thay vì chỉ đọc lý thuyết. Đề CCA-F là scenario-based, không phải trivia: bạn cần engineering judgment, không phải thuộc lòng.

### Format kỳ thi

| | |
|---|---|
| Số câu | 60 (4/6 scenarios random) |
| Thời gian | 120 phút |
| Pass | 720/1000 |
| Phí | $99 |

### 5 Domains

| # | Domain | Folder | Trọng số | Học gì |
|---|---|---|---|---|
| 1 | Agentic Architecture & Orchestration | [domain-1-agentic/](./domain-1-agentic/) | **27%** | Agentic loop, hub-and-spoke, subagents, hooks, prompt chaining, sessions |
| 2 | Tool Design & MCP Integration | [domain-2-tools-mcp/](./domain-2-tools-mcp/) | 18% | Tool descriptions, naming, MCP scoping, tool budget |
| 3 | Claude Code Configuration & Workflows | [domain-3-claude-code/](./domain-3-claude-code/) | 20% | CLAUDE.md hierarchy, skills, slash commands, CI/CD |
| 4 | Prompt Engineering & Structured Output | [domain-4-prompting/](./domain-4-prompting/) | 20% | JSON schema, few-shot ranges, prompt chaining, escalation routing |
| 5 | Context Management & Reliability | [domain-5-context/](./domain-5-context/) | 15% | Lost-in-the-middle, trim, handoff summaries, batch vs real-time |

### 6 Exam Scenarios (học hết, thi random 4)

Xem [scenarios/](./scenarios/) — mỗi scenario kết hợp 2-3 domains.

1. Customer Support Resolution Agent
2. Code Generation with Claude Code
3. Multi-Agent Research System
4. Developer Productivity with Claude
5. Claude Code for CI/CD
6. Structured Data Extraction

### Cách dùng repo

**Setup 1 lần:**

```bash
# Cần Python 3.11+ và uv (https://docs.astral.sh/uv/)
git clone https://github.com/hueanmy/cca-f-roadmap.git
cd cca-f-roadmap
uv sync                              # cài deps
cp .env.example .env                 # rồi điền ANTHROPIC_API_KEY vào .env
```

**Chạy 1 example:**

```bash
uv run domain-1-agentic/examples/01-agentic-loop.py
```

**Học theo flow:**

1. Đọc README của domain — hiểu **trap** và **mental model**
2. Chạy example — code minh hoạ cụ thể cho trap đó
3. Tự sửa code — thử break "đáp án đúng" để hiểu vì sao "đáp án sai" lại hấp dẫn
4. Khi nắm chắc 5 domain → mở scenarios/ làm timed mock

### Common Traps (CỰC kỳ hay gặp trong đề)

- ❌ **Few-shot để enforce tool ordering** → ordering là compliance, phải dùng programmatic prerequisites
- ❌ **Self-reported confidence cho escalation routing** → LLM confidence kém calibrated
- ❌ **Route mọi workflow sang Batch API** → Batch không có SLA, blocking flow phải dùng real-time
- ❌ **Tăng context window để fix attention** → context size ≠ attention quality
- ❌ **Return empty khi subagent fail** → phải return structured error context
- ❌ **18 tools/agent** → 4–5 là optimal

### 5 Mental Models cho kỳ thi

- **M1** Programmatic enforcement vs. prompt-based guidance — financial/compliance → code, không prompt
- **M2** Tool description = routing mechanism chính (không phải function name, không phải system prompt)
- **M3** Subagent KHÔNG kế thừa context — pass mọi thứ explicit qua prompt
- **M4** Lost-in-the-middle là constraint thật — key info ở đầu/cuối, không ở giữa
- **M5** Batch API vs real-time là **latency decision**, không phải cost decision

### Ngôn ngữ

- **README domain** — Tiếng Việt (giải thích "tại sao")
- **Code comments** — English (universal)
- **Examples** — Python (Anthropic SDK 2026); Domain 2 thêm MCP server

### Repo này không phải

- ❌ Đề thi leak — chỉ là practice patterns, examples Anthropic SDK
- ❌ Document chính thức của Anthropic — link gốc luôn ở [docs.claude.com](https://docs.claude.com)
- ❌ Production-ready code — examples tối giản để học

---

## English

A public study journal for the **Claude Certified Architect — Foundations** exam. 5 domains, 6 exam scenarios, working code for every common trap and mental model.

### Quick start

```bash
git clone https://github.com/hueanmy/cca-f-roadmap.git
cd cca-f-roadmap
uv sync
cp .env.example .env  # add ANTHROPIC_API_KEY
uv run domain-1-agentic/examples/01-agentic-loop.py
```

Each domain has a README + `examples/` folder. Examples are minimal, idiomatic 2026-era Python (model IDs `claude-opus-4-7`, `claude-sonnet-4-6`, `claude-haiku-4-5`). Domain READMEs are in Vietnamese (primary audience), code comments in English.

---

## License

MIT. See [LICENSE](./LICENSE).

## Refs

- [exampro.co/cca-f](https://exampro.co/cca-f) — official course
- [claudecertifications.com](https://claudecertifications.com) — free study guide
- [docs.claude.com](https://docs.claude.com) — Agent SDK & MCP source of truth
- [Companion roadmap](https://hueanmy.github.io/cca-f-roadmap.html)
