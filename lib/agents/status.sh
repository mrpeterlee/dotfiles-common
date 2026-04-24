#!/usr/bin/env bash
#
# status.sh - Show current agent config installation status
#
# Assumes lib/common.sh has been sourced.
# Assumes SCRIPT_DIR is set by the caller.

cmd_status() {
    echo ""
    echo -e "${BOLD}Agent Config Status${RESET}"
    echo "────────────────────────────────────────"
    echo ""

    # Claude Code
    info "Claude Code (~/.claude/)"
    check_file "$HOME/.claude/CLAUDE.md"
    check_file "$HOME/.claude/settings.json"
    for cmd_file in "$SCRIPT_DIR"/dot_claude/commands/*.md; do
        [[ -f "$cmd_file" ]] || continue
        local name
        name=$(basename "$cmd_file")
        check_file "$HOME/.claude/commands/$name"
    done
    echo ""

    # Codex
    info "Codex (~/.codex/)"
    check_file "$HOME/.codex/config.toml"
    check_file "$HOME/.codex/AGENTS.md"
    for prompt_file in "$SCRIPT_DIR"/dot_codex/prompts/*.md; do
        [[ -f "$prompt_file" ]] || continue
        local name
        name=$(basename "$prompt_file")
        check_file "$HOME/.codex/prompts/$name"
    done
    echo ""

    # OpenCode
    info "OpenCode (~/.config/opencode/)"
    check_file "$HOME/.config/opencode/opencode.json"
    check_file "$HOME/.config/opencode/AGENTS.md"
    echo ""

    # Gemini CLI
    info "Gemini CLI (~/.gemini/)"
    check_file "$HOME/.gemini/settings.json"
    check_file "$HOME/.gemini/GEMINI.md"
    echo ""

    # MCP servers
    info "MCP Servers"
    if has_cmd claude; then
        claude mcp list 2>/dev/null || warn "  Could not list MCP servers"
    else
        warn "  claude CLI not found"
    fi
    echo ""
}
