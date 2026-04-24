# General AI Assistant Rules

Rules that apply across all repositories.

## Keyboard Layout

This user uses **Graphite** layout (not QWERTY). Navigation in vim/tmux/etc:
```
y = left    h = down    a = up    e = right
j = end-of-word    l = append    ' = yank
```

## Secrets Management

**NEVER hardcode sensitive data in any repository.** All secrets are managed through 1Password and Bitwarden.

- Use `onepasswordRead` in chezmoi templates
- Use `op read` in shell scripts at runtime
- Use `.env` files that are `.gitignore`d for local dev
- Grep for sensitive patterns before committing:
  ```bash
  git diff --cached | grep -E "(password|secret|token|[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)"
  ```

### 1Password (`op`)

Service account tokens are always available via `OP_SERVICE_ACCOUNT_TOKEN` (sourced from `~/.config/op/env`).

- `op-use <vault-alias>` — switch active vault
- `op-with <vault-alias> <args>` — one-shot command with a specific vault
- `op-which` — show active vault

### Bitwarden (`bw`)

Server: `<your-bitwarden-server>` | User: `<your-bw-username>`

Bitwarden starts **locked** each session. To unlock during a Claude session:
```bash
bw-unlock    # Fetches master password from 1Password, unlocks, exports BW_SESSION
```

- `bw-unlock` — unlock vault (master password retrieved from `op://<vault>/<bitwarden-item>/password`)
- `bw-lock` — lock vault and clear session
- `bw-status` — check server/user/lock status
- After `bw-unlock`, use `bw` commands normally (e.g., `bw list items`, `bw get item <name>`)

## gstack

Use the `/browse` skill from gstack for **all web browsing**. NEVER use `mcp__claude-in-chrome__*` tools.

Available skills:
- `/office-hours` — YC Office Hours
- `/plan-ceo-review` — CEO/founder plan review
- `/plan-eng-review` — Engineering plan review
- `/plan-design-review` — Design plan review
- `/design-consultation` — Design system consultation
- `/design-shotgun` — Visual design exploration
- `/review` — PR review
- `/ship` — Ship workflow
- `/land-and-deploy` — Merge, deploy, and verify
- `/canary` — Post-deploy canary monitoring
- `/benchmark` — Performance regression detection
- `/browse` — Headless browser for QA and browsing
- `/connect-chrome` — Headed Chrome with side panel
- `/qa` — QA test and fix bugs
- `/qa-only` — QA test, report only (no fixes)
- `/design-review` — Design audit and fix loop
- `/setup-browser-cookies` — Import browser cookies
- `/setup-deploy` — Configure deployment settings
- `/retro` — Engineering retrospective
- `/investigate` — Systematic root-cause debugging
- `/document-release` — Post-ship documentation updates
- `/codex` — Multi-AI second opinion via Codex
- `/cso` — Security audit (OWASP + STRIDE)
- `/autoplan` — Auto-review pipeline (CEO, design, eng)
- `/careful` — Destructive command warnings
- `/freeze` — Restrict edits to a directory
- `/guard` — Full safety mode
- `/design-html` — Design to HTML
- `/plan-devex-review` — DevEx plan review
- `/devex-review` — DevEx review
- `/unfreeze` — Clear freeze boundary
- `/gstack-upgrade` — Upgrade gstack to latest
- `/learn` — Learn from examples
