#!/usr/bin/env bash
# Post-P2 invariant: no file in .files references the absorbed ~/.agents repo
# as a runtime dependency. Narrative mentions in repo-internal docs are OK.
set -euo pipefail

REPO_ROOT="${1:-$(git rev-parse --show-toplevel)}"

# Patterns that indicate an ~/.agents dependency.
patterns=(
  '~/\.agents/'
  '\$HOME/\.agents/'
  '\$\{HOME\}/\.agents/'
  'mrpeterlee/\.agents'
  'git@github\.com:mrpeterlee/\.agents'
)

# Excluded paths (allowed to mention ~/.agents for legitimate reasons):
# - this test (matches its own pattern list)
# - docs/** (narrative content)
# - README.md (narrative)
# - .claude/CLAUDE.md (repo-internal AGENTS.md-equivalent, narrates the absorption)
# - tests/hygiene/test_claude_skills_present.sh (meta-reference: regression guard
#   docstring describes the bug in the absorbed CLI)
# - lib/agents/** (namespaced merge of .agents lib/*.sh; cosmetic ~/.agents
#   string in user-facing echo messages, no runtime dependency)
exclude=(
  ':!tests/hygiene/test_no_agents_refs.sh'
  ':!tests/hygiene/test_claude_skills_present.sh'
  ':!docs/**'
  ':!README.md'
  ':!.claude/CLAUDE.md'
  ':!.git/**'
  ':!dot_codex/skills/dot_system/plugin-creator/**'
  ':!lib/agents/**'
)

bad=0
for pat in "${patterns[@]}"; do
  hits=$(git -C "$REPO_ROOT" grep -nE "$pat" -- "${exclude[@]}" 2>/dev/null || true)
  if [[ -n "$hits" ]]; then
    echo "FAIL: pattern '$pat' matched:"
    echo "$hits"
    bad=$((bad + 1))
  fi
done

if (( bad > 0 )); then
  exit 1
fi

echo "PASS: no ~/.agents runtime dependencies in .files"
