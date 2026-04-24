"""Thin subprocess wrapper around the chezmoi CLI.

Per `core/chezmoi.py` design notes:
  - Always pass --no-tty --no-pager --color=off --progress=false (deterministic output)
  - Sync subprocess.run for read-only verbs and short writes
  - Streaming Popen for `apply`, `update`, `init` (provided in stream() — see below)
  - Module-level _MUTATING_VERBS frozenset gates --dry-run injection
  - Binary discovery: $DOTS_CHEZMOI_BIN > shutil.which("chezmoi") > ~/.local/bin/chezmoi > ~/bin/chezmoi
  - Raise ChezmoiError(stderr.strip()) on rc != 0 unless check=False
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

# Verbs that mutate target state — receive --dry-run when wrapper is in dry-run mode.
_MUTATING_VERBS: frozenset[str] = frozenset(
    {
        "apply",
        "update",
        "init",
        "add",
        "re-add",
        "destroy",
        "forget",
        "edit",
        "chattr",
        "import",
        "secret-keyring-set",
        "state",
    }
)

# Canonical args we ALWAYS pass to chezmoi to make output deterministic.
_CANONICAL_ARGS: tuple[str, ...] = (
    "--no-tty",
    "--no-pager",
    "--color=off",
    "--progress=false",
)


def _contains_mutating_verb(args: Sequence[str]) -> bool:
    """Return True if any pre-`--` arg matches a known mutating chezmoi verb.

    Stops scanning at `--` so passthrough operands (e.g. `chezmoi git -- grep
    apply`) don't false-positive trigger --dry-run injection on otherwise
    read-only invocations.

    Conservative within the pre-`--` window: false positives (extra --dry-run
    on benign invocations like `-c apply.toml`) are harmless; false negatives
    (missing --dry-run on a mutating run) are not. We accept the false-positive
    rate to eliminate the class of "is this arg a verb or an operand?" parsing
    bugs that plagued the prior _first_non_option / _VALUE_TAKING_GLOBALS
    design (codex caught 3 P1s in 3 review rounds).
    """
    for a in args:
        if a == "--":
            return False
        if a in _MUTATING_VERBS:
            return True
    return False


class ChezmoiError(RuntimeError):
    """Raised when chezmoi exits non-zero (or the binary cannot be found)."""


@dataclass(frozen=True)
class ChezmoiResult:
    """Result of a single chezmoi invocation."""

    returncode: int
    stdout: str
    stderr: str
    args: tuple[str, ...]


def discover_binary() -> Path:
    """Resolve the chezmoi binary by env override, PATH, then standard install dirs.

    Search order: $DOTS_CHEZMOI_BIN > shutil.which("chezmoi") > ~/.local/bin/chezmoi
    > ~/bin/chezmoi (Windows: append .exe at every step).

    Raises ChezmoiError if no usable binary is found.
    """
    suffix = ".exe" if sys.platform == "win32" else ""
    env_override = os.environ.get("DOTS_CHEZMOI_BIN")
    if env_override:
        path = Path(env_override)
        if path.is_file():
            return path
    path_resolved = shutil.which(f"chezmoi{suffix}")
    if path_resolved:
        return Path(path_resolved)
    home = Path(os.environ.get("HOME", str(Path.home())))
    for candidate in (
        home / ".local" / "bin" / f"chezmoi{suffix}",
        home / "bin" / f"chezmoi{suffix}",
    ):
        # shutil.which() filters by executability; mirror that for fallbacks
        # so we don't return a non-executable file and fail later with
        # PermissionError. Env override stays is_file()-only — operator-controlled.
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    raise ChezmoiError(
        "chezmoi binary not found. Install with `curl -fsLS get.chezmoi.io | sh -b ~/.local/bin`."
    )


@dataclass
class Wrapper:
    """Stateful chezmoi wrapper. Construct once per dots invocation."""

    binary: Path
    dry_run: bool = False
    source: Path | None = None  # passed as --source if set

    def build_argv(self, args: Sequence[str]) -> list[str]:
        argv: list[str] = [str(self.binary), *_CANONICAL_ARGS]
        if self.source is not None:
            argv.extend(["--source", str(self.source)])
        argv.extend(args)
        if self.dry_run and _contains_mutating_verb(args) and "--dry-run" not in args:
            argv.append("--dry-run")
        return argv

    def run(
        self,
        args: Sequence[str],
        *,
        check: bool = True,
        timeout: float | None = 300.0,
        env: dict[str, str] | None = None,
        cwd: Path | None = None,
    ) -> ChezmoiResult:
        """Invoke chezmoi and capture stdout/stderr.

        Use this for short verbs (data, status, diff, doctor, managed, ignored).
        For long-running verbs (apply, update, init), prefer `stream()`.
        """
        argv = self.build_argv(args)
        completed = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, **(env or {})},
            cwd=str(cwd) if cwd else None,
            check=False,
        )
        result = ChezmoiResult(
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            args=tuple(argv),
        )
        if check and completed.returncode != 0:
            raise ChezmoiError(
                completed.stderr.strip()
                or f"chezmoi {' '.join(args)} exited {completed.returncode}"
            )
        return result
