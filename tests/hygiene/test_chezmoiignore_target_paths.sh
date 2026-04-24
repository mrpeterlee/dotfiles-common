#!/usr/bin/env bash
# Hygiene gate: .chezmoiignore patterns must be in TARGET-PATH form, not
# chezmoi SOURCE-STATE form.
#
# Bug class (caught 2026-04-24, lines 127/133/134 of .chezmoiignore):
#   chezmoi matches .chezmoiignore patterns against the *target* path
#   (e.g. ".claude/teams/foo/inboxes/") -- NOT the source-state path
#   (e.g. "private_dot_claude/teams/foo/inboxes/"). A pattern like
#       private_dot_claude/teams/*/inboxes/
#   silently does NOT match anything, so the files leak into git via
#   `cli backup` (chezmoi add ~/.claude). We discovered this when
#   operator-sensitive files (Telegram allowlists, team inboxes, bot
#   pidfiles) appeared in git diffs after a routine backup.
#
# Fix: use the target form. The above becomes:
#       .claude/teams/*/inboxes/
#
# A leading "/" is also legal -- it anchors the pattern to the target
# root -- so "/private_dot_claude/..." would also be wrong but
# "/.claude/..." would be fine. We strip the leading "/" before
# inspecting the first path segment.
#
# Reference: https://www.chezmoi.io/reference/special-files/chezmoiignore/
#   "Patterns are matched against the target path, not the source path."
#
# Usage:
#   ./test_chezmoiignore_target_paths.sh           # scan repo
#   ./test_chezmoiignore_target_paths.sh <root>    # scan a specific root
#   ./test_chezmoiignore_target_paths.sh --self-test
#       run an internal positive-test self-check that a known-bad
#       pattern triggers a failure in the matcher
set -euo pipefail

REPO_ROOT_DEFAULT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# Source-state attribute prefixes that signal a wrong-form ignore line.
# A first path-segment that EXACTLY matches one of these or starts with
# "<prefix>" followed by anything is the bug class.
readonly BAD_PREFIXES=(
  'private_'
  'dot_'
  'symlink_'
  'empty_'
  'exact_'
  'encrypted_'
  'executable_'
  'readonly_'
  'remove_'
  'run_once_'
  'run_onchange_'
  'run_after_'
  'run_before_'
  'modify_'
  'create_'
  'literal_'
)

# is_bad_pattern <line>
#   Returns 0 (true) if the .chezmoiignore line uses source-state form.
#   Returns 1 (false) for blank lines, comments, and well-formed lines.
is_bad_pattern() {
  local line="$1"
  # Strip trailing CR (in case a file was edited on Windows).
  line="${line%$'\r'}"
  # Skip blanks.
  [[ -z "${line// /}" ]] && return 1
  # Skip comments.
  [[ "${line#"${line%%[![:space:]]*}"}" == \#* ]] && return 1
  # Strip leading negation marker.
  [[ "$line" == !* ]] && line="${line#!}"
  # Strip leading anchor slash (legal; matches against absolute target path).
  [[ "$line" == /* ]] && line="${line#/}"
  # First path segment = everything up to the first "/" or end-of-line.
  local first="${line%%/*}"
  [[ -z "$first" ]] && return 1
  local prefix
  for prefix in "${BAD_PREFIXES[@]}"; do
    if [[ "$first" == "$prefix" || "$first" == "$prefix"* ]]; then
      return 0
    fi
  done
  return 1
}

self_test() {
  local rc=0
  local bad_samples=(
    'private_dot_claude/teams/*/inboxes/'
    'private_dot_claude/channels/*/bot.pid'
    'dot_config/foo'
    '!private_dot_ssh/id_rsa'
    '/private_dot_local/share/secret'
    'run_once_before_00-install.sh'
    'literal_dot_thing'
    'readonly_dot_ssh/config'
    'remove_dot_cache/foo'
  )
  local good_samples=(
    '.claude/teams/*/inboxes/'
    '.claude/channels/*/bot.pid'
    '.config/foo'
    '!.ssh/id_rsa'
    '/.local/share/secret'
    ''
    '   '
    '# private_dot_claude/teams/ is a comment, not a pattern'
    'README.md'
    'private-key-style-name/foo'
  )

  local s
  for s in "${bad_samples[@]}"; do
    if ! is_bad_pattern "$s"; then
      echo "SELF-TEST FAIL: matcher missed bad pattern: '$s'"
      rc=1
    fi
  done
  for s in "${good_samples[@]}"; do
    if is_bad_pattern "$s"; then
      echo "SELF-TEST FAIL: matcher false-positive on good pattern: '$s'"
      rc=1
    fi
  done

  if (( rc == 0 )); then
    echo "PASS: self-test (matcher correctly classifies ${#bad_samples[@]} bad + ${#good_samples[@]} good samples)"
  else
    echo "FAIL: self-test"
  fi
  return $rc
}

scan_file() {
  local file="$1"
  local lineno=0
  local offenders=0
  local raw
  while IFS= read -r raw || [[ -n "$raw" ]]; do
    lineno=$((lineno + 1))
    if is_bad_pattern "$raw"; then
      echo "  $file:$lineno: $raw"
      offenders=$((offenders + 1))
    fi
  done < "$file"
  return $offenders
}

main() {
  if [[ "${1:-}" == "--self-test" ]]; then
    self_test
    exit $?
  fi

  local repo_root="${1:-$REPO_ROOT_DEFAULT}"

  # Always run the self-test first so we know the matcher is healthy
  # before we trust its verdict on real files.
  if ! self_test >/dev/null 2>&1; then
    echo "FAIL: internal self-test failed -- matcher logic is broken"
    self_test
    exit 1
  fi

  # Find all .chezmoiignore files chezmoi recognizes:
  #   - the root .chezmoiignore
  #   - any nested .chezmoiignore in subdirectories of the source tree
  # Skip .git, worktrees, node_modules, and .venv.
  local files=()
  while IFS= read -r f; do
    files+=("$f")
  done < <(find "$repo_root" \
              \( -path '*/.git' -o -path '*/node_modules' -o -path '*/.venv' \
                 -o -path '*/.claude/worktrees' \) -prune -o \
              -type f -name '.chezmoiignore' -print 2>/dev/null | sort)

  if (( ${#files[@]} == 0 )); then
    echo "FAIL: no .chezmoiignore files found under $repo_root"
    exit 1
  fi

  local total_offenders=0
  local f
  for f in "${files[@]}"; do
    local n
    set +e
    scan_file "$f"
    n=$?
    set -e
    total_offenders=$((total_offenders + n))
  done

  if (( total_offenders > 0 )); then
    echo
    echo "FAIL: $total_offenders source-state pattern(s) in .chezmoiignore (scanned ${#files[@]} file(s))"
    echo "       chezmoi matches against TARGET paths, not source-state paths."
    echo "       Rewrite e.g. 'private_dot_claude/foo' -> '.claude/foo'."
    echo "       See https://www.chezmoi.io/reference/special-files/chezmoiignore/"
    exit 1
  fi

  echo "PASS: ${#files[@]} .chezmoiignore file(s) use target-path form"
}

main "$@"
