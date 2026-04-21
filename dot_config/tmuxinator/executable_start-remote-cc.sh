#!/usr/bin/env bash
# start-remote-cc.sh — Bootstrap and attach to a remote Claude Code tmux session
#
# Creates a detached tmux session on the remote host, sends all setup commands
# to it via non-interactive SSH, then attaches via ssh with auto-reconnect.
#
# If the remote tmux session already exists, setup is skipped (just attaches).
#
# Usage: start-remote-cc.sh <host> <worktree> <state_dir> <op_bot_ref> <work_dir> [sleep_delay]

HOST="${1:?Usage: start-remote-cc.sh <host> <worktree> <state_dir> <op_bot_ref> <work_dir> [sleep_delay]}"
WORKTREE="$2"
STATE_DIR="$3"
OP_BOT_REF="$4"
WORK_DIR="$5"
SLEEP_DELAY="${6:-0}"
SESSION="cc_${WORKTREE}"

# Phase 1: Create remote tmux session and send setup commands via non-interactive SSH
# Skipped if session already exists (e.g., reconnecting after SSH drop)
ssh "$HOST" "bash -s -- '$SESSION' '$STATE_DIR' '$OP_BOT_REF' '$WORK_DIR' '$SLEEP_DELAY' '$WORKTREE'" << 'REMOTE' || true
SESSION="$1"; STATE_DIR="$2"; OP_BOT_REF="$3"; WORK_DIR="$4"; SLEEP_DELAY="$5"; WORKTREE="$6"

if tmux has-session -t "$SESSION" 2>/dev/null; then
    exit 0
fi

tmux -u new-session -d -s "$SESSION"

if [ "$SLEEP_DELAY" -gt 0 ] 2>/dev/null; then
    tmux send-keys -t "$SESSION" "sleep $SLEEP_DELAY" Enter
fi

tmux send-keys -t "$SESSION" "export PATH=\$HOME/.bun/bin:\$PATH && source ~/.config/op/env 2>/dev/null && export OP_SERVICE_ACCOUNT_TOKEN" Enter
tmux send-keys -t "$SESSION" "mkdir -p /tmp/claude_telegram_sessions/${STATE_DIR}" Enter
tmux send-keys -t "$SESSION" "test -f /tmp/claude_telegram_sessions/${STATE_DIR}/access.json || cp ~/.claude/channels/telegram/access.json /tmp/claude_telegram_sessions/${STATE_DIR}/access.json" Enter
tmux send-keys -t "$SESSION" "export TELEGRAM_BOT_TOKEN=\$(op read '${OP_BOT_REF}')" Enter
tmux send-keys -t "$SESSION" "export TELEGRAM_STATE_DIR=/tmp/claude_telegram_sessions/${STATE_DIR}" Enter
tmux send-keys -t "$SESSION" "sleep 1 && _BW_PW=\$(op read 'op://Tapai/Bitwarden/password' 2>/dev/null) && command -v bw >/dev/null 2>&1 && export BW_SESSION=\$(bw unlock \"\$_BW_PW\" --raw); unset _BW_PW" Enter
tmux send-keys -t "$SESSION" "cd ~/${WORK_DIR}" Enter
tmux send-keys -t "$SESSION" "claude --worktree ${WORKTREE} --channels plugin:telegram@claude-plugins-official --dangerously-skip-permissions" Enter

# After claude is up, send initial prompts (channel routing + periodic progress loop).
# Detached so it survives this SSH session closing.
POST_DELAY=$((SLEEP_DELAY + 30))
nohup bash -c "
    sleep $POST_DELAY
    tmux send-keys -t '$SESSION' 'Always respond to me in Telegram' Enter
    sleep 5
    tmux send-keys -t '$SESSION' '/loop cron 0,30 * * * * — Every 30 minutes, review all current tasks and classify them as completed, ongoing, or pending. Completed tasks are closed and must never be executed again. Ongoing tasks must be checked for latest status using cli, Playwright MCP or RDP where applicable. Pending tasks are eligible to start only if there are zero ongoing tasks. When zero ongoing tasks remain, start pending tasks according to their assigned priority sequence.' Enter
    sleep 1
    tmux send-keys -t '$SESSION' Enter
" >/dev/null 2>&1 </dev/null &
disown 2>/dev/null || true
REMOTE

# Phase 2: Attach to remote tmux session with auto-reconnect loop
while true; do
    ssh -o "ServerAliveInterval=30" -o "ServerAliveCountMax=3" -t "$HOST" "tmux -u attach -t $SESSION"
    echo "SSH disconnected. Reconnecting in 5s..."
    sleep 5
done
