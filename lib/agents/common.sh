#!/usr/bin/env bash
#
# common.sh - Shared helpers for the agents CLI
#
# Assumes SCRIPT_DIR is set by the caller.

# Colors (disabled if not a terminal)
if [[ -t 1 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    BLUE='\033[0;34m'
    CYAN='\033[0;36m'
    DIM='\033[2m'
    BOLD='\033[1m'
    RESET='\033[0m'
else
    RED='' GREEN='' YELLOW='' BLUE='' CYAN='' DIM='' BOLD='' RESET=''
fi

# Logging functions
info() { echo -e "${BLUE}==>${RESET} $*"; }
success() { echo -e "${GREEN}✓${RESET} $*"; }
warn() { echo -e "${YELLOW}!${RESET} $*"; }
error() { echo -e "${RED}✗${RESET} $*" >&2; }
debug() { [[ "${AGENTS_DEBUG:-}" == "1" ]] && echo -e "${YELLOW}[debug]${RESET} $*" || true; }

# Check if a command exists
has_cmd() {
    command -v "$1" &>/dev/null
}

# Copy a file, always overwriting
copy_force() {
    local src="$1"
    local dst="$2"
    local label="${3:-$(basename "$dst")}"

    mkdir -p "$(dirname "$dst")"
    cp "$src" "$dst"
    success "  wrote $label"
}

# Check file existence and show timestamp
check_file() {
    local f="$1"
    local name
    name=$(basename "$f")
    if [[ -f "$f" ]]; then
        local mtime
        mtime=$(stat -c '%y' "$f" 2>/dev/null | cut -d. -f1)
        success "  $name  (${mtime:-unknown})"
    else
        error "  $name  (missing)"
    fi
}

# Find or install chezmoi
ensure_chezmoi() {
    if has_cmd chezmoi; then
        CHEZMOI="chezmoi"
        return 0
    elif [[ -x "${HOME}/.local/bin/chezmoi" ]]; then
        CHEZMOI="${HOME}/.local/bin/chezmoi"
        return 0
    fi

    info "Installing chezmoi..."
    sh -c "$(curl -fsLS get.chezmoi.io)" -- -b ~/.local/bin
    CHEZMOI="${HOME}/.local/bin/chezmoi"
    success "chezmoi installed"
}

# Agent registry — single source of truth
AGENTS=(claude codex opencode gemini)

declare -A AGENT_DIRS=(
    [claude]="$HOME/.claude"
    [codex]="$HOME/.codex"
    [opencode]="$HOME/.config/opencode"
    [gemini]="$HOME/.gemini"
)
