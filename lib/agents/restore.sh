#!/usr/bin/env bash
#
# restore.sh - Full agent setup from scratch
#
# Assumes lib/common.sh has been sourced.
# Assumes SCRIPT_DIR is set by the caller.

# Install 1Password CLI if missing
_install_1password_cli() {
    if has_cmd op; then
        local ver
        ver=$(op --version 2>/dev/null || echo "unknown")
        success "  1Password CLI ($ver)"
        return 0
    fi

    info "  Installing 1Password CLI..."

    # Detect platform
    local os arch
    os=$(uname -s | tr '[:upper:]' '[:lower:]')
    arch=$(uname -m)
    case "$arch" in
        x86_64)  arch="amd64" ;;
        aarch64) arch="arm64" ;;
    esac

    if [[ "$os" == "linux" ]]; then
        # Try package manager first
        if has_cmd apt-get; then
            curl -sS https://downloads.1password.com/linux/keys/1password.asc | \
                sudo gpg --batch --yes --dearmor --output /usr/share/keyrings/1password-archive-keyring.gpg 2>/dev/null
            echo "deb [arch=${arch} signed-by=/usr/share/keyrings/1password-archive-keyring.gpg] https://downloads.1password.com/linux/debian/${arch} stable main" | \
                sudo tee /etc/apt/sources.list.d/1password.list >/dev/null
            sudo apt-get update -qq && sudo apt-get install -y -qq 1password-cli
        else
            # Direct binary download fallback
            local tmp
            tmp=$(mktemp -d)
            curl -sSfo "${tmp}/op.zip" \
                "https://cache.agilebits.com/dist/1P/op2/pkg/v2.30.3/op_${os}_${arch}_v2.30.3.zip"
            unzip -oq "${tmp}/op.zip" -d "${tmp}/"
            install -m 755 "${tmp}/op" "${HOME}/.local/bin/op"
            rm -rf "$tmp"
        fi

        if has_cmd op; then
            success "  1Password CLI installed"
        else
            warn "  1Password CLI installation failed (non-fatal)"
        fi
    elif [[ "$os" == "darwin" ]]; then
        if has_cmd brew; then
            brew install --cask 1password-cli
            success "  1Password CLI installed via Homebrew"
        else
            warn "  Cannot install 1Password CLI without Homebrew (non-fatal)"
        fi
    else
        warn "  Unsupported platform for 1Password CLI: $os (non-fatal)"
    fi
}

# Install an agent CLI via npm if missing
_install_agent_cli() {
    local cmd="$1"
    local pkg="$2"
    local label="$3"

    if has_cmd "$cmd"; then
        local ver
        ver=$("$cmd" --version 2>/dev/null | head -1 || echo "unknown")
        success "  $label ($ver)"
        return 0
    fi

    if ! has_cmd npm && ! has_cmd npx; then
        warn "  $label: npm/npx not found — skipping (install Node.js first)"
        return 0
    fi

    info "  Installing $label..."
    if npm install -g "$pkg" 2>/dev/null; then
        success "  $label installed"
    else
        warn "  $label: npm install failed (non-fatal, try: npm install -g $pkg)"
    fi
}

# Install MCP servers from mcp/servers.json
_install_mcp_servers() {
    local mcp_file="$SCRIPT_DIR/mcp/servers.json"

    if [[ ! -f "$mcp_file" ]]; then
        warn "No MCP config found: $mcp_file"
        return 0
    fi

    if ! has_cmd claude; then
        warn "claude CLI not found — skipping MCP server install"
        return 0
    fi

    if ! has_cmd jq; then
        warn "jq not found — skipping MCP server install"
        return 0
    fi

    info "Installing MCP servers..."

    local count
    count=$(jq '.servers | length' "$mcp_file")

    for ((i = 0; i < count; i++)); do
        local name server_cmd scope
        name=$(jq -r ".servers[$i].name" "$mcp_file")
        server_cmd=$(jq -r ".servers[$i].command" "$mcp_file")
        scope=$(jq -r ".servers[$i].scope // \"user\"" "$mcp_file")

        local args_json
        args_json=$(jq -r ".servers[$i].args // [] | .[]" "$mcp_file")

        local cmd_args=()
        cmd_args+=(claude mcp add)
        [[ "$scope" != "user" ]] && cmd_args+=(--scope "$scope")
        cmd_args+=("$name" -- "$server_cmd")

        while IFS= read -r arg; do
            [[ -n "$arg" ]] && cmd_args+=("$arg")
        done <<< "$args_json"

        if "${cmd_args[@]}" 2>/dev/null; then
            success "  $name installed"
        else
            warn "  $name may already exist or failed (non-fatal)"
        fi
    done
}

_restore_oauth_file() {
    local doc_name="$1"
    local target="$2"
    local vault="$3"

    if ! op item get "$doc_name" --vault "$vault" &>/dev/null; then
        debug "  $doc_name: not found in vault"
        return 1
    fi

    mkdir -p "$(dirname "$target")"

    if op document get "$doc_name" --vault "$vault" --out-file "$target" 2>/dev/null; then
        success "  $doc_name → $target"
    else
        warn "  $doc_name: failed to restore"
        return 1
    fi
}

