# Domain 1 — Agentic Architecture & Orchestration

> **27% đề thi** — domain nặng nhất. Nếu chỉ có thời gian học 1 domain, học cái này.

## Mental models cần nắm

- **M1** Programmatic enforcement vs. prompt-based guidance — financial/compliance consequence → code, không prompt
- **M3** Subagent KHÔNG kế thừa context — mọi thứ phải pass explicit trong prompt

## Sub-topics

### - [ ] Agentic loop

> Stop khi `stop_reason = "end_turn"`, tiếp tục khi `"tool_use"`.

Agentic loop là pattern cốt lõi: gọi API → nếu Claude trả `tool_use` thì execute tool → append `tool_result` → gọi lại → lặp tới khi `end_turn`.

**Tại sao matter:** Đề thi hỏi cách handle stop reasons rất nhiều. Nếu bạn break loop khi gặp `tool_use` (thay vì `end_turn`) → agent dừng giữa chừng.

**Học gì cụ thể:**
- 4 stop reasons: `end_turn`, `tool_use`, `max_tokens`, `stop_sequence`
- `max_tokens` ≠ done — phải continue và yêu cầu Claude finalize
- Append nguyên `response.content` (preserve `tool_use` blocks) khi tiếp tục
- Safety cap: `for iteration in range(10)` để tránh infinite loop

**Refs:** [Tool use](https://docs.claude.com/en/docs/build-with-claude/tool-use) · example: [`examples/01-agentic-loop.py`](./examples/01-agentic-loop.py)

---

### - [ ] Programmatic prerequisites (KHÔNG dùng prompt)

> 🚨 **Trap:** dùng few-shot/system prompt để enforce "phải gọi `get_customer` trước `process_refund`".

Sai vì prompt là **probabilistic**. Khi có financial/compliance consequence, phải dùng **deterministic code**: tool handler check state, return error nếu prerequisite chưa thoả.

**Tại sao matter:** Đây là trap phổ biến nhất trong đề. Câu hỏi sẽ cho 4 đáp án với 1 đáp án "few-shot examples showing the right ordering" — bẫy. Đáp án đúng là một biến thể của "block the tool until prerequisite verified".

**Học gì cụ thể:**
- Pattern: tool handler raise `PrerequisiteError` → return as `tool_result` `is_error=True`
- Claude tự đọc lỗi và gọi prerequisite tool trước
- Few-shot demonstrations vẫn OK cho **tone/style**, KHÔNG cho ordering

**Refs:** example: [`examples/02-programmatic-prerequisites.py`](./examples/02-programmatic-prerequisites.py)

---

### - [ ] Multi-agent hub-and-spoke

> Coordinator (hub) quản routing & error handling, subagents (spokes) có isolated context.

Subagent không thấy conversation history của coordinator — đây không phải bug, là design constraint. Phải pass mọi thứ qua prompt.

**Tại sao matter:** Trap: "subagent automatically inherits coordinator's context". Sai — subagent vào "lạnh", phải brief đầy đủ.

**Học gì cụ thể:**
- Coordinator dùng `Task` tool (Claude Code) hoặc spawn nested `client.messages.create` (Agent SDK)
- Subagent isolated context = save token cho coordinator
- Parallel subagents: spawn nhiều `Task` calls trong **một** assistant response
- Subagent fail → return **structured error**, không return empty (im lặng = trap)

**Refs:** example: [`examples/03-multi-agent-handoff.py`](./examples/03-multi-agent-handoff.py)

---

### - [ ] Hooks (PostToolUse, interception)

> Hook = shell/code chạy deterministically tại lifecycle event, không phụ thuộc Claude quyết định.

Use cases: normalize tool output (heterogeneous formats), block policy violations (refund > $500), audit log.

**Tại sao matter:** Câu hỏi: "làm sao block refund > $500 mà không trust Claude phải nhớ rule?" → đáp án đúng dùng **hook**, không dùng system prompt.

**Học gì cụ thể:**
- Events: `PreToolUse`, `PostToolUse`, `Stop`, `SessionStart`, `FileChanged`
- `PreToolUse` block: hook return non-zero exit → tool không chạy, Claude nhận error
- `PostToolUse` normalize: rewrite tool output trước khi feed lại Claude
- Matcher để filter: chỉ chạy cho tool name match pattern

**Refs:** [Hooks](https://docs.claude.com/en/docs/claude-code/hooks)

---

### - [ ] Task decomposition: chaining vs dynamic

| | Prompt chaining | Dynamic decomposition |
|---|---|---|
| Steps | Fixed sequential | Open-ended |
| Use case | Extract → translate → validate | Research, exploration |
| Predictability | Cao | Thấp |

**Tại sao matter:** Trap: "dynamic decomposition for fixed pipeline". Overhead không cần — chaining đủ.

**Học gì cụ thể:**
- Chaining = nhiều `client.messages.create` tuần tự, output bước trước = input bước sau
- Dynamic = 1 agent quyết định bước tiếp theo dựa trên kết quả vừa rồi
- Chaining dễ debug, dễ retry, cheap; dynamic linh hoạt hơn nhưng tốn

---

### - [ ] Sessions & forking

> `--resume <session-name>` để tiếp tục, `fork_session` để branch độc lập từ baseline.

**Học gì cụ thể:**
- Session = persisted message history, không phải in-memory
- Fork: 2 branches share ancestor, không thấy nhau sau split — useful cho "thử cách 1 vs cách 2"
- Session ≠ subagent — session là time, subagent là space

---

## Examples

- [01-agentic-loop.py](./examples/01-agentic-loop.py) — agentic loop với `stop_reason` handling đầy đủ
- [02-programmatic-prerequisites.py](./examples/02-programmatic-prerequisites.py) — chứng minh tại sao prompt không enforce ordering
- [03-multi-agent-handoff.py](./examples/03-multi-agent-handoff.py) — hub-and-spoke với explicit context passing + structured error
- [04-tool-error-handling.py](./examples/04-tool-error-handling.py) — return structured error context, không return empty

## Notes của tôi

> Format gợi ý:
> - Học ngày: ___
> - Trap nào suýt rơi: ___
> - Còn confused: ___
