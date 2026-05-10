# Domain 4 — Prompt Engineering & Structured Output

> **20% đề thi.** Trap nặng nhất ở đây: dùng prompt cho việc lẽ ra phải dùng code.

## Mental models cần nắm

- **M1** Programmatic enforcement vs prompt-based guidance — financial/compliance → code
- **Few-shot là cho TONE/STYLE**, không phải compliance ordering hay validation

## Sub-topics

### - [ ] JSON schema enforcement (defense in depth)

> Schema + few-shot + validation retry = reliable structured output.

**Tại sao matter:** Trap câu kinh điển: "tôi chỉ cần một field — dùng prompt 'return JSON with field X'". Sai. Dùng `response_format` (structured outputs) hoặc `tool_use` enforcement, plus retry on parse failure.

**Học gì cụ thể:**
- 3 layers: **schema** (server-side guarantee) → **few-shot** (model learns shape) → **validation** (catch the rare drift)
- `tool_use` pattern: fake "tool" với input_schema = output schema, force tool_choice → guaranteed shape
- Retry pattern: parse JSON → on `JSONDecodeError`, send the error back và ask Claude fix
- Khi nào KHÔNG dùng schema: free-form prose answers, creative writing

**Refs:** example: [`examples/01-structured-output.py`](./examples/01-structured-output.py)

---

### - [ ] Few-shot — chỉ dùng cho TONE/STYLE

> 🚨 Trap: "use few-shot to enforce tool ordering" / "use few-shot to enforce field validation".

**Tại sao matter:** Đề có ÍT NHẤT 1 câu thử trap này. Few-shot là probabilistic — dạy model **distribution** của good outputs. Không phải hard constraint.

**Học gì cụ thể:**
- ✅ Few-shot OK cho: tone matching, output style, formatting style, response length
- ❌ Few-shot KHÔNG cho: ordering, validation rules, security checks, compliance fields
- Replace với: programmatic prerequisites (Domain 1), JSON schema, validation retry

---

### - [ ] Prompt chaining cho multi-step extraction

> Đừng nhồi 5 task vào 1 prompt. Chain.

**Tại sao matter:** Single mega-prompt = 4× lower accuracy than chained pipeline trong nhiều benchmarks.

**Học gì cụ thể:**
- Pattern: extract → normalize → validate → enrich (4 calls, 4 narrow prompts)
- Chain output: output JSON của step N → input của step N+1
- Cost: tăng calls nhưng giảm output token (vì mỗi prompt narrow → output ngắn)
- Cache prefix: nếu chain calls share system prompt → bật prompt caching, save 90%

**Refs:** example: [`examples/02-prompt-chaining.py`](./examples/02-prompt-chaining.py)

---

### - [ ] Self-reported confidence — KHÔNG dùng cho routing

> 🚨 Trap: "ask Claude how confident it is, route to human if confidence < 0.8".

**Tại sao matter:** LLMs are mis-calibrated — model **most confident exactly when it's wrong**. Câu này đáp án đúng là dùng **external signal** (rule-based check, ground-truth lookup, second-model agreement).

**Học gì cụ thể:**
- External signal patterns: regex/parser validity, business rule check, "did the user phrase this as a complaint?" (sentiment external classifier)
- Two-model agreement: chạy task qua 2 models, agree → high confidence; disagree → escalate
- Embedding similarity to known-hard cases (pre-compiled list) → escalate

**Refs:** example: [`examples/03-escalation-routing.py`](./examples/03-escalation-routing.py)

---

### - [ ] Probabilistic vs Deterministic — bảng quyết định

| Constraint type | Use |
|---|---|
| Tone, style, voice | Prompt + few-shot |
| Output shape | JSON schema / tool_use |
| Order of tools | Programmatic prerequisites |
| Compliance gate | Hook (PreToolUse) |
| Field validation | Schema + retry, not just prompt |
| Routing decision | External signal, not self-confidence |

---

## Examples

- [01-structured-output.py](./examples/01-structured-output.py) — schema + retry, defense in depth
- [02-prompt-chaining.py](./examples/02-prompt-chaining.py) — extract → normalize → validate pipeline
- [03-escalation-routing.py](./examples/03-escalation-routing.py) — external signal vs self-confidence

## Notes của tôi

> Học ngày: ___ · Insight: ___ · Confused: ___
