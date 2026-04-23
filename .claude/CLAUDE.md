# Dotfiles Repository (~/.files)

This is the **common, org-agnostic baseline** of a chezmoi-managed
dotfiles system. Per-org content lives in overlays that stack on
top of this repo at apply time.

- Cross-platform support (Linux, macOS, Windows/WSL)
- chezmoi templates for machine-specific configuration
- Graphite keyboard layout (not QWERTY)
- Overlay layering for organizational content (see
  `docs/overlay-convention.md`)

## Verify Before Returning

**Before returning any result to the user, CLAUDE MUST run and verify
that the changes complete successfully and the outputs match
expectations.** This means:
- Run the relevant commands (`chezmoi apply`, `chezmoi diff`, shell
  source, etc.) after making changes
- Inspect the actual output files to confirm they rendered correctly
- Confirm environment variables are set, configs are valid, and no
  errors occurred
- If verification fails, fix the issue and re-verify before responding
- Never assume a change works -- prove it

## Overlay Model (Critical)

This repo is **org-agnostic**. It contains no vault names, no infra
IPs, no org-specific email domains, no project-specific aliases.
That content lives in **overlays** -- separate chezmoi source-state
trees under `<org-repo>/dotfiles-overlay/` -- that are applied *after*
this base repo.

An overlay's `.chezmoidata/overlay.yaml` defines:

- `vault:` -- the 1Password vault name the overlay consumes
- `infra:` -- org-specific infra values (AWS IDs, VPN hosts, etc.)

Templates in the base repo MUST NOT reference `.vault` or org-specific
values. If a template needs to call `onepasswordRead`, it belongs in
an overlay, not in `.files`.

The `dots` CLI (Python/Click, part of the umbrella dotfiles-unification
work) applies overlays sequentially in a deterministic order driven
by the host's `host-role`. A per-host manifest tracks provenance so
files that move out of an overlay get cleaned up on the next apply.

See `docs/overlay-convention.md` for the full model.

## Hygiene Gate

`tests/hygiene/test_no_org_plaintext.sh` scans the repo on every PR
for banned organizational-plaintext patterns -- specific vault names,
infra IPs, org email domains, bastion hostnames, etc. If you find
yourself wanting to commit any of those to this repo, the content
belongs in an overlay.

When adding content here, ask: **"Would this work identically for
an unrelated org or personal use?"** If no, it belongs in an overlay.

## Secrets Management

**NEVER hardcode sensitive data in this repository.**

Base templates treat secrets abstractly -- they reference `.vault`
(supplied by an overlay) and never hardcode a vault name. Reading
the actual secrets is the overlay's responsibility.

In an overlay template (NOT in base `.files`):

```go
{{- $value := onepasswordRead (printf "op://%s/Infrastructure/field_name" .vault) -}}
```

In shell scripts at runtime, use the `op` CLI with the active service
account -- overlay-provided wrappers (like `op-use`, `op-with`) switch
vaults. Those wrappers ship from their respective overlays, not from
this base.

### Without an overlay

If no overlay is applied, chezmoi uses placeholder values from
`.chezmoidata.yaml` and no `onepasswordRead` calls fire. This lets
the base repo apply cleanly on a fresh machine with no org context.

### Overlay-side naming conventions

When authoring templates inside an overlay, prefer these conventions
for `infra.*` keys so overlays interoperate:

| Type | Convention | Example |
|------|------------|---------|
| Hostnames | `snake_case` with `_host` suffix | `vpn_host`, `db_host` |
| Ports | `snake_case` with `_port` suffix | `vpn_port`, `api_port` |
| URLs | `snake_case` with `_url` suffix | `vault_url`, `api_url` |
| AWS IDs | `aws_` prefix | `aws_account_id`, `aws_route53_zone_id` |
| IPs | `_ip` suffix | `internal_ip`, `gateway_ip` |
| Credentials | Use `onepasswordRead` at render time; don't persist in chezmoi data |

## File Conventions

### Chezmoi Naming

| Prefix/Suffix | Meaning |
|---------------|---------|
| `dot_` | File starts with `.` (e.g., `dot_zshrc` -> `.zshrc`) |
| `private_` | File has restricted permissions (600) |
| `executable_` | File is executable (755) |
| `.tmpl` | File is a Go template |
| `run_once_` | Script runs once per machine |
| `run_` | Script runs on every apply |

