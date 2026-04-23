#!/usr/bin/env bash
set -euo pipefail

# Patterns that must not appear anywhere in the stripped .files repo.
# Organizational / infrastructure plaintext that belongs in overlays.
readonly BANNED_PATTERNS=(
  'AstroCapital'
  'astrocapital\.net'
  'acap\.cc'
  'tapai\.com'
  'op://ACap/'
  'op://Tapai/'
  '18\.138\.191\.35'     # acap EC2 public IP
  '13\.251\.46\.169'     # tapai-admin EC2 public IP
  '13\.228\.5\.236'      # kayden's box
  '10\.1\.1\.100'        # sg-prod-1 LAN IP
  'sg-prod-1\.acap\.cc'
  'cn-prod-1\.acap\.cc'
  'infisical\.acap\.cc'
  'infisical\.tapai\.com'
  'pw\.tapai\.com'
  'tapai\.tech@acap\.cc'
  'peter\.lee@astrocapital\.net'
)

# Directories / files to skip from the scan (intentional placeholders).
readonly EXCLUDE_DIRS=(
  '.git'
  'node_modules'
  '.venv'
  'tests/hygiene/golden'
  'docs'   # documentation of the convention; quotes vault/org names as examples
)

build_exclude_args() {
  local args=()
  for d in "${EXCLUDE_DIRS[@]}"; do
    args+=("--exclude-dir=$d")
  done
  printf '%s\n' "${args[@]}"
}

scan() {
  local repo_root="${1:?repo root required}"
  local rc=0
  local exclude_args=()
  while IFS= read -r line; do exclude_args+=("$line"); done < <(build_exclude_args)

  for pattern in "${BANNED_PATTERNS[@]}"; do
    if matches=$(grep -rInE "$pattern" "${exclude_args[@]}" "$repo_root" 2>/dev/null); then
      if [[ -n "$matches" ]]; then
        echo "::error::banned pattern '$pattern' found in .files:"
        echo "$matches"
        rc=1
      fi
    fi
  done
  return $rc
}

repo_root="${1:-$(git rev-parse --show-toplevel)}"
scan "$repo_root"
