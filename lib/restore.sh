#!/usr/bin/env bash
#
# restore.sh - Restore dotfiles and tools from repo to system
#
# Assumes lib/common.sh and lib/platform.sh have been sourced.
# Assumes SCRIPT_DIR, CHEZMOI_BIN, CHEZMOI_SOURCE, CHEZMOI_CONFIG_DIR, REPO are set.

# Install miniconda to /opt/conda if not present (Linux only).
# Requires write access to /opt — on multi-user hosts run as the /opt owner.
ensure_conda() {
    local conda_dir="/opt/conda"

    # Only supported on Linux
    [[ "$(uname -s)" != "Linux" ]] && return 0

    if [[ -x "${conda_dir}/bin/conda" ]]; then
        debug "Miniconda already installed at ${conda_dir}"
        return 0
    fi

    # Check we can write to /opt (or create /opt/conda)
    local use_sudo=false
    if mkdir -p "$conda_dir" 2>/dev/null; then
        # Remove the dir we just created so the installer can create it fresh
        rmdir "$conda_dir" 2>/dev/null || true
    elif sudo -n mkdir -p "$conda_dir" 2>/dev/null; then
        use_sudo=true
        sudo rmdir "$conda_dir" 2>/dev/null || true
    else
        warn "Cannot write to /opt — skipping conda install (run as /opt owner or use sudo)"
        return 0
    fi

    info "Installing Miniconda to ${conda_dir}..."
    local arch
    arch=$(uname -m)
    local url="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-${arch}.sh"

    local tmp
    tmp=$(mktemp /tmp/miniconda-XXXXXX.sh)
    curl -fsSLo "$tmp" "$url"
    chmod +x "$tmp"

    if [[ "$use_sudo" == "true" ]]; then
        sudo env HOME="$HOME" bash "$tmp" -b -p "$conda_dir"
        sudo chown -R "$(id -u):$(id -g)" "$conda_dir"
        # Reclaim ~/.conda created by installer running as root
        sudo chown -R "$(id -u):$(id -g)" "${HOME}/.conda" 2>/dev/null || true
    else
        env -i HOME="$HOME" PATH="/usr/bin:/bin" bash "$tmp" -b -p "$conda_dir"
    fi
    rm -f "$tmp"

    # Accept ToS for default channels
    CONDA_DEFAULT_ENV="" CONDA_PREFIX="" \
        "${conda_dir}/bin/conda" tos accept \
            --override-channels --channel https://repo.anaconda.com/pkgs/main 2>/dev/null || true
    CONDA_DEFAULT_ENV="" CONDA_PREFIX="" \
        "${conda_dir}/bin/conda" tos accept \
            --override-channels --channel https://repo.anaconda.com/pkgs/r 2>/dev/null || true

    # Clean stale env registrations
    mkdir -p "${HOME}/.conda"
    echo "${conda_dir}" > "${HOME}/.conda/environments.txt"

    # Make world-readable so other users can use the env
    chmod -R a+rX "$conda_dir"
    chmod 755 "${conda_dir}/envs" 2>/dev/null || true

    success "Miniconda installed at ${conda_dir}"
}

# Build the shared conda env if no prod symlink exists yet.
ensure_conda_env() {
    local conda_dir="/opt/conda"

    [[ "$(uname -s)" != "Linux" ]] && return 0
    [[ ! -x "${conda_dir}/bin/conda" ]] && return 0

    if [[ -L "${conda_dir}/envs/prod" ]]; then
        debug "Conda prod env already exists"
        return 0
    fi

    info "Building conda environment (this may take a while)..."

    # Ensure conda is on PATH and no stale env vars interfere
    export CONDA_DEFAULT_ENV="" CONDA_PREFIX="" CONDA_SHLVL=0
    export PATH="${conda_dir}/bin:${PATH}"

    source "${SCRIPT_DIR}/lib/conda.sh"
    cmd_conda_build

    # Make world-readable
    chmod -R a+rX "$conda_dir"
    chmod 755 "${conda_dir}/envs" 2>/dev/null || true
}