### Template Files

Files ending in `.tmpl` are processed by chezmoi. Common patterns:

```go
// Conditional blocks
{{ if eq .chezmoi.os "darwin" }}
# macOS specific
{{ else if eq .chezmoi.os "linux" }}
# Linux specific
{{ end }}

// Overlay-supplied values (only valid in overlay templates)
ssh -p {{ .infra.vpn_port }} user@{{ .infra.vpn_host }}

// String operations
{{ .infra.base_domain | upper }}
```

## Common Tasks

### Adding a New Config File

```bash
# Add existing file to chezmoi
chezmoi add ~/.config/app/config.toml

# If it needs templating, rename it
mv dot_config/app/config.toml dot_config/app/config.toml.tmpl
```

If the file contains org-specific values, it belongs in an **overlay**
source-state tree, not in this base repo.

### Testing Templates

```bash
# Test template rendering
chezmoi execute-template '{{ .chezmoi.os }}'

# Preview what would be written
chezmoi diff

# Apply changes
chezmoi apply

# Dry-run into a throwaway destination
chezmoi apply --dry-run --source=. --destination=/tmp/render-test
```

### Refreshing prompts / data

```bash
chezmoi init --force
chezmoi apply
```

## Security Guidelines

1. **Never commit real values** -- base templates stay abstract;
   overlays supply the vault name via `.vault`
2. **Check before committing** -- run `git diff` and look for IPs,
   passwords, tokens, org-specific hostnames
3. **Use `.chezmoidata.yaml` for defaults** -- safe placeholder
   values only
4. **The hygiene gate is authoritative** --
   `tests/hygiene/test_no_org_plaintext.sh` enumerates the patterns
   that must not appear in base. CI runs this on every PR. Run it
   locally before pushing:
   ```bash
   ./tests/hygiene/test_no_org_plaintext.sh
   ```
5. **Grep for sensitive patterns** before pushing:
   ```bash
   git diff --cached | grep -E '(password|secret|token|[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)'
   ```

## Useful Commands

```bash
# CLI wrapper (base)
./cli backup|restore|apply|update|conda|status|help

# Chezmoi operations
chezmoi diff              # Preview changes
chezmoi apply             # Apply changes
chezmoi edit ~/.zshrc     # Edit managed file
chezmoi data              # Show all template data
chezmoi doctor            # Diagnose issues

# Hygiene / CI gates
./tests/hygiene/test_no_org_plaintext.sh     # banned-pattern scan
```

Overlay-provided commands (`op-use`, `op-with`, project-specific
wrappers) come from whichever overlay the host applies, not from
this base.

## Windows Environment Model

Two environments, one repo:

| Environment | Purpose | Tools |
|-------------|---------|-------|
| **cmd/PowerShell** | Minimal Claude Code host | **winget:** 1Password CLI, ripgrep, bat, zoxide, eza. **conda:** lazygit. **system:** git, chezmoi. |
| **WSL** | Full dev environment | Standard Linux -- run `cli restore` inside WSL. Gets conda env, zsh, tmux, neovim, all terminal utilities. |

The Windows side intentionally has no Neovim, Oh My Posh, fzf, fd,
or delta. All dev tooling lives in WSL. Do not add dev tools to the
Windows package list or PowerShell profile.

## Conda Environment Management

The `cli conda` command manages a blue-green conda environment at
`/opt/conda/envs/`. This is a shared development environment (`prod`)
containing Python, Node.js, Rust, and common dev dependencies.

### Architecture

```
/opt/conda/                              # miniconda base (system-wide)
/opt/conda/envs/
  prod-20260203-120000/                  # timestamped actual env
  prod-20260210-040000/                  # newer env
  prod -> prod-20260210-040000           # symlink (atomic swap)
  .prod-previous                         # records prior target for rollback
```

