"""dots doctor — preflight sanity checks. Prints PASS/WARN/FAIL per check."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import click

from acap_dotfiles.core.chezmoi import ChezmoiError, discover_binary
from acap_dotfiles.core.config import DotsConfig


def _has_op() -> bool:
    return shutil.which("op") is not None


def _git_remote_url(cwd: Path) -> str | None:
    if not (cwd / ".git").exists():
        return None
    try:
        out = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=str(cwd),
            text=True,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        return None
    return out.stdout.strip() or None


@click.command()
def doctor() -> None:
    """Preflight sanity checks for chezmoi + op + source dir + git remote."""
    cfg = DotsConfig()
    failed = False
    warned = False

    # 1. chezmoi binary
    try:
        binary = discover_binary()
        click.echo(f"  ✓ chezmoi found: {binary}")
    except ChezmoiError as e:
        click.echo(f"  ✗ {e}")
        failed = True

    # 2. chezmoi source dir
    if (cfg.home / ".chezmoi.toml.tmpl").is_file():
        click.echo(f"  ✓ chezmoi source dir: {cfg.home}")
    else:
        click.echo(f"  ✗ chezmoi source not found at {cfg.home} (no .chezmoi.toml.tmpl)")
        failed = True

    # 3. op (optional)
    if _has_op():
        click.echo("  ✓ 1Password CLI (op) installed")
    else:
        click.echo("  ! WARN: op not installed — OAuth sync features disabled")
        warned = True

    # 4. git remote sanity
    remote = _git_remote_url(cfg.home)
    if remote and "dotfiles-common" in remote:
        click.echo(f"  ✓ git remote: {remote}")
    elif remote:
        click.echo(f"  ! WARN: git remote does not look like dotfiles-common: {remote}")
        warned = True
    else:
        click.echo("  ! WARN: no git remote configured")
        warned = True

    if failed:
        click.echo("\nFAIL: 1+ critical check failed", err=True)
        sys.exit(2)
    if warned:
        click.echo("\nPASS with WARN")
    else:
        click.echo("\nall checks passed")