# Install essential CLI tools into ~/.local/bin when conda env is not available.
# These are the minimum tools needed for a functional zsh experience.
install_essential_tools() {
    local bin_dir="${HOME}/.local/bin"

    # Skip if the conda prod env already provides these tools
    if [[ -d /opt/conda/envs/prod/bin ]] && [[ -x /opt/conda/envs/prod/bin/oh-my-posh ]]; then
        debug "Conda prod env provides tools, skipping standalone install"
        return 0
    fi

    # Only run on Linux
    [[ "$(uname -s)" != "Linux" ]] && return 0

    mkdir -p "$bin_dir"

    local arch
    arch=$(uname -m)
    local arch_go arch_alt
    case "$arch" in
        x86_64)  arch_go="amd64"; arch_alt="x86_64" ;;
        aarch64) arch_go="arm64"; arch_alt="aarch64" ;;
        *)       warn "Unsupported architecture: ${arch}"; return 0 ;;
    esac

    local tmp
    tmp=$(mktemp -d)
    trap "rm -rf '$tmp'" RETURN

    info "Installing essential CLI tools into ~/.local/bin..."

    # oh-my-posh (prompt theme)
    if ! command -v oh-my-posh &>/dev/null; then
        info "  Installing oh-my-posh..."
        local omp_tag
        omp_tag=$(curl -sL https://api.github.com/repos/JanDeDobbeleer/oh-my-posh/releases/latest | jq -r '.tag_name')
        if [[ -n "$omp_tag" && "$omp_tag" != "null" ]]; then
            curl -sLo "${bin_dir}/oh-my-posh" \
                "https://github.com/JanDeDobbeleer/oh-my-posh/releases/download/${omp_tag}/posh-linux-${arch_go}"
            chmod +x "${bin_dir}/oh-my-posh"
            success "  oh-my-posh ${omp_tag}"
        fi
    else
        debug "  oh-my-posh already available"
    fi

    # fzf is managed by chezmoi via .chezmoiexternal.toml — skip here

    # eza (ls replacement)
    if ! command -v eza &>/dev/null; then
        info "  Installing eza..."
        local eza_tag
        eza_tag=$(curl -sL https://api.github.com/repos/eza-community/eza/releases/latest | jq -r '.tag_name')
        if [[ -n "$eza_tag" && "$eza_tag" != "null" ]]; then
            curl -sL "https://github.com/eza-community/eza/releases/download/${eza_tag}/eza_${arch_alt}-unknown-linux-gnu.tar.gz" \
                | tar xz -C "$tmp"
            cp "${tmp}/eza" "${bin_dir}/eza" 2>/dev/null || cp "${tmp}/./eza" "${bin_dir}/eza" 2>/dev/null
            chmod +x "${bin_dir}/eza"
            success "  eza ${eza_tag}"
        fi
    else
        debug "  eza already available"
    fi

    # lazygit (git TUI) — uses x86_64/arm64
    if ! command -v lazygit &>/dev/null; then
        info "  Installing lazygit..."
        local lg_tag
        lg_tag=$(curl -sL https://api.github.com/repos/jesseduffield/lazygit/releases/latest | jq -r '.tag_name')
        if [[ -n "$lg_tag" && "$lg_tag" != "null" ]]; then
            local lg_ver="${lg_tag#v}"
            local lg_arch; case "$arch" in x86_64) lg_arch="x86_64";; aarch64) lg_arch="arm64";; esac
            curl -sL "https://github.com/jesseduffield/lazygit/releases/download/${lg_tag}/lazygit_${lg_ver}_linux_${lg_arch}.tar.gz" \
                | tar xz -C "$bin_dir" lazygit
            chmod +x "${bin_dir}/lazygit"
            success "  lazygit ${lg_tag}"
        fi
    else
        debug "  lazygit already available"
    fi

    # delta (git pager)
    if ! command -v delta &>/dev/null; then
        info "  Installing delta..."
        local delta_tag
        delta_tag=$(curl -sL https://api.github.com/repos/dandavison/delta/releases/latest | jq -r '.tag_name')
        if [[ -n "$delta_tag" && "$delta_tag" != "null" ]]; then
            curl -sL "https://github.com/dandavison/delta/releases/download/${delta_tag}/delta-${delta_tag}-${arch_alt}-unknown-linux-gnu.tar.gz" \
                | tar xz -C "$tmp"
            cp "${tmp}/delta-${delta_tag}-${arch_alt}-unknown-linux-gnu/delta" "${bin_dir}/delta"
            chmod +x "${bin_dir}/delta"
            success "  delta ${delta_tag}"
        fi
    else
        debug "  delta already available"
    fi

    # neovim — uses x86_64/arm64
    if ! command -v nvim &>/dev/null; then
        info "  Installing nvim..."
        local nvim_tag
        nvim_tag=$(curl -sL https://api.github.com/repos/neovim/neovim/releases/latest | jq -r '.tag_name')
        if [[ -n "$nvim_tag" && "$nvim_tag" != "null" ]]; then
            local nvim_arch; case "$arch" in x86_64) nvim_arch="x86_64";; aarch64) nvim_arch="arm64";; esac
            curl -sLo "${tmp}/nvim.tar.gz" \
                "https://github.com/neovim/neovim/releases/download/${nvim_tag}/nvim-linux-${nvim_arch}.tar.gz"
            tar xzf "${tmp}/nvim.tar.gz" -C "$tmp"
            cp "${tmp}/nvim-linux-${nvim_arch}/bin/nvim" "${bin_dir}/nvim"
            chmod +x "${bin_dir}/nvim"
            # Copy runtime files needed by nvim
            local share_dir="${HOME}/.local/share"
            if [[ -d "${tmp}/nvim-linux-${nvim_arch}/share/nvim" ]]; then
                mkdir -p "${share_dir}"
                rm -rf "${share_dir}/nvim"
                cp -r "${tmp}/nvim-linux-${nvim_arch}/share/nvim" "${share_dir}/"
            fi
            # Copy lib files needed by nvim
            if [[ -d "${tmp}/nvim-linux-${nvim_arch}/lib" ]]; then
                mkdir -p "${HOME}/.local/lib"
                cp -r "${tmp}/nvim-linux-${nvim_arch}/lib/"* "${HOME}/.local/lib/" 2>/dev/null || true
            fi
            success "  nvim ${nvim_tag}"
        fi
    else
        debug "  nvim already available"
    fi

    # gh (GitHub CLI)
    if ! command -v gh &>/dev/null; then
        info "  Installing gh..."
        local gh_ver
        gh_ver=$(curl -sL https://api.github.com/repos/cli/cli/releases/latest | jq -r '.tag_name' | sed 's/^v//')
        if [[ -n "$gh_ver" && "$gh_ver" != "null" ]]; then
            curl -sL "https://github.com/cli/cli/releases/download/v${gh_ver}/gh_${gh_ver}_linux_${arch_go}.tar.gz" \
                | tar xz -C "$tmp"
            cp "${tmp}/gh_${gh_ver}_linux_${arch_go}/bin/gh" "${bin_dir}/gh"
            chmod +x "${bin_dir}/gh"
            success "  gh ${gh_ver}"
        fi
    else
        debug "  gh already available"
    fi

    success "Essential CLI tools installed"
}

# Create default config for non-interactive mode
create_default_config() {
    mkdir -p "$CHEZMOI_CONFIG_DIR"
    cat > "${CHEZMOI_CONFIG_DIR}/chezmoi.toml" <<EOF
# Root-level chezmoi configuration (must be before any sections)
sourceDir = "${HOME}/.files"

[data]
    email = "peter.lee@astrocapital.net"
    name = "Peter Lee"
    hostname = "$(hostname)"
    personal = true
    osid = "$(uname -s | tr '[:upper:]' '[:lower:]')"
    arch = "$(uname -m | sed 's/x86_64/amd64/')"
    isWSL = $(test -f /proc/sys/fs/binfmt_misc/WSLInterop && echo true || echo false)
    isDarwin = $(test "$(uname -s)" = "Darwin" && echo true || echo false)
    isLinux = $(test "$(uname -s)" = "Linux" && echo true || echo false)
    isWindows = false
    pkgmgr = "$(command -v pacman >/dev/null && echo pacman || (command -v brew >/dev/null && echo brew || echo apt))"
    hasOp = $(command -v op >/dev/null && echo true || echo false)
    opSignedIn = false

    [data.infra]
        aws_account_id = "000000000000"
        aws_route53_zone_id = "ZXXXXXXXXXXXXXXXXXX"
        aws_iam_role = "arn:aws:iam::000000000000:role/example-role"
        vpn_host = "vpn.example.com"
        vpn_port = "55555"
        vault_url = "https://vault.example.com"
        docker_registry = "registry.example.com"
        internal_ip = "10.0.0.1"
        internal_port = "8080"
        base_domain = "example.com"

[edit]
    command = "nvim"

[diff]
    pager = "diff-so-fancy"

[git]
    autoCommit = false
    autoPush = false
EOF
}

# Install system prerequisites and 1Password CLI.
# Always installs prereqs and op — no flag parsing.
_restore_prereqs() {
    echo ""
    echo -e "${BOLD}Installing Prerequisites${RESET}"
    echo "────────────────────────────────────────"
    echo ""

    # Detect platform
    detect_platform

    echo "Platform detected:"
    echo "  OS:       $(uname -s)"
    echo "  Arch:     $(uname -m)"
    echo "  Distro:   ${DISTRO:-unknown}"
    echo "  Package:  ${PKGMGR:-unknown}"
    [[ "$IS_WSL" == "true" ]] && echo "  WSL:      yes"
    echo ""

    # Install Homebrew first on macOS
    if [[ "$IS_DARWIN" == "true" ]]; then
        install_homebrew
    fi

    # Define required packages
    local -a base_packages=(
        curl
        wget
        git
        jq
        unzip
    )

    local -a optional_packages=(
        zsh
        tmux
        tree
        htop
        ripgrep
        xclip
    )

    # Add platform-specific package names
    local -a install_packages=()

    info "Checking base prerequisites..."
    for pkg in "${base_packages[@]}"; do
        local pkg_name
        pkg_name=$(get_pkg_name "$pkg")
        if ! has_cmd "$pkg"; then
            install_packages+=("$pkg_name")
            echo "  ✗ $pkg (will install)"
        else
            echo "  ✓ $pkg"
        fi
    done

    info "Checking optional prerequisites..."
    for pkg in "${optional_packages[@]}"; do
        local pkg_name
        pkg_name=$(get_pkg_name "$pkg")
        if ! has_cmd "$pkg"; then
            install_packages+=("$pkg_name")
            echo "  ✗ $pkg (will install)"
        else
            echo "  ✓ $pkg"
        fi
    done

    # Add fd and bat with proper package names
    if ! has_cmd fd && ! has_cmd fdfind; then
        install_packages+=("$(get_pkg_name fd)")
        echo "  ✗ fd (will install)"
    else
        echo "  ✓ fd"
    fi

    if ! has_cmd bat && ! has_cmd batcat; then
        install_packages+=("$(get_pkg_name bat)")
        echo "  ✗ bat (will install)"
    else
        echo "  ✓ bat"
    fi

    echo ""

    # Install missing packages
    if [[ ${#install_packages[@]} -gt 0 ]]; then
        info "Installing ${#install_packages[@]} packages..."
        pkg_install "${install_packages[@]}"
        success "Packages installed"
    else
        success "All base packages already installed"
    fi

    # Create symlinks for fd and bat on Debian/Ubuntu
    if [[ "$PKGMGR" == "apt" ]]; then
        mkdir -p ~/.local/bin
        if [[ -f /usr/bin/fdfind ]] && [[ ! -f ~/.local/bin/fd ]]; then
            ln -sf /usr/bin/fdfind ~/.local/bin/fd
            debug "Created symlink: fd -> fdfind"
        fi
        if [[ -f /usr/bin/batcat ]] && [[ ! -f ~/.local/bin/bat ]]; then
            ln -sf /usr/bin/batcat ~/.local/bin/bat
            debug "Created symlink: bat -> batcat"
        fi
    fi

    echo ""

    # Install 1Password CLI
    info "Checking 1Password CLI..."
    install_1password_cli || true

    echo ""

    # Install chezmoi
    info "Checking chezmoi..."
    if has_cmd chezmoi || [[ -x "$CHEZMOI_BIN" ]]; then
        local chezmoi_version
        chezmoi_version=$(chezmoi --version 2>/dev/null | head -1 || echo "unknown")
        success "chezmoi already installed ($chezmoi_version)"
    else
        ensure_chezmoi
    fi

    echo ""
    echo -e "${BOLD}Summary${RESET}"
    echo "────────────────────────────────────────"
    echo ""
    echo "Core tools:"
    has_cmd curl && success "curl" || error "curl"
    has_cmd git && success "git" || error "git"
    has_cmd jq && success "jq" || error "jq"
    echo ""
    echo "1Password:"
    if has_cmd op; then
        success "op CLI installed"
        if op account list &>/dev/null 2>&1; then
            success "op signed in"
        else
            warn "op not signed in (run 'op signin')"
        fi
    else
        error "op CLI not installed"
    fi
    echo ""
    echo "Chezmoi:"
    has_cmd chezmoi || [[ -x "$CHEZMOI_BIN" ]] && success "chezmoi installed" || error "chezmoi not installed"
    echo ""
}

cmd_restore() {
    local force=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --force|-f)
                force=true
                shift
                ;;
            *)
                error "Unknown option: $1"
                echo "Usage: cli restore [--force]"
                exit 1
                ;;
        esac
    done

    if [[ "$force" == "true" ]]; then
        echo ""
        echo -e "${BOLD}Force Reinstalling Dotfiles${RESET}"
        echo "────────────────────────────────────────"
        echo ""

        # Wipe chezmoi state and external deps first
        info "Cleaning chezmoi state..."
        rm -rf "$CHEZMOI_SOURCE"
        rm -f "${CHEZMOI_CONFIG_DIR}/chezmoistate.boltdb"

        info "Removing external dependencies..."
        rm -rf "${HOME}/.local/share/tmux/plugins/tpm"
        rm -rf "${HOME}/.local/share/zinit"
        rm -rf "${HOME}/.local/share/nvim/lazy/lazy.nvim"
        rm -f "${HOME}/.local/bin/fzf"
        rm -f "${HOME}/.local/bin/nvim.appimage"
    else
        echo ""
        echo -e "${BOLD}Installing Dotfiles${RESET}"
        echo "────────────────────────────────────────"
        echo ""
    fi

    # Install prereqs and 1Password CLI
    _restore_prereqs

    # Handle non-interactive mode
    if [[ ! -t 0 ]]; then
        info "Non-interactive mode detected, using defaults"
        create_default_config
    fi

    # Initialize chezmoi
    if [[ "$force" == "true" ]]; then
        info "Initializing chezmoi..."
        mkdir -p "$CHEZMOI_SOURCE"

        if is_local_source; then
            info "Copying from local source..."
            rsync -a --exclude='.git' "${SCRIPT_DIR}/" "$CHEZMOI_SOURCE/"
            debug "Copied $(find "$CHEZMOI_SOURCE" -type f | wc -l) files"
        else
            "$CHEZMOI_BIN" init "$REPO" --prompt=false
        fi
    else
        if [[ ! -t 0 ]]; then
            # Non-interactive: skip init if local source (config already has sourceDir)
            if is_local_source; then
                info "Using local source: ${SCRIPT_DIR}"
            else
                info "Fetching from: ${REPO}"
                "$CHEZMOI_BIN" init "$REPO" --prompt=false
            fi
        else
            # Interactive mode — let chezmoi handle prompts
            if is_local_source; then
                info "Using local source: ${SCRIPT_DIR}"
                "$CHEZMOI_BIN" init --source "$SCRIPT_DIR"
            else
                info "Fetching from: ${REPO}"
                "$CHEZMOI_BIN" init "$REPO"
            fi
        fi
    fi

    # Apply dotfiles
    info "Applying dotfiles..."
    if [[ ! -t 0 ]] || [[ "$force" == "true" ]]; then
        "$CHEZMOI_BIN" apply --force
    else
        "$CHEZMOI_BIN" apply
    fi

    # Install conda + shared env (Linux only, skips if already present)
    ensure_conda
    ensure_conda_env

    # Install essential CLI tools if conda env is not available
    install_essential_tools

    # Refresh externals on force reinstall
    if [[ "$force" == "true" ]]; then
        info "Refreshing external dependencies..."
        "$CHEZMOI_BIN" apply --refresh-externals 2>&1 || warn "Some externals may have failed"
    fi

    echo ""
    success "Restore complete!"
    echo ""
    echo "Run 'cli status' to see what was installed."
    echo "Run 'chezmoi diff' to see pending changes."
    echo ""
}
