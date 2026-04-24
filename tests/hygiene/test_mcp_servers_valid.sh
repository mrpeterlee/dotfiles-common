#!/usr/bin/env bash
# Gate: mcp/servers.json must be valid JSON and every server entry must have
# either a "command" (stdio transport) or a "url" (http/sse transport).
set -euo pipefail

REPO_ROOT="${1:-$(git rev-parse --show-toplevel)}"
MANIFEST="$REPO_ROOT/mcp/servers.json"

if [[ ! -f "$MANIFEST" ]]; then
  echo "FAIL: $MANIFEST missing"
  exit 1
fi

if ! jq empty "$MANIFEST" >/dev/null 2>&1; then
  echo "FAIL: $MANIFEST is not valid JSON"
  exit 1
fi

bad=0
while IFS= read -r name; do
  has_cmd=$(jq -r --arg n "$name" '.[$n] | has("command")' "$MANIFEST")
  has_url=$(jq -r --arg n "$name" '.[$n] | has("url")' "$MANIFEST")
  if [[ "$has_cmd" != "true" && "$has_url" != "true" ]]; then
    echo "FAIL: server '$name' has neither command nor url"
    bad=$((bad + 1))
  fi
done < <(jq -r 'keys[]' "$MANIFEST")

if (( bad > 0 )); then
  exit 1
fi

echo "PASS: $(jq 'keys | length' "$MANIFEST") MCP server entries valid"
