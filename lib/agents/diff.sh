#!/usr/bin/env bash
#
# diff.sh - Preview what chezmoi would change
#
# Assumes lib/common.sh has been sourced.
# Assumes SCRIPT_DIR is set by the caller.

cmd_diff() {
    echo ""
    echo -e "${BOLD}Chezmoi Diff${RESET}"
    echo "────────────────────────────────────────"
    echo ""

    ensure_chezmoi

    "$CHEZMOI" -S "$SCRIPT_DIR" diff || true
    echo ""
}
