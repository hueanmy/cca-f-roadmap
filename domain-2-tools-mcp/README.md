# Domain 2 — Tool Design & MCP Integration

> **18% đề thi.** Domain ngắn nhưng có vài câu trap kinh điển về tool naming và tool budget.

## Mental model cần nắm

- **M2** Tool description = routing mechanism chính. Không phải function name, không phải system prompt.

## Sub-topics

### - [ ] Tool description — viết như writing API docs cho LLM

> Mô tả tệ → model đoán mò giữa các tools. Mô tả tốt → model chọn đúng 99% lần.

**Tại sao matter:** Đề có câu cho 4 tools với name tương tự (`analyze_code`, `analyze_quality`, `check_code`, `inspect_code`). Đáp án sai bảo "rename functions". Đáp án đúng: rewrite descriptions để boundaries rõ ràng.

**Học gì cụ thể:**
- Description phải có: input format, example query/use, edge cases, **explicit boundaries vs similar tools**
- "Use this tool when..." > "This tool does..."
- Anti-pattern: copy docstring vào description không edit
- Test: đưa 2 tools cho Claude với fuzzy task → nó pick đúng cái nào? Nếu sai → fix description

**Refs:** example: [`examples/01-tool-description-quality.py`](./examples/01-tool-description-quality.py)

---

### - [ ] Tool budget — 4–5 tools/agent là optimal

> 🚨 Trap: cho 1 agent dùng 18 tools "for flexibility". Selection reliability giảm thẳng đứng.

**Tại sao matter:** Câu hỏi: "agent đang chọn sai tool ~30% lần. Cách fix?" — đáp án đúng là **giảm tool count + tăng description quality**, không phải "thêm few-shot cho từng tool".

**Học gì cụ thể:**
- Tool overlap → split agents (mỗi agent có sub-set thuộc role)
- 4–5 tools/agent = sweet spot empirical
- Nếu cần 18 tools → multi-agent (coordinator + 3-4 specialist agents)
- "Reasoning overload": context dài + nhiều tools = model mệt mỏi

**Refs:** example: [`examples/02-tool-budget.py`](./examples/02-tool-budget.py)

---

### - [ ] Naming để tránh overlap

Trước:
```python
analyze_code  # ambiguous — quality? structure? security?
```

Sau:
```python
analyze_code_structure   # imports, call graph, complexity
analyze_code_quality     # lint, style, dead code
audit_code_security      # CVE, secrets, unsafe patterns
```

**Học gì cụ thể:**
- Verb + noun + qualifier
- Tránh synonyms (check vs inspect vs analyze)
- Nếu không tách được name rõ → tools đang chồng chéo về function

---

### - [ ] MCP (Model Context Protocol)

> Standard cho Claude Code (và clients khác) connect tới external tool servers.

**Học gì cụ thể:**
- 3 transport types: **stdio** (local subprocess), **SSE** (deprecated), **streamable HTTP** (recommended remote)
- Server expose: `tools`, `resources`, `prompts`
- MCP server scoping: mỗi agent **chỉ expose tools thuộc role của nó** — không dump toàn bộ MCP tools cho mọi agent
- Authentication: OAuth cho remote, env vars cho stdio
- Permission scoping: user grant per-tool, không grant per-server

**Refs:** [MCP docs](https://modelcontextprotocol.io) · example: [`examples/03-mcp-server-stdio.py`](./examples/03-mcp-server-stdio.py)

---

### - [ ] MCP server scoping & boundaries

> 🚨 Trap: "expose all 20 MCP tools to all agents for maximum flexibility."

Đáp án đúng: mỗi agent role-scoped. Coordinator không cần `format_code_block`. Code-writer không cần `send_slack_message`.

**Học gì cụ thể:**
- Trong Claude Code: dùng `--allowedTools` flag hoặc settings.json `permissions.allow` để scope
- Scoping per agent file (`.claude/agents/*.md` có `allowedTools` frontmatter)
- Audit log via `PreToolUse` hook — track tool count drift over time

---

## Examples

- [01-tool-description-quality.py](./examples/01-tool-description-quality.py) — bad description vs good description, đo selection accuracy
- [02-tool-budget.py](./examples/02-tool-budget.py) — 18 tools vs 5 tools, side-by-side
- [03-mcp-server-stdio.py](./examples/03-mcp-server-stdio.py) — minimal MCP server (stdio)

## Notes của tôi

> Học ngày: ___ · Insight: ___ · Confused: ___
