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


def status_porcelain(cwd: Path) -> list[str]:
    """Return changed paths from `git status --porcelain --untracked-files=all`.

    Includes both tracked modifications (M, A, D, R, C, U) and untracked files
    (??). Each entry is the file path with the porcelain status prefix stripped
    (e.g. `dot_zshrc`, not ` M dot_zshrc`). Rename entries (`R  old -> new`)
    return the new path.

    Used by `dots backup` so brand-new files added by `chezmoi re-add` show up
    in the preview — `git diff --name-only HEAD` would silently miss them.

    Raises GitError on non-zero exit (e.g. not a git repo).
    """
    out = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
    )
    if out.returncode != 0:
        raise GitError(out.stderr.strip() or "git status failed")
    paths: list[str] = []
    for line in out.stdout.splitlines():
        if not line.strip():
            continue
        # Porcelain v1 format: 2-char status, space, path. Renames use ` -> `.
        path = line[3:] if len(line) > 3 else ""
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if path:
            paths.append(path)
    return paths


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
