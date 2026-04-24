#!/usr/bin/env bash
#
# apply.sh - Apply agent configs to the system
#
# Assumes lib/common.sh has been sourced.
# Assumes SCRIPT_DIR is set by the caller.

# Per-agent copy-mode install functions
_install_claude() {
    info "Installing Claude Code config..."
    local src="$SCRIPT_DIR/dot_claude"
    local dst="${AGENT_DIRS[claude]}"

    # Top-level files
    for f in CLAUDE.md AGENTS.md settings.json marketplace.json plugin.json keybindings.json; do
        [[ -f "$src/$f" ]] && copy_force "$src/$f" "$dst/$f" "$f"
    done

    # Directories with flat .md or .json files
    for dir in commands plans mcp-configs; do
        [[ -d "$src/$dir" ]] || continue
        mkdir -p "$dst/$dir"
        for f in "$src/$dir"/*; do
            [[ -f "$f" ]] || continue
            local name
            name=$(basename "$f")
            copy_force "$f" "$dst/$dir/$name" "$dir/$name"
        done
    done

    # Recursive directories
    for dir in agents rules scripts skills tasks teams todos channels docs; do
        [[ -d "$src/$dir" ]] || continue
        info "  Syncing $dir/..."

        # Handle chezmoi symlink_ files → create actual symlinks
        for sf in "$src/$dir"/symlink_*; do
            [[ -f "$sf" ]] || continue
            local link_name="${sf##*/symlink_}"
            local link_target
            link_target=$(cat "$sf")
            local link_path="$dst/$dir/$link_name"
            if [[ ! -L "$link_path" ]] || [[ "$(readlink "$link_path")" != "$link_target" ]]; then
                ln -sfn "$link_target" "$link_path"
                success "    $dir/$link_name -> $link_target"
            fi
        done

        # Copy regular files/dirs (skip symlink_ files)
        find "$src/$dir" -mindepth 1 -maxdepth 1 ! -name 'symlink_*' | while read -r entry; do
            local name
            name=$(basename "$entry")
            if [[ -d "$entry" ]]; then
                cp -r "$entry" "$dst/$dir/$name"
            elif [[ -f "$entry" ]]; then
                mkdir -p "$dst/$dir"
                copy_force "$entry" "$dst/$dir/$name" "$dir/$name"
            fi
        done
    done
}

# Inject secrets from 1Password (runs after config apply)
_inject_credentials() {
    if ! has_cmd op; then
        warn "1Password CLI not found — skipping credential injection"
        echo "  Login manually or install op CLI and rerun"
        return 0
    fi

    # Skip if no vault configured (overlay must export AGENTS_OAUTH_VAULT)
    if [[ -z "${AGENTS_OAUTH_VAULT:-}" ]]; then
        warn "AGENTS_OAUTH_VAULT not set — skipping credential injection"
        echo "  Set AGENTS_OAUTH_VAULT=<vault-name> in your overlay to enable"
        return 0
    fi

    # Switch to vault-specific service account if available
    local orig_token="${OP_SERVICE_ACCOUNT_TOKEN:-}"
    if [[ -n "${AGENTS_OAUTH_SA_TOKEN:-}" ]]; then
        export OP_SERVICE_ACCOUNT_TOKEN="$AGENTS_OAUTH_SA_TOKEN"
    fi

    if ! op vault get "$AGENTS_OAUTH_VAULT" --format json &>/dev/null; then
        warn "Cannot access configured vault ($AGENTS_OAUTH_VAULT) — skipping credential injection"
        echo "  Run: op-use <vault-shortcut>   (or set AGENTS_OAUTH_SA_TOKEN)"
        [[ -z "$orig_token" ]] && unset OP_SERVICE_ACCOUNT_TOKEN || export OP_SERVICE_ACCOUNT_TOKEN="$orig_token"
        return 0
    fi

    info "Injecting credentials from 1Password..."

    # Claude Code OAuth — detect active profile from ~/.claude.json
    local profile="${CLAUDE_DEFAULT_PROFILE:-}"
    if [[ -z "$profile" && -f "$HOME/.claude.json" ]]; then
        profile=$(python3 -c "import json; print(json.load(open('$HOME/.claude.json')).get('oauthAccount',{}).get('emailAddress',''))" 2>/dev/null || echo "")
    fi
    local creds
    if [[ -n "$profile" ]]; then
        creds=$(op document get "Claude Code OAuth ($profile)" --vault "$AGENTS_OAUTH_VAULT" 2>/dev/null || echo "")
    fi
    if [[ -z "${creds:-}" || "${creds:-}" == "{}" ]]; then
        creds=$(op document get "Claude Code OAuth" --vault "$AGENTS_OAUTH_VAULT" 2>/dev/null || echo "")
    fi
    if [[ -n "$creds" && "$creds" != "{}" ]]; then
        echo "$creds" > "$HOME/.claude/.credentials.json"
        chmod 600 "$HOME/.claude/.credentials.json"
        success "  Claude Code OAuth credentials injected"
    else
        warn "  Claude Code OAuth not found in 1Password"
    fi

    # Telegram bot token
    local tg_token
    tg_token=$(op read "op://${AGENTS_OAUTH_VAULT}/Telegram Bot Token/credential" 2>/dev/null || echo "")
    if [[ -n "$tg_token" ]]; then
        mkdir -p "$HOME/.claude/channels/telegram"
        echo "TELEGRAM_BOT_TOKEN=$tg_token" > "$HOME/.claude/channels/telegram/.env"
        chmod 600 "$HOME/.claude/channels/telegram/.env"
        success "  Telegram bot token injected"
    else
        warn "  Telegram Bot Token not found in 1Password"
    fi

    # Restore original service account token
    if [[ -z "$orig_token" ]]; then
        unset OP_SERVICE_ACCOUNT_TOKEN
    else
        export OP_SERVICE_ACCOUNT_TOKEN="$orig_token"
    fi
}

