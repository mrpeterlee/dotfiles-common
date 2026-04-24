#!/usr/bin/env bash
#
# update.sh - Update agent configs from repo
#
# Assumes lib/common.sh has been sourced.
# Assumes SCRIPT_DIR is set by the caller.

cmd_update() {
    local no_backup=false

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --no-backup) no_backup=true; shift ;;
            *) error "Unknown option: $1"; exit 1 ;;
        esac
    done

    echo ""
    echo -e "${BOLD}Updating Agent Configs${RESET}"
    echo "────────────────────────────────────────"
    echo ""

    ensure_chezmoi

    # 1. Safety backup (capture current state before overwriting)
    if [[ "$no_backup" == "false" ]]; then
        info "Safety backup before update..."
        source "${SCRIPT_DIR}/lib/backup.sh"
        cmd_backup --skip-oauth
    else
        debug "Safety backup skipped (--no-backup)"
    fi

    # 2. Git pull
    info "Pulling latest from remote..."
    if (cd "$SCRIPT_DIR" && git pull --ff-only 2>&1); then
        success "Repo updated"
    else
        warn "Git pull failed (may have local changes — continuing with current state)"
    fi
    echo ""

    # 3. Apply configs
    info "Applying configs..."
    source "${SCRIPT_DIR}/lib/apply.sh"
    cmd_apply all
    echo ""

    # 4. Refresh MCP servers
    source "${SCRIPT_DIR}/lib/restore.sh"
    _install_mcp_servers
    echo ""

    # 5. Refresh externals (if chezmoi externals configured)
    if [[ -f "$SCRIPT_DIR/.chezmoiexternal.toml" ]] || [[ -f "$SCRIPT_DIR/.chezmoiexternal.yaml" ]]; then
        info "Refreshing external dependencies..."
        "$CHEZMOI" -S "$SCRIPT_DIR" apply --refresh-externals 2>&1 || warn "Some externals may have failed"
        success "Externals refreshed"
        echo ""
    fi

    success "Update complete!"
    echo ""
}
