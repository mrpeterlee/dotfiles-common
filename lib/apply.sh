#!/usr/bin/env bash
#
# apply.sh - Apply dotfiles from repo to system (lightweight)
#
# Assumes lib/common.sh has been sourced (provides: info, success, error, ensure_chezmoi).
# Assumes SCRIPT_DIR, CHEZMOI_BIN are set by the caller.

cmd_apply() {
    echo ""
    echo -e "${BOLD}Applying Dotfiles${RESET}"
    echo "────────────────────────────────────────"
    echo ""

    ensure_chezmoi

    info "Running chezmoi apply..."
    "$CHEZMOI" apply --source "$SCRIPT_DIR" "$@"

    success "Apply complete!"
    echo ""
}
