---
name: pr-security-review
description: Use when the user asks for a security review of a PR or branch — looks for hardcoded secrets, unsafe deserialization, SQL injection, missing auth checks, and CVE-tagged dependencies. Triggers on "security review", "audit this PR", "is this safe to merge", or when changes touch auth/billing/PII paths.
---

# PR Security Review

You are auditing a pull request for security issues before it merges to main.
This skill runs OUT-OF-BAND of normal review — only when explicitly invoked.

## Procedure

1. **Get the diff.** Run `gh pr diff $PR_NUMBER` (or `git diff main..HEAD` if no PR number given).

2. **Triage the change scope.** Categorize each file:
   - 🔴 **Sensitive** — auth/, billing/, payments/, anything reading env vars or making outbound HTTP
   - 🟡 **Adjacent** — DB models, request validation, logging
   - 🟢 **Low-risk** — pure UI, docs, tests

3. **Check sensitive files first.** For each one:
   - **Secrets:** grep for patterns: `sk_live_`, `AKIA`, `aws_secret`, hardcoded `password=`, `api_key=`. Catch `Bearer` tokens in test fixtures (real ones get committed by accident).
   - **Auth:** is there an `@require_auth` (or equivalent) on every new endpoint? Are role checks present where expected?
   - **Injection:** any raw SQL string concat? `f"SELECT ... {user_input}"` is a flag. Should be parameterized.
   - **Deserialization:** `pickle.loads`, `yaml.load` (without `SafeLoader`), `eval`, `exec` — all flagged.
   - **PII:** are we logging emails / phones / card numbers? Check structlog calls in changed files.

4. **Check dependency changes.** If `pyproject.toml` or `requirements.txt` changed:
   - For each new/upgraded dep, check `pip-audit` or the GitHub advisory DB.
   - Flag any major-version bump in a security-relevant lib (cryptography, requests, urllib3, jinja2).

5. **Output format.**
   ```
   ## Security review: PR #<num>
   ### 🔴 Blockers (must fix)
   - <file:line> — <one-line>
   ### 🟡 Concerns (worth discussing)
   - <file:line> — <one-line>
   ### 🟢 Looks fine
   - <one-line summary>
   ### Recommendation
   <approve / request changes / block>
   ```

## Constraints

- **Never** propose code edits in this skill. Output the review only — the human decides.
- If the PR is over 1000 lines of diff, ask the user to scope down before reviewing.
- If you find a 🔴 blocker, also paste the relevant 5-line code snippet so the reviewer doesn't have to context-switch.

## Refs

- `compliance/PCI-CHECKLIST.md` — what an auditor would flag
- `architecture.md#auth` — current auth pattern
- pip-audit: `uv run pip-audit`
