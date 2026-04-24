#!/usr/bin/env bash
#
# backup.sh - Capture live system changes back into the repo
#
# Assumes lib/common.sh has been sourced.
# Assumes SCRIPT_DIR is set by the caller.

# Backup a single OAuth file to 1Password
_backup_oauth_file() {
    local file="$1"
    local doc_name="$2"
    local vault="$3"

    if [[ ! -f "$file" ]]; then
        warn "  $doc_name: skipped (file not found)"
        return 1
    fi

    if [[ ! -s "$file" ]]; then
        warn "  $doc_name: skipped (empty file)"
        return 1
    fi

    if op item get "$doc_name" --vault "$vault" &>/dev/null; then
        if op document edit "$doc_name" --vault "$vault" "$file" 2>/dev/null; then
            success "  $doc_name: updated"
        else
            error "  $doc_name: failed to update"
            return 1
        fi
    else
        if op document create "$file" --vault "$vault" --title "$doc_name" 2>/dev/null; then
            success "  $doc_name: created"
        else
            error "  $doc_name: failed to create"
            return 1
        fi
    fi
}

# Backup OAuth tokens to 1Password (vault from $AGENTS_OAUTH_VAULT)
_backup_oauth() {
    if ! has_cmd op; then
        warn "1Password CLI not found — skipping OAuth backup"
        return 0
    fi

    # Skip if no vault configured (overlay must export AGENTS_OAUTH_VAULT)
    if [[ -z "${AGENTS_OAUTH_VAULT:-}" ]]; then
        warn "AGENTS_OAUTH_VAULT not set — skipping OAuth backup"
        echo "  Set AGENTS_OAUTH_VAULT=<vault-name> in your overlay to enable"
        return 0
    fi

    info "Backing up OAuth tokens..."

    # Switch to vault-specific service account if available
    local orig_token="${OP_SERVICE_ACCOUNT_TOKEN:-}"
    if [[ -n "${AGENTS_OAUTH_SA_TOKEN:-}" ]]; then
        export OP_SERVICE_ACCOUNT_TOKEN="$AGENTS_OAUTH_SA_TOKEN"
    fi

    # Verify vault access
    if ! op vault get "$AGENTS_OAUTH_VAULT" --format json &>/dev/null; then
        warn "Cannot access configured vault ($AGENTS_OAUTH_VAULT) — skipping OAuth backup"
        echo "  Run: op-use <vault-shortcut>   (or set AGENTS_OAUTH_SA_TOKEN)"
        export OP_SERVICE_ACCOUNT_TOKEN="$orig_token"
        return 0
    fi

    local backed_up=0

    # Back up Claude Code OAuth per profile (source of truth)
    local profiles_dir="$HOME/.acap/cc/profiles"
    if [[ -d "$profiles_dir" ]]; then
        for profile_dir in "$profiles_dir"/*/; do
            [[ -d "$profile_dir" ]] || continue
            local email
            email=$(basename "$profile_dir")
            local creds_file="$profile_dir/.credentials.json"
            _backup_oauth_file "$creds_file" "Claude Code OAuth ($email)" "$AGENTS_OAUTH_VAULT" \
                && backed_up=$((backed_up + 1)) || true
        done
    else
        # Fallback: no profiles dir, back up active credentials
        _backup_oauth_file "$HOME/.claude/.credentials.json" "Claude Code OAuth" "$AGENTS_OAUTH_VAULT" \
            && backed_up=$((backed_up + 1)) || true
    fi

    _backup_oauth_file "$HOME/.codex/auth.json" "Codex OAuth" "$AGENTS_OAUTH_VAULT" \
        && backed_up=$((backed_up + 1)) || true
    _backup_oauth_file "$HOME/.gemini/oauth_creds.json" "Gemini OAuth" "$AGENTS_OAUTH_VAULT" \
        && backed_up=$((backed_up + 1)) || true

    # Restore original service account token
    if [[ -z "$orig_token" ]]; then
        unset OP_SERVICE_ACCOUNT_TOKEN
    else
        export OP_SERVICE_ACCOUNT_TOKEN="$orig_token"
    fi

    if [[ "$backed_up" -gt 0 ]]; then
        success "$backed_up OAuth token(s) backed up to 1Password ($AGENTS_OAUTH_VAULT)"
    else
        warn "No OAuth tokens backed up"
    fi
}

cmd_backup() {
    local skip_oauth=false

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --skip-oauth) skip_oauth=true; shift ;;
            *) error "Unknown option: $1"; exit 1 ;;
        esac
    done

    echo ""
    echo -e "${BOLD}Backing Up Agent Configs${RESET}"
    echo "────────────────────────────────────────"
    echo ""

    # 1. Chezmoi full add to discover new files + sync changes
    ensure_chezmoi

    info "Syncing ~/.claude to source (chezmoi add)..."
    local changed=0
    local add_output
    add_output=$("$CHEZMOI" -S "$SCRIPT_DIR" add --force --secrets=ignore -v "$HOME/.claude" 2>&1) || true
    if [[ -n "$add_output" ]]; then
        while IFS= read -r line; do
            # Strip ANSI escape codes for matching
            local clean_line
            clean_line=$(echo "$line" | sed 's/\x1b\[[0-9;]*m//g')
            if [[ "$clean_line" == *"added:"* ]] || [[ "$clean_line" == *"modified:"* ]]; then
                success "  $clean_line"
                changed=$((changed + 1))
            fi
        done <<< "$add_output"
    fi

    # Remove gstack-linked private_ dirs (managed by gstack, not chezmoi)
    for d in "$SCRIPT_DIR"/dot_claude/skills/private_*/; do
        [[ -d "$d" ]] && rm -rf "$d"
    done
    # Remove gstack repo if accidentally added
    [[ -d "$SCRIPT_DIR/dot_claude/skills/gstack" ]] && rm -rf "$SCRIPT_DIR/dot_claude/skills/gstack"

    if [[ "$changed" -gt 0 ]]; then
        info "$changed file(s) synced"
    else
        success "All config files unchanged"
    fi
    echo ""

    # 2. OAuth backup
    if [[ "$skip_oauth" == "false" ]]; then
        _backup_oauth
        echo ""
    fi

    # 3. Show changed + untracked files
    local changes
    changes=$(cd "$SCRIPT_DIR" && git status --short 2>/dev/null || true)

    if [[ -n "$changes" ]]; then
        info "Changed files in repo:"
        echo "$changes" | while read -r line; do
            echo "  $line"
        done
        echo ""
        echo "  Next: run 'cd "$SCRIPT_DIR" && git diff' to review"
        echo "        then 'git add <files> && git commit && git push'"
    else
        success "No changes in repo"
    fi
    echo ""
}
