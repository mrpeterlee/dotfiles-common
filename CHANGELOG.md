# Changelog

All notable changes to `dotfiles-common` are recorded here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and (for the `python/` package) version numbers follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Python `dots` CLI replacing bash `cli` (P3 of dotfiles-unification umbrella).
  - 11 verbs: `apply`, `update`, `status`, `doctor`, `backup`, `restore`,
    `ssh render`, `host role show|set`, `manifest show`, `release cut`,
    `migrate-from-legacy`.
  - Cross-platform (Linux / macOS / Windows; Python 3.11+).
  - Plugin extension via PEP 621 entry points (`dots.commands` group).
  - Lazy command loading — top-level `dots --help` does not import every verb.
  - `--dry-run` honored by all mutating chezmoi verbs.
  - Honors `NO_COLOR` env var (https://no-color.org).

### Changed

- `~/.files/cli` and `~/.files/cli.ps1` are now thin shims that exec `dots`
  for the migrated verbs. `cli conda` and `cli agents` continue to work
  unchanged via `lib/cli-legacy.{sh,ps1}`.

### Deprecated

- Direct invocation of `~/.files/cli apply|update|status|backup|restore` —
  use `dots` instead. The shim emits one warning per call.

### Migration

Run `dots migrate-from-legacy` once to acknowledge the migration banner. It
prints the verb-mapping (cli apply → dots apply, etc.), notes which
subcommands stay bash-only (`cli conda`, `cli agents`), and drops a marker
at `~/.config/dots/.migrated` so subsequent invocations are silent.
