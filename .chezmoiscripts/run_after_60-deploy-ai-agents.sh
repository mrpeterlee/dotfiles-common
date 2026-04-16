#!/usr/bin/env bash
set -euo pipefail

echo "==> Deploying AI agent configurations..."

# User-level agents
if [[ -d "$HOME/.agents" ]]; then
    if [[ -x "$HOME/.agents/cli" ]]; then
        echo "  Running ~/.agents/cli apply..."
        if ! "$HOME/.agents/cli" apply; then
            echo "  ⚠ Skipping user agents: ~/.agents/cli apply failed (cli may be outdated; try 'cd ~/.agents && git pull')"
        fi
    else
        echo "  ⚠ Skipping user agents: ~/.agents exists but cli is not executable"
    fi
else
    echo "  ⊘ Skipping user agents: ~/.agents directory does not exist (clone https://github.com/... to enable)"
fi

# Org-level agents
if [[ -x "$HOME/acap/.agents/cli" ]]; then
    echo "  Running ~/acap/.agents/cli install..."
    "$HOME/acap/.agents/cli" install
else
    echo "  Skipping org agents: ~/acap/.agents/cli not found"
fi

echo "==> AI agent configuration deployed."
