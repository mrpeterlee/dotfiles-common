#!/usr/bin/env bash
#
# status.sh - Show installation status
#
# Assumes lib/common.sh has been sourced (provides: info, success, warn, error, debug).
# Assumes CHEZMOI_BIN is set by the caller.

cmd_status() {
    echo ""
    echo -e "${BOLD}Dotfiles Status${RESET}"
    echo "────────────────────────────────────────"
    echo ""

    # Check chezmoi
    if command -v chezmoi &>/dev/null || [[ -x "$CHEZMOI_BIN" ]]; then
        success "chezmoi installed"
        CHEZMOI="${CHEZMOI_BIN}"
        command -v chezmoi &>/dev/null && CHEZMOI="chezmoi"
    else
        error "chezmoi not installed"
        echo ""
        echo "Run 'cli restore' to get started."
        return 1
    fi

    # Count managed files
    local file_count
    file_count=$("$CHEZMOI" managed --include=files 2>/dev/null | wc -l || echo 0)
    echo "  Managed files: ${file_count}"
    echo ""

    echo "External dependencies:"
    test -d ~/.local/share/tmux/plugins/tpm && success "TPM (Tmux Plugin Manager)" || error "TPM"
    test -d ~/.local/share/zinit && success "Zinit (Zsh plugin manager)" || error "Zinit"
    test -d ~/.local/share/nvim/lazy/lazy.nvim && success "Lazy.nvim (Neovim plugins)" || error "Lazy.nvim"
    test -x ~/.local/bin/fzf && success "fzf" || error "fzf"
    test -x ~/.local/bin/nvim.appimage && success "Neovim" || error "Neovim"
    echo ""

    echo "Config files:"
    test -f ~/.config/zsh/.zshrc && success "zsh" || error "zsh"
    test -f ~/.config/nvim/init.lua && success "nvim" || error "nvim"
    test -f ~/.config/tmux/tmux.conf && success "tmux" || error "tmux"
    test -f ~/.config/git/config && success "git" || error "git"
    test -f ~/.wezterm.lua && success "wezterm" || error "wezterm"
    test -f ~/.config/lazygit/config.yml && success "lazygit" || error "lazygit"
    echo ""

    echo "Conda environment:"
    if [[ -x /opt/conda/bin/conda ]]; then
        success "Miniconda (/opt/conda)"
    else
        warn "Miniconda not installed"
    fi
    if [[ -L /opt/conda/envs/prod ]]; then
        success "prod -> $(readlink /opt/conda/envs/prod)"
    else
        warn "No prod env (run 'cli conda build')"
    fi
    echo ""
}
