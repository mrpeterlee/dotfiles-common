"""Narrow git wrapper. Exposes only the subcommands dots needs (diff, pull, tag, log)."""

from __future__ import annotations

import subprocess  # ALLOWED inside core/git.py (added to hygiene allow-list)
from pathlib import Path


class GitError(RuntimeError):
    """Raised when git exits non-zero."""


def diff_name_only(cwd: Path, ref: str = "HEAD") -> list[str]:
    """Return changed file paths (one per line) from `git diff --name-only <ref>`.

    Raises GitError on non-zero exit (e.g. not a git repo).
    """
    out = subprocess.run(
        ["git", "diff", "--name-only", ref],
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
    )
    if out.returncode != 0:
        raise GitError(out.stderr.strip() or "git diff failed")
    return [ln for ln in out.stdout.splitlines() if ln.strip()]


def remote_url(cwd: Path, name: str = "origin") -> str | None:
    """Return the URL of the named remote, or None if no such remote is configured."""
    out = subprocess.run(
        ["git", "remote", "get-url", name],
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
    )
    return out.stdout.strip() if out.returncode == 0 else None


def current_tag(cwd: Path) -> str | None:
    """Return the tag pointing at HEAD, or None if HEAD has no exact-match tag."""
    out = subprocess.run(
        ["git", "describe", "--exact-match", "--tags"],
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
    )
    return out.stdout.strip() if out.returncode == 0 else None