Shell activation: `conda activate /opt/conda/envs/prod` (in each
user's `.bashrc`). The symlink lets builds complete and validate
before activation takes effect. The env is **shared across all
users** on a host -- there is one `prod` symlink, not per-user.

### Commands

| Command | Purpose |
|---------|---------|
| `cli conda build` | Create a new timestamped env, validate it, atomically swap the `prod` symlink, clean up envs older than 30 days |
| `cli conda status` | Show current `prod` target, Python/Node/uv versions, list all available envs |
| `cli conda rollback` | Revert `prod` symlink to the previously recorded env |
| `cli conda nuke` | Remove **all** timestamped envs and the `prod` symlink, then rebuild from scratch |
| `cli conda install-timer` | Install a systemd user timer for weekly auto-rebuild (Sun 04:00) |

### What gets installed

The build pipeline runs in this order:

1. **Conda packages** (`env/config/conda-packages.txt`) --
   `conda create -p <prefix> -c conda-forge --channel-priority strict`.
   Core runtime: `python=3.11`, `nodejs`, `rust`, `uv`. Terminal
   utilities: `bat`, `ripgrep`, `fzf`, `zoxide`, `git-delta`, `eza`,
   `lazygit`, `tmux`, `neovim`.

2. **Pip packages** (`env/config/pip-packages.txt`) --
   `uv pip install --python <prefix>/bin/python`.

3. **NPM tools** (`env/config/npm-tools.txt`) -- `npm install -g`
   within the env.

4. **Standalone CLI binaries** (`env/lib/cli-tools.sh`) -- downloaded
   into `<prefix>/bin/`: `gh`, `kubectl`, `argocd`, `helm`, `yazi`,
   `sesh`, `twm`, `oh-my-posh`.

5. **System-level tools** -- installed outside the env, available on
   system PATH: `op` (1Password CLI), `claude` (Claude Code).

Org-specific pip indexes or private channels are layered in via
overlay scripts, not by this base repo.

### Adding or removing packages

- **Conda**: edit `env/config/conda-packages.txt`
- **Pip**: edit `env/config/pip-packages.txt`
- **NPM**: edit `env/config/npm-tools.txt`
- **Standalone binary**: add an `_install_<name>` function to
  `env/lib/cli-tools.sh` and call it from `install_cli_tools`

After editing, run `cli conda build` to create a fresh env with the
changes. The previous env remains available for rollback.

### Cleanup policy

After every successful build, `_env_cleanup` (in `cli`) removes
timestamped env directories older than 30 days. The current `prod`
target and the previous env (for rollback) are always preserved
regardless of age.

### Validation

`env/lib/validate.sh` checks:
- Python is 3.11.x
- Critical imports: `pandas`, `numpy`, `scipy`, `sqlalchemy`, `loguru`
- `uv`, `node` binaries present
- NPM tools present
- Terminal utilities present (`bat`, `rg`, `fzf`, `zoxide`, `delta`,
  `eza`, `lazygit`, `tmux`, `nvim`)
- Standalone CLI tools present (`gh`, `kubectl`, `argocd`, `helm`,
  `yazi`, `sesh`, `twm`, `oh-my-posh`)
- `op` available on system PATH

If validation fails, the new env is deleted and the `prod` symlink
is **not** swapped.

### Multi-host deployment

The env is shared by all users on a given host. `/opt` must be owned
by the primary operator account.

To deploy to a remote host:

```bash
# 1. Sync dotfiles to remote (overlay repos sync separately)
rsync -avz --delete --exclude='.git' ~/.files/ <remote>:~/.files/

# 2. Run deploy (installs miniconda if missing, builds env)
ssh <remote> 'export CONDA_DEFAULT_ENV="" CONDA_PREFIX="" CONDA_SHLVL=0 \
  PATH="/opt/conda/bin:$PATH" && bash ~/.files/env/deploy-host.sh'

# 3. Set up user bashrc files (requires sudo)
ssh <remote> 'sudo bash ~/.files/env/setup-bashrc.sh'
```

`deploy-host.sh` is safe to re-run: it skips miniconda install if
`/opt/conda` already exists. `setup-bashrc.sh` is idempotent.

## AI Agent Configs

Agent configs (Claude Code, Codex, OpenClaw) have moved to `~/.agents`
(separate repo).

- `~/.agents/cli install` -- install all agent configs
- `~/.agents/cli snapshot` -- capture evolved workspace files
- The deploy script
  (`.chezmoiscripts/run_after_60-deploy-ai-agents.sh.tmpl`) triggers
  `~/.agents/cli install` automatically.

## Related Documentation

- `README.md` -- user-facing documentation
- `docs/overlay-convention.md` -- overlay layering model
- `docs/secrets-management.md` -- detailed secrets guide
- `.chezmoi.toml.tmpl` -- template configuration source
- `.chezmoidata.yaml` -- default values reference
