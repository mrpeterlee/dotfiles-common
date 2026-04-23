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

# Boot prompt sent to claude after it starts. Override via CC_BOOT_PROMPT env var.
# Default delegates the full operational spec to loop_prompt.md in the acap repo
# so the spec can evolve without re-deploying this script; each cron tick re-reads
# the file and executes its instructions.
BOOT_PROMPT="${CC_BOOT_PROMPT:-/loop cron 0,30 * * * * — Re-read /home/peter/acap/ansible/roles/tmuxinator/loop_prompt.md each tick and execute its instructions.}"

# Escape single quotes for safe embedding inside a single-quoted ssh arg:
#   ' -> '\''
BOOT_PROMPT_ESC=$(printf '%s' "$BOOT_PROMPT" | sed "s/'/'\\\\''/g")

# Phase 1: Create remote tmux session and send setup commands via non-interactive SSH
# Skipped if session already exists (e.g., reconnecting after SSH drop)
ssh "$HOST" "bash -s -- '$SESSION' '$STATE_DIR' '$OP_BOT_REF' '$WORK_DIR' '$SLEEP_DELAY' '$WORKTREE' '$BOOT_PROMPT_ESC'" << 'REMOTE' || true
SESSION="$1"; STATE_DIR="$2"; OP_BOT_REF="$3"; WORK_DIR="$4"; SLEEP_DELAY="$5"; WORKTREE="$6"; BOOT_PROMPT="$7"

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
# Prefer the session-scoped git worktree so the bot never touches the main
# clone (the auto-deploy cron does `git reset --hard origin/main` on it).
# Fall back to the main clone if the worktree hasn't been provisioned yet.
tmux send-keys -t "$SESSION" "cd ~/${WORK_DIR}/.claude/worktrees/${WORKTREE} 2>/dev/null || cd ~/${WORK_DIR}" Enter
tmux send-keys -t "$SESSION" "claude --worktree ${WORKTREE} --channels plugin:telegram@claude-plugins-official --dangerously-skip-permissions" Enter

# After claude is up, send the consolidated boot prompt (channel routing + periodic progress loop).
# Detached so it survives this SSH session closing.
# Uses `tmux send-keys -l` (literal mode) so tokens like "Enter" inside the prompt
# body are not interpreted as key names. Enter is sent as a separate keystroke.
POST_DELAY=$((SLEEP_DELAY + 30))
export BOOT_PROMPT SESSION POST_DELAY
nohup bash -c '
    sleep "$POST_DELAY"
    tmux send-keys -l -t "$SESSION" "$BOOT_PROMPT"
    sleep 0.5
    tmux send-keys -t "$SESSION" Enter
    sleep 1
    tmux send-keys -t "$SESSION" Enter
' >/dev/null 2>&1 </dev/null &
disown 2>/dev/null || true
REMOTE

# Phase 2: Attach to remote tmux session with auto-reconnect loop
while true; do
    ssh -o "ServerAliveInterval=30" -o "ServerAliveCountMax=3" -t "$HOST" "tmux -u attach -t $SESSION"
    echo "SSH disconnected. Reconnecting in 5s..."
    sleep 5
done
