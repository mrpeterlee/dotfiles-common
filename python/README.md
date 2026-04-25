# acap-dotfiles-cli — `dots`

Unified cross-platform Python CLI replacing the legacy bash `~/.files/cli` and
PowerShell `~/.files/cli.ps1`. Wraps chezmoi for apply/update/restore plus
inventory-as-code helpers, host-role management, manifest inspection, release
cuts, and a one-shot migration shim.

Runs on Linux, macOS, and Windows. Python 3.11+.

## Install

From a fresh checkout of `dotfiles-common`:

```bash
cd ~/.files/python
uv venv
uv pip install -e ".[dev]"
uv run dots --version
```

For end-users on existing hosts, the legacy entrypoints `~/.files/cli` and
`~/.files/cli.ps1` are now thin shims that exec `dots` for migrated verbs and
fall back to `lib/cli-legacy.{sh,ps1}` for `conda` / `agents`. No reinstall
needed — the shim emits one deprecation warning per call.

## Quickstart

```bash
dots doctor                       # preflight: chezmoi + op + git remote checks
dots apply                        # chezmoi apply (extra args after `--`)
dots update                       # apply + refresh externals
dots status                       # human-readable install report
dots backup                       # chezmoi re-add + git status preview
dots restore                      # chezmoi init + apply (fresh host bootstrap)
dots ssh render --role personal   # emit ~/.ssh/config block from inventory
dots host role show               # current host role (acap | tapai | personal)
dots host role set acap           # persist host role to ~/.config/dots/role.toml
dots manifest show --json         # print the chezmoi-managed manifest
dots release cut patch            # bump version + tag v<version>
dots migrate-from-legacy          # one-shot migration banner from bash cli
```

Global flags: `-v` / `-vv` / `-vvv` (verbosity), `--no-color` (also honors
`NO_COLOR`), `--dry-run` (forwarded to mutating chezmoi verbs).

## Verb reference

| Command                       | Description                                                                         |
|-------------------------------|-------------------------------------------------------------------------------------|
| `dots apply`                  | Apply dotfiles via `chezmoi apply`. Extra args after `--` forwarded.                |
| `dots update`                 | Apply, then refresh externals (best-effort).                                        |
| `dots status`                 | Probe chezmoi-managed file count + common tool install paths.                       |
| `dots doctor`                 | Preflight checks: chezmoi binary, source dir, op CLI, git remote.                   |
| `dots backup`                 | `chezmoi re-add` then `git status --porcelain` to preview commit.                   |
| `dots restore [--force]`      | `chezmoi init` + `apply` for fresh-host bootstrap. Auto-stubs config when non-TTY.  |
| `dots ssh render`             | Render inventory YAML → SSH config block. `--role`, `--out`, `--inventory`.         |
| `dots host role show`         | Print current host role (or `unset`).                                               |
| `dots host role set <value>`  | Persist host role (`acap` \| `tapai` \| `personal`) to `~/.config/dots/role.toml`. |
| `dots manifest show [--json]` | Print the chezmoi-managed manifest as `(role, path)` entries.                       |
| `dots release cut <level>`    | Bump version (`patch`\|`minor`\|`major`\|`pre`), commit, and tag `v<version>`.     |
| `dots migrate-from-legacy`    | One-shot migration banner from the legacy bash `cli`. Idempotent.                   |

## Project layout

```
python/
├── pyproject.toml                # PEP 621 metadata + entry points
├── noxfile.py                    # multi-Python test matrix (3.11/3.12/3.13)
├── README.md                     # this file
├── src/acap_dotfiles/
│   ├── __init__.py               # __version__
│   ├── cli.py                    # Click root + LazyGroup verb dispatch
│   ├── commands/                 # one module per verb (lazy-loaded)
│   │   ├── apply.py
│   │   ├── update.py
│   │   ├── status.py
│   │   ├── doctor.py
│   │   ├── backup.py
│   │   ├── restore.py
│   │   ├── ssh.py                # `dots ssh render`
│   │   ├── host.py               # `dots host role show|set`
│   │   ├── manifest.py           # `dots manifest show`
│   │   ├── release.py            # `dots release cut`
│   │   └── migrate.py            # `dots migrate-from-legacy`
│   ├── core/                     # pure-logic helpers (chezmoi wrapper, config,
│   │   │                         # git, inventory, manifest, role)
│   │   └── ...
│   └── io/                       # side-effecting helpers (exec, log)
│       └── ...
└── tests/
    ├── unit/                     # 88+ pytest unit tests (no chezmoi binary)
    └── integration/              # docker-based end-to-end (apply on real
                                  # chezmoi binary in a clean Linux container)
```

## Tests

```bash
uv run pytest tests/unit/ -q       # 88+ unit tests, ~0.5s
uv run pytest -m integration       # docker integration (chezmoi apply E2E)
uv run nox                         # full matrix (3.11 / 3.12 / 3.13)
```

CI runs the matrix on every push via `.github/workflows/dots-ci.yml`.

## Deprecation timeline

The bash `~/.files/cli` and PowerShell `~/.files/cli.ps1` are thin shims that
exec `dots` for the migrated verbs (`apply`, `update`, `status`, `backup`,
`restore`) and emit one deprecation warning per call. `cli conda` and
`cli agents` continue to delegate to `lib/cli-legacy.{sh,ps1}` unchanged —
those subcommands are not part of P3 scope.

| Phase            | When                              | What                                                     |
|------------------|-----------------------------------|----------------------------------------------------------|
| **Now (P3)**     | This release                      | Shim warns once per call. Both `cli` and `dots` work.    |
| **+1 release**   | Next minor bump (~1 month)        | Shim still works; warning becomes error-coloured.        |
| **+2 releases**  | One full release cycle after P3   | Migrated verbs removed from shim. `cli conda/agents` stay. |

Track the cutover in `~/.files/CHANGELOG.md`.

## Contributing

This package is part of the `dotfiles-common` repo and follows the ACap
engineering standards documented in `~/acap/CLAUDE.md`:

1. **TDD discipline.** Write failing tests first under `tests/unit/`, implement
   minimal code to pass, refactor. The repo target is 80%+ coverage; the unit
   suite must stay green (`uv run pytest tests/unit/ -q`) on every commit.
2. **Three-reviewer cycle.** Every PR goes through (a) self-review,
   (b) Claude code-reviewer agent, (c) Codex second opinion via
   `superpowers:codex-review`. Address CRITICAL + HIGH issues before merge.
3. **No direct `subprocess`.** Spawn external processes through
   `acap_dotfiles.io.exec` so they're streamable + timeout-bounded. The
   `tests/unit/test_no_direct_subprocess.py` hygiene test enforces this with
   a hand-curated allow-list.
4. **Pure logic in `core/`, side effects in `io/`.** Keeps unit tests fast and
   avoids touching the filesystem in module-level code.
5. **One verb per file under `commands/`.** Keep modules under ~150 lines;
   extract helpers to `core/` when shared.

For broader codebase rules (Decimal for money, UTC timestamps, parameterized
queries) see `~/acap/CLAUDE.md`. For the P3 plan + decomposition rationale,
see `docs/superpowers/plans/2026-04-24-dotfiles-unification-p3-dots-cli.md`
in the `astro-cap/acap` monorepo.
