#!/usr/bin/env bash
# Regression guard: the original ~/.agents/cli silently dropped private_dot_claude/skills/.
# After P2 absorption, these skill files MUST be present in the .files source tree.
set -euo pipefail

REPO_ROOT="${1:-$(git rev-parse --show-toplevel)}"

required=(
  "private_dot_claude/skills/git-workflow/SKILL.md"
  "private_dot_claude/skills/infra-verify/SKILL.md"
)

missing=0
for path in "${required[@]}"; do
  if [[ ! -f "$REPO_ROOT/$path" ]]; then
    echo "MISSING: $path"
    missing=$((missing + 1))
  fi
done

if (( missing > 0 )); then
  echo "FAIL: $missing required skill file(s) missing from .files"
  exit 1
fi

echo "PASS: all required Claude skills present"
