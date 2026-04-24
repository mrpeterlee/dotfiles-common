# Dotfiles

Cross-platform infrastructure baseline dotfiles managed with [chezmoi](https://www.chezmoi.io/).

This repo is the **common, org-agnostic** base. Organizational content
(vault names, infra IPs, per-org hosts, project-specific shell aliases)
lives in **overlays** that stack on top at apply time. See
`docs/overlay-convention.md` for the layering model.

## Quick Start

### One-liner install (new machine)

```bash
# Install chezmoi and apply this repo
sh -c "$(curl -fsLS get.chezmoi.io)" -- init --apply MrPeterLee
```

At `chezmoi init` time, you will be prompted for:

- Your git email and name
- Host role (base-only, or a known overlay role)
- Whether this is a personal machine

### Using the CLI

```bash
# Clone to ~/.files and use the CLI
git clone https://github.com/MrPeterLee/dotfiles.git ~/.files
cd ~/.files

./cli restore              # Apply dotfiles + install prereqs
./cli restore --force      # Clean-slate reinstall
./cli backup               # Capture system changes into repo
./cli conda build          # Build conda environment
./cli status               # Show what's installed
./cli help                 # Full usage guide
```

The `dots` CLI (Python/Click, part of the umbrella dotfiles-unification
work) will eventually replace the bash `cli` wrapper and handle overlay
stacking natively. Until then, overlays are applied via their own
`chezmoi apply --source=<overlay-root>` invocation.

## What's Included (base)

| Category | Tools |
|----------|-------|
| **Shell** | zsh (zinit + powerlevel10k), bash |
| **Editor** | Neovim (AstroNvim v4 + Lazy.nvim) |
| **Terminal** | WezTerm, tmux + tmuxinator |
| **Git** | lazygit, git config with aliases |
| **File Manager** | yazi |
| **Utilities** | fzf, zoxide, bat, ripgrep |
| **AI Agents** | Claude Code (settings, commands, skills), Codex (config, prompts), OpenCode, MCP servers |

Org-specific content (project aliases, infisical/vault wrappers,
per-org tmuxinator sessions, per-org SSH config) lives in overlays,
not here.

## Platform Support

- **Linux**: Debian/Ubuntu (apt), Arch (pacman), Fedora (dnf)
- **macOS**: Homebrew
- **Windows**: WSL + native (GlazeWM, Windows Terminal)

## Keyboard Layout

This config uses the **Graphite** keyboard layout (not QWERTY).
Navigation keys are remapped consistently across all tools:

```
y = left    h = down    a = up    e = right
j = end-of-word    l = append    ' = yank
```

## Secrets Management

The base repo does **not** reference any specific 1Password vault.
Instead, overlay `.chezmoidata/overlay.yaml` defines a `vault:` key;
templates that need a secret read from `op://{{ .vault }}/...`.

See `docs/secrets-management.md` and `docs/overlay-convention.md`
for the full model.

### Without an overlay

If no overlay is applied, chezmoi uses placeholder values from
`.chezmoidata.yaml` and no `onepasswordRead` calls fire. You can
also create a local secrets file for machine-specific exports:

```bash
touch ~/.config/zsh/.secrets.local.zsh
chmod 600 ~/.config/zsh/.secrets.local.zsh
# Add: export API_KEY="your-key"
```

## Common Commands

```bash
# See what would change
chezmoi diff

# Apply changes
chezmoi apply

# Edit a managed file
chezmoi edit ~/.zshrc

# Add a new file to chezmoi
chezmoi add ~/.config/some/file

# Update from remote
chezmoi update

# Re-run scripts (force refresh externals)
chezmoi apply --refresh-externals

# Re-initialize (refresh secrets)
chezmoi init --force
```

## Directory Structure

```
~/.local/share/chezmoi/
├── .chezmoi.toml.tmpl      # Machine config + prompt data
├── .chezmoidata.yaml       # Default/placeholder values
├── .chezmoiignore          # Platform exclusions
├── .chezmoiexternal.toml   # External deps (TPM, zinit, fzf)
├── .chezmoiscripts/        # Installation scripts
├── dot_config/             # ~/.config/* files (incl. opencode/)
├── dot_claude/             # ~/.claude/ — Claude Code config + skills + commands
├── dot_codex/              # ~/.codex/ — Codex CLI config + prompts
├── private_dot_local/      # ~/.local/* files
├── dot_*                   # Home directory dotfiles
├── mcp/servers.json        # MCP servers (registered via chezmoi onchange)
├── tests/                  # Hygiene + render-matrix CI gates
└── docs/                   # Convention docs (overlay, secrets)
```

## Adding New Config

1. `chezmoi add ~/.config/app/config.toml` — capture the file
2. Rename to `.tmpl` if templating is needed
3. If the file contains org-specific values, the file probably
   belongs in an **overlay**, not in `.files` — see
   `docs/overlay-convention.md`

## Hygiene gate

`tests/hygiene/test_no_org_plaintext.sh` scans the repo for banned
organizational-plaintext patterns (specific vault names, infra IPs,
org-specific email domains, etc.). CI runs this on every PR. Offending
content belongs in overlays.

See `docs/secrets-management.md` for the detailed secrets guide,
`docs/overlay-convention.md` for the overlay layering model.
