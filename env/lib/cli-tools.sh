#!/usr/bin/env bash
# cli-tools.sh — Install standalone CLI binaries into the conda env
# Sourced by build.sh; do not run directly.

install_cli_tools() {
    local prefix="$1"
    local bin_dir="${prefix}/bin"
    local arch
    arch=$(uname -m)

    # Normalise arch for download URLs
    case "$arch" in
        x86_64)  arch_go="amd64"; arch_alt="x86_64" ;;
        aarch64) arch_go="arm64"; arch_alt="aarch64" ;;
        *)
            warn "Unsupported architecture: ${arch}"
            return 1
            ;;
    esac

    local tmp
    tmp=$(mktemp -d)
    trap "rm -rf '$tmp'" RETURN

    _install_gh       "$bin_dir" "$arch_go" "$tmp"
    _install_kubectl  "$bin_dir" "$arch_go"
    _install_argocd   "$bin_dir" "$arch_go"
    _install_helm     "$bin_dir" "$arch_go" "$tmp"
    _install_aliyun   "$bin_dir" "$arch_go" "$tmp"
    _install_yazi     "$bin_dir" "$arch_alt" "$tmp"
    _install_sesh     "$bin_dir" "$arch_go" "$arch_alt" "$tmp"
    _install_nvim     "$bin_dir" "$tmp"
    _install_twm      "$prefix" "$bin_dir"
    _install_aws      "$bin_dir" "$tmp"
    _install_ohmyposh "$bin_dir" "$arch_go"
    _install_tmuxinator "$prefix" "$bin_dir" "$tmp"

    success "Standalone CLI tools installed"
}

# ── GitHub CLI (gh) ──────────────────────────────────────────────────────────

