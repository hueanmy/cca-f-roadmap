# Domain 3 — Claude Code Configuration & Workflows

> **20% đề thi.** Heavy về file artifacts (CLAUDE.md, skills, hooks, slash commands) hơn là API code. Đề hay hỏi: "where do I put X" và "how does X compose with Y".

## Sub-topics

### - [ ] CLAUDE.md hierarchy

> 3 levels: **enterprise** → **user** (`~/.claude/CLAUDE.md`) → **project** (`./CLAUDE.md`). Project-level wins for conflicts (override gần nhất ăn).

**Tại sao matter:** Đề: "hai instructions đối nghịch xuất hiện ở user-level và project-level. Cái nào ăn?" → project-level (closer to the actual work).

**Học gì cụ thể:**
- Loaded vào context **mỗi session start** — đừng dài quá (sweet spot 100–500 dòng)
- Imperative voice: "Use uv run pytest" thay vì "we use pytest typically"
- `@filename` syntax để @import file khác (ví dụ `@AGENTS.md`)
- Nội dung nên có: tech stack, conventions, common commands, anti-patterns

**Refs:** [Memory](https://docs.claude.com/en/docs/claude-code/memory) · example: [`examples/CLAUDE.md.example`](./examples/CLAUDE.md.example)

---

### - [ ] Skills

> Folder structure: `.claude/skills/<name>/SKILL.md`. Load **on-demand** khi user task match skill description.

**Tại sao matter:** Khác CLAUDE.md (luôn load), Skills load có chọn lọc → save context. Đề: "team có 50 workflow domain-specific. Đặt hết vào CLAUDE.md hay tách Skills?" → **Skills**.

**Học gì cụ thể:**
- Frontmatter: `name`, `description` (Claude đọc cái này để decide load)
- Description quality = load accuracy. "Code review skill" tệ. "Use when user asks to review a PR..." tốt
- Skill có thể spawn subagent, dùng tools, đọc file
- Project-level (`.claude/skills/`) vs user-level (`~/.claude/skills/`)

**Refs:** [Skills](https://docs.claude.com/en/docs/claude-code/skills) · example: [`examples/skill-example/SKILL.md`](./examples/skill-example/SKILL.md)

---

### - [ ] Custom slash commands

> File ở `.claude/commands/<name>.md`. User gõ `/<name>` → Claude load file đó như prompt.

**Tại sao matter:** Đề có một câu như "team muốn standardize 'convert legacy test to playwright'. Best primitive?" → **slash command**, không phải skill (skill dispatched probabilistically; slash command dispatched deterministically).

**Học gì cụ thể:**
- Argument: `$ARGUMENTS` placeholder trong command file
- Naming convention: `cf-orchestrate-convert`, `cf-deploy-prod` — prefix theo team
- User-level (`~/.claude/commands/`) vs project-level — project wins khi conflict
- Slash command vs skill: slash = explicit user intent, skill = reactive

**Refs:** [Slash commands](https://docs.claude.com/en/docs/claude-code/slash-commands) · example: [`examples/cf-orchestrate-convert.md`](./examples/cf-orchestrate-convert.md)

---

### - [ ] Hooks

> Lifecycle events. **Deterministic** — không phụ thuộc Claude.

Domain 1 đã cover phần hook trap. Ở đây focus vào **CI/CD usage**.

**Học gì cụ thể:**
- `SessionStart` hook để inject context (vd: `git status` output)
- `PostToolUse` để format code sau mỗi Edit
- `Stop` hook để chạy test trước khi end turn
- `settings.json` location: project (`.claude/settings.json`), user (`~/.claude/settings.json`), local (gitignored)

---

### - [ ] CI/CD integration (non-interactive mode)

> 🚨 Trap: dùng tương interactive `claude` trong CI. CI fail vì nó chờ TTY input.

**Tại sao matter:** Đề: "CI step gọi Claude Code và treo. Vì sao?" → thiếu non-interactive flags.

**Học gì cụ thể:**
- `claude -p "prompt"` = print mode (one-shot, exit)
- `--output-format json` = parse-able output
- `--allowedTools "Edit,Write,Bash(npm:*)"` = scope tools cho CI
- `--dangerously-skip-permissions` cho ephemeral CI environment (vẫn cẩn trọng)
- `storageState` pattern cho automated browser tests (Playwright session)

**Refs:** [CI/CD docs](https://docs.claude.com/en/docs/claude-code/ci) · example: [`examples/ci-pipeline.sh`](./examples/ci-pipeline.sh)

---

### - [ ] Directory convention

```
.claude/
├── settings.json          # hooks, permissions, env
├── settings.local.json    # gitignored, dev-specific
├── agents/                # subagent definitions (.md with frontmatter)
├── skills/                # Skill files (load on-demand)
├── commands/              # /<name> custom slash commands
└── rules/                 # constraint rules (referenced from CLAUDE.md)
CLAUDE.md                  # project memory (auto-load)
```

---

## Examples

- [CLAUDE.md.example](./examples/CLAUDE.md.example) — template với mọi section quan trọng
- [skill-example/SKILL.md](./examples/skill-example/SKILL.md) — frontmatter + body đúng cách
- [cf-orchestrate-convert.md](./examples/cf-orchestrate-convert.md) — custom slash command với `$ARGUMENTS`
- [ci-pipeline.sh](./examples/ci-pipeline.sh) — non-interactive Claude Code trong GitHub Actions
- [hook-format-on-edit.json](./examples/hook-format-on-edit.json) — PostToolUse hook config

## Notes của tôi

> Học ngày: ___ · Insight: ___ · Confused: ___
