#!/usr/bin/env bash
# Non-interactive Claude Code in CI — what the exam expects you to know.
#
# CCA-F trap: developers run plain `claude` in CI and the job hangs forever
# waiting for TTY input. The fix is `-p` (print/headless mode) plus explicit
# tool scoping with `--allowedTools`.
#
# Usage in GitHub Actions:
#   - run: bash domain-3-claude-code/examples/ci-pipeline.sh
#     env:
#       ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
#       PR_NUMBER: ${{ github.event.pull_request.number }}

set -euo pipefail

: "${ANTHROPIC_API_KEY:?must be set}"
: "${PR_NUMBER:?must be set in GH Actions step}"

# ---------------------------------------------------------------------------
# 1. PR triage — read the diff, decide if a security review is warranted.
#    --output-format json so we can parse the verdict in bash.
# ---------------------------------------------------------------------------
echo "📋 Triaging PR #$PR_NUMBER..."

VERDICT=$(claude -p "Review PR #$PR_NUMBER. Output a single JSON object {\"needs_security_review\": bool, \"reason\": string}. Nothing else." \
  --output-format json \
  --allowedTools "Bash(gh:*)" \
  | jq -r '.result')

NEEDS_SECURITY=$(echo "$VERDICT" | jq -r '.needs_security_review')
REASON=$(echo "$VERDICT" | jq -r '.reason')

echo "   verdict: needs_security_review=$NEEDS_SECURITY ($REASON)"

# ---------------------------------------------------------------------------
# 2. Conditionally run the security review skill — only when triage says yes.
#    Note --allowedTools is scoped: we let it READ files and call gh, but not
#    write anything. CI shouldn't be making code changes from a review job.
# ---------------------------------------------------------------------------
if [[ "$NEEDS_SECURITY" == "true" ]]; then
  echo "🔒 Running security review..."
  claude -p "/pr-security-review $PR_NUMBER" \
    --allowedTools "Read,Grep,Bash(gh:*),Bash(git:*)" \
    --output-format text \
    > security-review.md

  # Post review as a PR comment.
  gh pr comment "$PR_NUMBER" --body-file security-review.md
fi

# ---------------------------------------------------------------------------
# 3. Common mistakes the exam will quiz you on:
#
#   ❌ claude "review the PR"                         # hangs — no -p
#   ❌ claude -p "..." --dangerously-skip-permissions # too broad in untrusted CI
#   ❌ claude -p "..."                                # no tool scoping → can run anything
#   ✅ claude -p "..." --allowedTools "Read,Grep"     # scoped, explicit, safe
# ---------------------------------------------------------------------------

echo "✅ done"
