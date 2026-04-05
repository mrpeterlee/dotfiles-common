#!/usr/bin/env bash
# build.sh — Core build function for conda env creation
# Sourced by cli; do not run directly.

build_env() {
    local prefix="$1"
    local config_dir="${SCRIPT_DIR}/env/config"

    info "Creating conda environment at ${prefix}..."
    conda create -y -p "$prefix" \
        -c conda-forge \
        --strict-channel-priority \
        --file "${config_dir}/conda-packages.txt"

    # Remove conda tmux if pulled in as a dependency — the conda-forge
    # build (3.6) crashes on client attach.  System tmux (/usr/bin/tmux)
    # is stable and already on PATH.
    if [[ -x "${prefix}/bin/tmux" ]]; then
        rm -f "${prefix}/bin/tmux"
        info "Removed conda tmux (using system tmux instead)"
    fi

    local env_python="${prefix}/bin/python"
    local env_uv="${prefix}/bin/uv"

    info "Installing pip packages via uv..."
    "$env_uv" pip install --python "$env_python" \
        -r "${config_dir}/pip-packages.txt"

    info "Installing npm CLI tools..."
    local npm_bin="${prefix}/bin/npm"
    if [[ -x "$npm_bin" ]]; then
        # Put the env's bin on PATH so node/npm shebang lines resolve,
        # and set npm prefix so global installs land in the env.
        local saved_path="$PATH"
        export PATH="${prefix}/bin:${PATH}"
        export NPM_CONFIG_PREFIX="$prefix"
        while IFS= read -r pkg || [[ -n "$pkg" ]]; do
            # Skip comments and blank lines
            [[ -z "$pkg" || "$pkg" == \#* ]] && continue
            info "  npm install -g ${pkg}"
            "$npm_bin" install -g "$pkg"
        done < "${config_dir}/npm-tools.txt"
        unset NPM_CONFIG_PREFIX
        export PATH="$saved_path"
    else
        warn "npm not found at ${npm_bin}, skipping npm tools"
    fi

    info "Installing packages from custom indexes..."
    ENV_PYTHON="$env_python" ENV_UV="$env_uv" source "${config_dir}/pip-custom-indexes.sh" || true

    info "Installing standalone CLI tools..."
    source "${SCRIPT_DIR}/env/lib/cli-tools.sh"
    install_cli_tools "$prefix"

    success "Environment built at ${prefix}"
}
