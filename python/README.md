# acap-dotfiles-cli — `dots`

Unified cross-platform Python CLI replacing the legacy bash `~/.files/cli` and
PowerShell `cli.ps1`. Wraps chezmoi for apply/update/restore plus a few extras.

## Build

    uv venv && source .venv/bin/activate
    uv pip install -e ".[dev]"
    uv run dots --version

## Test

    uv run pytest                      # unit tests
    uv run pytest -m integration       # docker integration tests
    uv run nox                         # full matrix

## Project layout

See `docs/superpowers/plans/2026-04-24-dotfiles-unification-p3-dots-cli.md` in
the astro-cap/acap repo for the implementation plan + decomposition rationale.

## Deprecation of legacy `cli`

The bash `~/.files/cli` and PowerShell `~/.files/cli.ps1` are now thin shims that
exec `dots` and emit one warning. They will be removed one release cycle after
P3 lands; track the deprecation in `~/.files/CHANGELOG.md`.