_install_codex() {
    info "Installing Codex config..."
    local src="$SCRIPT_DIR/dot_codex"
    local dst="${AGENT_DIRS[codex]}"

    mkdir -p "$dst" "$dst/prompts"

    # Top-level files (strip private_ prefix for chezmoi naming)
    [[ -f "$src/private_config.toml" ]] && copy_force "$src/private_config.toml" "$dst/config.toml" "config.toml"
    [[ -f "$src/AGENTS.md" ]] && copy_force "$src/AGENTS.md" "$dst/AGENTS.md" "AGENTS.md"

    # Prompts
    for prompt_file in "$src"/prompts/*.md; do
        [[ -f "$prompt_file" ]] || continue
        local name
        name=$(basename "$prompt_file")
        copy_force "$prompt_file" "$dst/prompts/$name" "prompts/$name"
    done

    # Memories and skills (non-system)
    for dir in memories skills; do
        [[ -d "$src/$dir" ]] || continue
        mkdir -p "$dst/$dir"
        find "$src/$dir" -mindepth 1 -maxdepth 1 | while read -r entry; do
            local name
            name=$(basename "$entry")
            if [[ -d "$entry" ]]; then
                cp -r "$entry" "$dst/$dir/$name"
            elif [[ -f "$entry" ]]; then
                copy_force "$entry" "$dst/$dir/$name" "$dir/$name"
            fi
        done
    done
}

_install_opencode() {
    info "Installing OpenCode config..."
    local src="$SCRIPT_DIR/dot_opencode"
    local dst="${AGENT_DIRS[opencode]}"

    mkdir -p "$dst"

    copy_force "$src/opencode.json" "$dst/opencode.json" "opencode.json"
    copy_force "$src/AGENTS.md" "$dst/AGENTS.md" "AGENTS.md"
}

_install_gemini() {
    info "Installing Gemini CLI config..."
    local src="$SCRIPT_DIR/dot_gemini"
    local dst="${AGENT_DIRS[gemini]}"

    mkdir -p "$dst"

    copy_force "$src/settings.json" "$dst/settings.json" "settings.json"
    copy_force "$src/GEMINI.md" "$dst/GEMINI.md" "GEMINI.md"
}

# Apply a single agent's config via copy mode
_apply_copy_agent() {
    local agent="$1"
    case "$agent" in
        claude)   _install_claude ;;
        codex)    _install_codex ;;
        opencode) _install_opencode ;;
        gemini)   _install_gemini ;;
        *)
            error "Unknown agent: $agent"
            echo "  Available: ${AGENTS[*]}"
            return 1
            ;;
    esac
}

# Apply configs via chezmoi (handles templates + 1Password)
_apply_chezmoi() {
    # Generate a local chezmoi config for this source dir
    local config_dir="$SCRIPT_DIR/.chezmoi-config"
    mkdir -p "$config_dir"

    # Detect 1Password mode
    local op_mode="account"
    local has_op="false"
    local use_op="no"
    if has_cmd op; then
        if [[ -n "${OP_SERVICE_ACCOUNT_TOKEN:-}" ]]; then
            op_mode="service"
            has_op="true"
            use_op="yes"
        fi
    fi

    cat > "$config_dir/chezmoi.toml" <<CONF
[data]
    name = "$(whoami)"
    useOp = "$use_op"
    hasOp = $has_op

[onepassword]
    mode = "$op_mode"
CONF

    info "Running chezmoi apply..."
    "$CHEZMOI" --config "$config_dir/chezmoi.toml" -S "$SCRIPT_DIR" apply --force

    # Status report
    info "Credentials:"
    if has_cmd op; then
        success "  1Password CLI found — credentials applied"
    else
        warn "  1Password CLI not found — credentials skipped (login manually)"
    fi
}

cmd_apply() {
    local agent="${1:-all}"

    echo ""
    echo -e "${BOLD}Applying Agent Configs${RESET}"
    echo "────────────────────────────────────────"
    echo ""

    # Try chezmoi mode first, fall back to copy mode
    if has_cmd chezmoi || [[ -x "${HOME}/.local/bin/chezmoi" ]]; then
        if [[ "$agent" != "all" ]]; then
            warn "chezmoi mode applies all agents — '$agent' filter ignored"
        fi
        ensure_chezmoi
        _apply_chezmoi
    else
        info "chezmoi not found — using copy mode"
        echo ""

        if [[ "$agent" == "all" ]]; then
            for a in "${AGENTS[@]}"; do
                _apply_copy_agent "$a"
                echo ""
            done
        else
            _apply_copy_agent "$agent"
        fi
    fi

    # Inject credentials from 1Password
    _inject_credentials
    echo ""

    # Install gstack skills
    info "Installing gstack skills..."
    local gstack_dst="${HOME}/.claude/skills/gstack"
    if [[ -d "$gstack_dst" ]]; then
        success "  gstack already installed — skipping"
    else
        git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git "$gstack_dst" \
            && (cd "$gstack_dst" && ./setup) \
            && success "  gstack installed" \
            || warn "  gstack installation failed — continuing"
    fi

    echo ""
    success "Apply complete!"
    echo ""

    # Additional setup instructions
    echo ""
    echo -e "${BOLD}┌─────────────────────────────────────────────────────┐${RESET}"
    echo -e "${BOLD}│         Next: Install Everything Claude Code        │${RESET}"
    echo -e "${BOLD}└─────────────────────────────────────────────────────┘${RESET}"
    echo ""
    echo -e "  ${CYAN}${BOLD}Step 1${RESET}  Add the marketplace"
    echo -e "  ${DIM}────────────────────────────────────────────────${RESET}"
    echo -e "  /plugin marketplace add https://github.com/affaan-m/everything-claude-code"
    echo ""
    echo -e "  ${CYAN}${BOLD}Step 2${RESET}  Install the plugin"
    echo -e "  ${DIM}────────────────────────────────────────────────${RESET}"
    echo -e "  /plugin install ecc@ecc"
    echo ""
    echo -e "  ${CYAN}${BOLD}Step 3${RESET}  Clone, install, and configure"
    echo -e "  ${DIM}────────────────────────────────────────────────${RESET}"
    echo -e "  cd /tmp"
    echo -e "  git clone https://github.com/affaan-m/everything-claude-code.git"
    echo -e "  cd everything-claude-code"
    echo -e "  npm install"
    echo -e "  ./install.sh --profile full"
    echo -e "  rm -rf /tmp/everything-claude-code"
    echo ""
    echo -e "  ${CYAN}${BOLD}Step 4${RESET}  Add UI/UX Pro Max skill"
    echo -e "  ${DIM}────────────────────────────────────────────────${RESET}"
    echo -e "  /plugin marketplace add nextlevelbuilder/ui-ux-pro-max-skill"
    echo -e "  /plugin install ui-ux-pro-max@ui-ux-pro-max-skill"
    echo ""
    echo -e "  ${DIM}More info: https://github.com/affaan-m/everything-claude-code${RESET}"
    echo ""
}
