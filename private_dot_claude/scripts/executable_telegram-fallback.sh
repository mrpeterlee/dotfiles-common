#!/usr/bin/env bash
#
# Direct Bot API fallback notifier. Use when the Telegram MCP has
# disconnected and the in-session `mcp__plugin_telegram_telegram__reply`
# tool is unavailable.
#
# Reads:
#   $TELEGRAM_BOT_TOKEN  (inherited from the parent claude process)
#   $TELEGRAM_STATE_DIR/access.json  (first entry of .allowFrom)
#   -- or --
#   $TELEGRAM_FALLBACK_CHAT_ID  (override)
#
# Usage:
#   telegram-fallback.sh "message text"
#
# Exit codes:
#   0  — sent OK
#   1  — token missing
#   2  — chat_id unresolvable
#   3  — curl/HTTP failure
#
# This helper is deliberately minimal and NEVER writes the token to
# stdout, stderr, or any log file.

set -euo pipefail

msg="${1:-(no message)}"

token="${TELEGRAM_BOT_TOKEN:-}"
if [[ -z "$token" ]]; then
  echo "telegram-fallback: TELEGRAM_BOT_TOKEN unset" >&2
  exit 1
fi

chat_id="${TELEGRAM_FALLBACK_CHAT_ID:-}"
if [[ -z "$chat_id" ]]; then
  access_json="${TELEGRAM_STATE_DIR:-}/access.json"
  if [[ -f "$access_json" ]]; then
    chat_id=$(jq -r '.allowFrom[0] // empty' "$access_json" 2>/dev/null || true)
  fi
fi
if [[ -z "$chat_id" ]]; then
  echo "telegram-fallback: chat_id unresolvable (set TELEGRAM_FALLBACK_CHAT_ID or populate \$TELEGRAM_STATE_DIR/access.json)" >&2
  exit 2
fi

http_code=$(curl -sS -o /tmp/telegram-fallback.$$.body -w '%{http_code}' \
  "https://api.telegram.org/bot${token}/sendMessage" \
  --data-urlencode "chat_id=${chat_id}" \
  --data-urlencode "text=${msg}" \
  --data-urlencode "disable_web_page_preview=true" 2>/dev/null || echo "000")

body=$(cat /tmp/telegram-fallback.$$.body 2>/dev/null || true)
rm -f /tmp/telegram-fallback.$$.body

if [[ "$http_code" != "200" ]]; then
  echo "telegram-fallback: HTTP $http_code" >&2
  # Surface API error message but NEVER the token.
  echo "$body" | jq -r '.description // .' 2>/dev/null >&2 || true
  exit 3
fi

exit 0
