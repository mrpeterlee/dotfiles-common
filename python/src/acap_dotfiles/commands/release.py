"""dots release cut {patch|minor|major|pre} — bump __version__, commit, tag."""

from __future__ import annotations

import re
import subprocess  # ALLOWED (added to hygiene allow-list in test_no_direct_subprocess.py)
import sys

import click

from acap_dotfiles.core.config import DotsConfig

VERSION_RE = re.compile(r'^__version__ = "(\d+)\.(\d+)\.(\d+)(?:-rc\.(\d+))?"$', re.MULTILINE)


def _bump(major: int, minor: int, patch: int, pre: int | None, level: str) -> str:
    if level == "major":
        return f"{major + 1}.0.0"
    if level == "minor":
        return f"{major}.{minor + 1}.0"
    if level == "patch":
        return f"{major}.{minor}.{patch + 1}"
    if level == "pre":
        if pre is None:
            return f"{major}.{minor}.{patch + 1}-rc.1"
        return f"{major}.{minor}.{patch}-rc.{pre + 1}"
    raise click.BadParameter(f"unknown level: {level}")


@click.group()
def release() -> None:
    """Release-management helpers."""


@release.command()
@click.argument("level", type=click.Choice(["patch", "minor", "major", "pre"]))
def cut(level: str) -> None:
    """Bump __version__, commit, and create annotated tag v<version>."""
    cfg = DotsConfig()
    init_py = cfg.home / "python" / "src" / "acap_dotfiles" / "__init__.py"
    if not init_py.is_file():
        click.echo(f"not found: {init_py}", err=True)
        sys.exit(2)
    text = init_py.read_text()
    m = VERSION_RE.search(text)
    if not m:
        click.echo("no __version__ line found", err=True)
        sys.exit(2)
    major, minor, patch = int(m.group(1)), int(m.group(2)), int(m.group(3))
    pre = int(m.group(4)) if m.group(4) else None

    # Refuse if working tree is dirty
    dirty = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(cfg.home),
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()
    if dirty:
        click.echo("working tree is dirty — commit or stash first", err=True)
        sys.exit(2)

    new = _bump(major, minor, patch, pre, level)
    init_py.write_text(VERSION_RE.sub(f'__version__ = "{new}"', text))

    subprocess.run(["git", "add", str(init_py)], cwd=str(cfg.home), check=True)
    subprocess.run(
        ["git", "commit", "-m", f"chore(release): bump to {new}"],
        cwd=str(cfg.home),
        check=True,
    )
    subprocess.run(
        ["git", "tag", "-a", f"v{new}", "-m", f"Release {new}"],
        cwd=str(cfg.home),
        check=True,
    )
    click.echo(f"released v{new}; push with: git push && git push --tags")
