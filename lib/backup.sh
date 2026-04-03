#!/usr/bin/env bash
#
# backup.sh - Capture live system changes back into the repo
#
# Assumes lib/common.sh has been sourced (provides: info, success, error, ensure_chezmoi).
# Assumes CHEZMOI_BIN is set by the caller.

cmd_backup() {
    echo ""
    echo -e "${BOLD}Backing Up Dotfiles${RESET}"
    echo "────────────────────────────────────────"
    echo ""

    ensure_chezmoi

    info "Capturing changes from live system..."
    "$CHEZMOI" re-add --source "$SCRIPT_DIR"

    # Show what changed in the source dir
    local changes
    changes=$(cd "$SCRIPT_DIR" && git diff --name-only 2>/dev/null || true)

    if [[ -n "$changes" ]]; then
        echo ""
        success "Files updated:"
        echo "$changes" | while read -r f; do
            echo "  $f"
        done
    else
        success "No changes detected"
    fi

    # Backup OAuth tokens via agents CLI
    if [[ -x "$HOME/.agents/cli" ]]; then
        "$HOME/.agents/cli" backup
    fi

    echo ""
    echo "Next: run 'git diff' to review, then 'git commit && git push'"
    echo ""
}