# Restore OAuth tokens from 1Password (reverse of backup)
_restore_oauth() {
    if ! has_cmd op; then
        warn "1Password CLI not found — skipping OAuth restore"
        return 0
    fi

    # Skip if no vault configured (overlay must export AGENTS_OAUTH_VAULT)
    if [[ -z "${AGENTS_OAUTH_VAULT:-}" ]]; then
        warn "AGENTS_OAUTH_VAULT not set — skipping OAuth restore"
        echo "  Set AGENTS_OAUTH_VAULT=<vault-name> in your overlay to enable"
        return 0
    fi

    info "Restoring OAuth tokens from 1Password..."

    # Switch to vault-specific service account if available
    local orig_token="${OP_SERVICE_ACCOUNT_TOKEN:-}"
    if [[ -n "${AGENTS_OAUTH_SA_TOKEN:-}" ]]; then
        export OP_SERVICE_ACCOUNT_TOKEN="$AGENTS_OAUTH_SA_TOKEN"
    fi

    if ! op vault get "$AGENTS_OAUTH_VAULT" --format json &>/dev/null; then
        warn "Cannot access configured vault ($AGENTS_OAUTH_VAULT) — skipping OAuth restore"
        if [[ -z "$orig_token" ]]; then
            unset OP_SERVICE_ACCOUNT_TOKEN
        else
            export OP_SERVICE_ACCOUNT_TOKEN="$orig_token"
        fi
        return 0
    fi

    local restored=0

    # Detect active Claude account from ~/.claude.json
    local active_email=""
    if [[ -f "$HOME/.claude.json" ]] && has_cmd python3; then
        active_email=$(python3 -c "
import json, sys
try:
    d = json.load(open('$HOME/.claude.json'))
    print(d.get('oauthAccount', {}).get('emailAddress', ''))
except: pass
" 2>/dev/null || true)
    fi

    # Restore Claude Code OAuth for the active account
    local active_restored=false
    if [[ -n "$active_email" ]]; then
        if _restore_oauth_file "Claude Code OAuth ($active_email)" "$HOME/.claude/.credentials.json" "$AGENTS_OAUTH_VAULT"; then
            restored=$((restored + 1))
            active_restored=true
        fi
    fi

    # Restore all profile credentials to their profile directories
    local profiles_dir="$HOME/.acap/cc/profiles"
    if [[ -d "$profiles_dir" ]]; then
        for profile_dir in "$profiles_dir"/*/; do
            [[ -d "$profile_dir" ]] || continue
            local email
            email=$(basename "$profile_dir")
            local creds_file="$profile_dir/.credentials.json"
            if _restore_oauth_file "Claude Code OAuth ($email)" "$creds_file" "$AGENTS_OAUTH_VAULT"; then
                restored=$((restored + 1))
            fi
        done
    fi

    # Fallback: try legacy single-document name
    if [[ "$active_restored" == "false" ]]; then
        _restore_oauth_file "Claude Code OAuth" "$HOME/.claude/.credentials.json" "$AGENTS_OAUTH_VAULT" \
            && restored=$((restored + 1)) || true
    fi

    _restore_oauth_file "Codex OAuth" "$HOME/.codex/auth.json" "$AGENTS_OAUTH_VAULT" \
        && restored=$((restored + 1)) || true
    _restore_oauth_file "Gemini OAuth" "$HOME/.gemini/oauth_creds.json" "$AGENTS_OAUTH_VAULT" \
        && restored=$((restored + 1)) || true

    # Restore original token
    if [[ -z "$orig_token" ]]; then
        unset OP_SERVICE_ACCOUNT_TOKEN
    else
        export OP_SERVICE_ACCOUNT_TOKEN="$orig_token"
    fi

    if [[ "$restored" -gt 0 ]]; then
        success "$restored OAuth token(s) restored from 1Password"
    else
        warn "No OAuth tokens restored"
    fi
}

cmd_restore() {
    local force=false

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --force) force=true; shift ;;
            *) error "Unknown option: $1"; exit 1 ;;
        esac
    done

    echo ""
    echo -e "${BOLD}Restoring Agent Configs (Full Setup)${RESET}"
    echo "────────────────────────────────────────"
    echo ""

    if [[ "$force" == "false" ]]; then
        # Check if configs already exist
        local existing=0
        for agent in "${AGENTS[@]}"; do
            [[ -d "${AGENT_DIRS[$agent]}" ]] && existing=$((existing + 1))
        done

        if [[ "$existing" -gt 0 ]]; then
            warn "$existing agent config dir(s) already exist."
            echo "  Use --force to overwrite without prompting."
            echo ""
            read -rp "  Continue and overwrite? [y/N] " answer
            if [[ "${answer,,}" != "y" ]]; then
                echo "  Aborted."
                exit 0
            fi
            echo ""
        fi
    fi

    # 1. Prerequisites
    echo -e "${BOLD}Checking Prerequisites${RESET}"
    echo ""

    ensure_chezmoi

    _install_1password_cli || true

    info "Checking agent CLIs..."
    _install_agent_cli "claude" "@anthropic-ai/claude-code" "Claude Code CLI" || true
    _install_agent_cli "codex" "@openai/codex" "Codex CLI" || true
    # opencode and gemini — check only, no known npm package for auto-install
    if has_cmd opencode; then
        success "  OpenCode CLI ($(opencode --version 2>/dev/null | head -1 || echo "found"))"
    else
        warn "  OpenCode CLI not found (install manually)"
    fi
    if has_cmd gemini; then
        success "  Gemini CLI ($(gemini --version 2>/dev/null | head -1 || echo "found"))"
    else
        warn "  Gemini CLI not found (install manually if needed)"
    fi
    echo ""

    # 2. Apply all configs
    source "${SCRIPT_DIR}/lib/apply.sh"
    cmd_apply all
    echo ""

    # 3. Install MCP servers
    _install_mcp_servers
    echo ""

    # 4. Restore OAuth tokens
    _restore_oauth
    echo ""

    # 5. Status report
    source "${SCRIPT_DIR}/lib/status.sh"
    cmd_status
}