_install_gh() {
    local bin_dir="$1" arch="$2" tmp="$3"
    info "Installing gh..."
    local version
    version=$(curl -sL https://api.github.com/repos/cli/cli/releases/latest | jq -r '.tag_name' | sed 's/^v//')
    if [[ -z "$version" || "$version" == "null" ]]; then
        warn "Could not determine gh version, skipping"
        return 0
    fi
    curl -sL "https://github.com/cli/cli/releases/download/v${version}/gh_${version}_linux_${arch}.tar.gz" \
        | tar xz -C "$tmp"
    cp "${tmp}/gh_${version}_linux_${arch}/bin/gh" "${bin_dir}/gh"
    chmod +x "${bin_dir}/gh"
    success "gh ${version}"
}

# ── kubectl ──────────────────────────────────────────────────────────────────

_install_kubectl() {
    local bin_dir="$1" arch="$2"
    info "Installing kubectl..."
    local version
    version=$(curl -sL https://dl.k8s.io/release/stable.txt)
    if [[ -z "$version" ]]; then
        warn "Could not determine kubectl version, skipping"
        return 0
    fi
    curl -sLo "${bin_dir}/kubectl" \
        "https://dl.k8s.io/release/${version}/bin/linux/${arch}/kubectl"
    chmod +x "${bin_dir}/kubectl"
    success "kubectl ${version}"
}

# ── ArgoCD CLI ───────────────────────────────────────────────────────────────

_install_argocd() {
    local bin_dir="$1" arch="$2"
    info "Installing argocd..."
    local version
    version=$(curl -sL https://api.github.com/repos/argoproj/argo-cd/releases/latest | jq -r '.tag_name')
    if [[ -z "$version" || "$version" == "null" ]]; then
        warn "Could not determine argocd version, skipping"
        return 0
    fi
    curl -sLo "${bin_dir}/argocd" \
        "https://github.com/argoproj/argo-cd/releases/download/${version}/argocd-linux-${arch}"
    chmod +x "${bin_dir}/argocd"
    success "argocd ${version}"
}

# ── Helm ─────────────────────────────────────────────────────────────────────

_install_helm() {
    local bin_dir="$1" arch="$2" tmp="$3"
    info "Installing helm..."
    local version
    version=$(curl -sL https://api.github.com/repos/helm/helm/releases/latest | jq -r '.tag_name')
    if [[ -z "$version" || "$version" == "null" ]]; then
        warn "Could not determine helm version, skipping"
        return 0
    fi
    curl -sL "https://get.helm.sh/helm-${version}-linux-${arch}.tar.gz" \
        | tar xz -C "$tmp"
    cp "${tmp}/linux-${arch}/helm" "${bin_dir}/helm"
    chmod +x "${bin_dir}/helm"
    success "helm ${version}"
}

# ── Alibaba Cloud CLI (aliyun) ───────────────────────────────────────────────

_install_aliyun() {
    local bin_dir="$1" arch="$2" tmp="$3"
    info "Installing aliyun..."
    local tag
    tag=$(curl -sL https://api.github.com/repos/aliyun/aliyun-cli/releases/latest | jq -r '.tag_name')
    if [[ -z "$tag" || "$tag" == "null" ]]; then
        warn "Could not determine aliyun version, skipping"
        return 0
    fi
    # Tag is "v3.x.x" but filenames use bare "3.x.x"
    local version="${tag#v}"
    curl -sLo "${tmp}/aliyun-cli.tgz" \
        "https://github.com/aliyun/aliyun-cli/releases/download/${tag}/aliyun-cli-linux-${version}-${arch}.tgz"
    tar xzf "${tmp}/aliyun-cli.tgz" -C "${bin_dir}/"
    chmod +x "${bin_dir}/aliyun"
    success "aliyun ${version}"
}

# ── Yazi (terminal file manager) ────────────────────────────────────────────

_install_yazi() {
    local bin_dir="$1" arch_alt="$2" tmp="$3"
    info "Installing yazi..."
    local tag
    tag=$(curl -sL https://api.github.com/repos/sxyazi/yazi/releases/latest | jq -r '.tag_name')
    if [[ -z "$tag" || "$tag" == "null" ]]; then
        warn "Could not determine yazi version, skipping"
        return 0
    fi
    local version="${tag#v}"
    curl -sL "https://github.com/sxyazi/yazi/releases/download/${tag}/yazi-${arch_alt}-unknown-linux-gnu.zip" \
        -o "${tmp}/yazi.zip"
    # Use Python to extract zip (unzip may not be installed)
    python3 -c "import zipfile,sys; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" \
        "${tmp}/yazi.zip" "${tmp}/yazi-extract"
    cp "${tmp}/yazi-extract/yazi-${arch_alt}-unknown-linux-gnu/yazi" "${bin_dir}/yazi"
    chmod +x "${bin_dir}/yazi"
    success "yazi ${version}"
}

# ── Sesh (tmux session manager) ─────────────────────────────────────────────

_install_sesh() {
    local bin_dir="$1" arch_go="$2" arch_alt="$3" tmp="$4"
    info "Installing sesh..."
    local tag
    tag=$(curl -sL https://api.github.com/repos/joshmedeski/sesh/releases/latest | jq -r '.tag_name')
    if [[ -z "$tag" || "$tag" == "null" ]]; then
        warn "Could not determine sesh version, skipping"
        return 0
    fi
    local version="${tag#v}"
    # Sesh uses Linux_x86_64 / Linux_arm64 naming
    local sesh_arch
    case "$arch_go" in
        amd64) sesh_arch="x86_64" ;;
        arm64) sesh_arch="arm64" ;;
    esac
    curl -sL "https://github.com/joshmedeski/sesh/releases/download/${tag}/sesh_Linux_${sesh_arch}.tar.gz" \
        | tar xz -C "$tmp"
    cp "${tmp}/sesh" "${bin_dir}/sesh"
    chmod +x "${bin_dir}/sesh"
    success "sesh ${version}"
}

# ── Neovim ──────────────────────────────────────────────────────────────────

_install_nvim() {
    local bin_dir="$1" tmp="$2"
    info "Installing nvim..."
    local tag
    tag=$(curl -sL https://api.github.com/repos/neovim/neovim/releases/latest | jq -r '.tag_name')
    if [[ -z "$tag" || "$tag" == "null" ]]; then
        warn "Could not determine nvim version, skipping"
        return 0
    fi
    local nvim_arch
    case "$(uname -m)" in
        x86_64)  nvim_arch="x86_64" ;;
        aarch64) nvim_arch="arm64" ;;
        *)       warn "Unsupported arch for nvim: $(uname -m)"; return 0 ;;
    esac
    curl -sLo "${tmp}/nvim-linux-${nvim_arch}.tar.gz" \
        "https://github.com/neovim/neovim/releases/download/${tag}/nvim-linux-${nvim_arch}.tar.gz"
    tar xzf "${tmp}/nvim-linux-${nvim_arch}.tar.gz" -C "$tmp"
    cp "${tmp}/nvim-linux-${nvim_arch}/bin/nvim" "${bin_dir}/nvim"
    chmod +x "${bin_dir}/nvim"
    # Also copy runtime files needed by nvim
    local share_dir="${bin_dir}/../share"
    if [[ -d "${tmp}/nvim-linux-${nvim_arch}/share/nvim" ]]; then
        mkdir -p "${share_dir}"
        cp -r "${tmp}/nvim-linux-${nvim_arch}/share/nvim" "${share_dir}/"
    fi
    success "nvim ${tag}"
}

# ── TWM (tmux workspace manager) ────────────────────────────────────────────

_install_twm() {
    local prefix="$1" bin_dir="$2"
    info "Installing twm via cargo..."
    # TWM has no prebuilt binaries; build from source using the env's Rust toolchain
    local saved_path="$PATH"
    export PATH="${prefix}/bin:${PATH}"
    if ! command -v cargo &>/dev/null; then
        warn "cargo not found, skipping twm"
        export PATH="$saved_path"
        return 0
    fi
    # c-compiler conda package provides <arch>-conda-linux-gnu-cc; also try plain cc/gcc
    local conda_cc
    conda_cc="$(command -v "$(uname -m)-conda-linux-gnu-cc" 2>/dev/null \
             || command -v cc 2>/dev/null \
             || command -v gcc 2>/dev/null \
             || true)"
    if [[ -z "$conda_cc" ]]; then
        warn "No C compiler found, skipping twm"
        export PATH="$saved_path"
        return 0
    fi
    CC="$conda_cc" CARGO_INSTALL_ROOT="$prefix" cargo install twm 2>&1 | tail -3 || true
    if [[ -x "${bin_dir}/twm" ]]; then
        success "twm $(${bin_dir}/twm --version 2>&1 || echo 'installed')"
    else
        warn "twm build failed"
    fi
    export PATH="$saved_path"
}

# ── AWS CLI v2 ──────────────────────────────────────────────────────────────

_install_aws() {
    local bin_dir="$1" tmp="$2"
    info "Installing aws-cli v2..."
    local arch
    arch=$(uname -m)
    curl -sLo "${tmp}/awscli.zip" \
        "https://awscli.amazonaws.com/awscli-exe-linux-${arch}.zip"
    python3 -c "import zipfile,sys; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" \
        "${tmp}/awscli.zip" "${tmp}/awscli-extract"
    # Python zipfile doesn't preserve Unix permissions; restore execute bits
    chmod -R +x "${tmp}/awscli-extract/aws/"
    "${tmp}/awscli-extract/aws/install" --install-dir "${bin_dir}/../lib/aws-cli" --bin-dir "${bin_dir}" --update 2>&1 | tail -3
    if [[ -x "${bin_dir}/aws" ]]; then
        success "aws $("${bin_dir}/aws" --version 2>&1 | awk '{print $1}')"
    else
        warn "aws-cli v2 install failed"
    fi
}

# ── Oh My Posh (prompt theme engine) ────────────────────────────────────────

_install_ohmyposh() {
    local bin_dir="$1" arch="$2"
    info "Installing oh-my-posh..."
    local tag
    tag=$(curl -sL https://api.github.com/repos/JanDeDobbeleer/oh-my-posh/releases/latest | jq -r '.tag_name')
    if [[ -z "$tag" || "$tag" == "null" ]]; then
        warn "Could not determine oh-my-posh version, skipping"
        return 0
    fi
    curl -sLo "${bin_dir}/oh-my-posh" \
        "https://github.com/JanDeDobbeleer/oh-my-posh/releases/download/${tag}/posh-linux-${arch}"
    chmod +x "${bin_dir}/oh-my-posh"
    success "oh-my-posh ${tag}"
}

# ── Tmuxinator (tmux session manager) ───────────────────────────────────────

_install_tmuxinator() {
    local prefix="$1" bin_dir="$2" tmp="$3"
    info "Installing tmuxinator..."
    local tag
    tag=$(curl -sL https://api.github.com/repos/tmuxinator/tmuxinator/releases/latest | jq -r '.tag_name')
    if [[ -z "$tag" || "$tag" == "null" ]]; then
        warn "Could not determine tmuxinator version, skipping"
        return 0
    fi
    local version="${tag#v}"
    curl -sLo "${tmp}/tmuxinator-${version}.gem" \
        "https://github.com/tmuxinator/tmuxinator/releases/download/${tag}/tmuxinator-${version}.gem"
    if [[ ! -f "${tmp}/tmuxinator-${version}.gem" ]]; then
        warn "Failed to download tmuxinator gem, skipping"
        return 0
    fi
    # Install gem into the conda env's default rubygems directory.
    # Conda's ruby_activate.sh sets GEM_HOME=$CONDA_PREFIX/share/rubygems/
    # and adds its bin/ to PATH, so no symlink is needed.
    "${bin_dir}/gem" install --no-document "${tmp}/tmuxinator-${version}.gem" 2>&1 | tail -3
    if [[ -f "${prefix}/share/rubygems/bin/tmuxinator" ]]; then
        success "tmuxinator ${version}"
    else
        warn "tmuxinator gem install did not produce a binary"
    fi
}
