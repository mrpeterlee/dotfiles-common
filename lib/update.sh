#!/usr/bin/env bash
#
# update.sh - Update all installed components
#
# Assumes lib/common.sh has been sourced (provides: info, success, warn, error, debug, ensure_chezmoi).
# Assumes SCRIPT_DIR, CHEZMOI_BIN are set by the caller.

cmd_update() {
    echo ""
    echo -e "${BOLD}Updating All Components${RESET}"
    echo "────────────────────────────────────────"
    echo ""

    ensure_chezmoi

    # 1. Apply dotfiles
    info "Applying dotfiles..."
    "$CHEZMOI" apply --source "$SCRIPT_DIR"
    success "Dotfiles applied"
    echo ""

    # 2. Refresh external dependencies (fzf, tpm, zinit, lazy.nvim)
    info "Refreshing external dependencies..."
    "$CHEZMOI" apply --source "$SCRIPT_DIR" --refresh-externals 2>&1 || warn "Some externals may have failed"
    success "Externals refreshed"
    echo ""

    # 3. Conda env (Linux only, skip if not installed)
    if [[ -x /opt/conda/bin/conda ]] && [[ -L /opt/conda/envs/prod ]]; then
        info "Rebuilding conda environment..."
        source "${SCRIPT_DIR}/lib/conda.sh"
        cmd_conda_build
    else
        debug "Conda not installed or no prod env — skipping"
    fi

    # 4. Essential CLI tools (only if conda env is not providing them)
    if [[ "$(uname -s)" == "Linux" ]]; then
        if [[ ! -d /opt/conda/envs/prod/bin ]] || [[ ! -x /opt/conda/envs/prod/bin/oh-my-posh ]]; then
            info "Updating essential CLI tools..."
            source "${SCRIPT_DIR}/lib/restore.sh"
            install_essential_tools
        else
            debug "Conda prod env provides CLI tools — skipping standalone install"
        fi
    fi

    # 5. Agent configs (if ~/.agents exists)
    if [[ -x "${HOME}/.agents/cli" ]]; then
        echo ""
        info "Updating agent configs..."
        "${HOME}/.agents/cli" apply
        success "Agent configs updated"
    else
        debug "~/.agents/cli not found — skipping"
    fi

    echo ""
    success "Update complete!"
    echo ""
}
