"""dots release cut {patch|minor|major|pre} — bump __version__, commit, tag."""

from __future__ import annotations

import re
import subprocess  # ALLOWED (added to hygiene allow-list in test_no_direct_subprocess.py)
import sys

import click

from acap_dotfiles.core.config import DotsConfig

VERSION_RE = re.compile(r'^__version__ = "(\d+)\.(\d+)\.(\d+)(?:-rc\.(\d+))?"$', re.MULTILINE)
# Match the static `version = "..."` line under [project] in pyproject.toml.
# Anchored to start-of-line and the literal `version =` to avoid colliding with
# `requires-python` / dep version specifiers further down the file.
PYPROJECT_VERSION_RE = re.compile(r'^version = "[^"]+"$', re.MULTILINE)


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
    """Release-management helpers (semver bump + tag).

    Owns the `__version__` string in `python/src/acap_dotfiles/__init__.py`,
    the static `version = "..."` line in `python/pyproject.toml`, and the
    derived `python/uv.lock`. Wired into the `acap-dotfiles-cli` PyPI release
    flow.
    """


@release.command()
@click.argument("level", type=click.Choice(["patch", "minor", "major", "pre"]))
def cut(level: str) -> None:
    """Bump version (patch|minor|major|pre), commit, and tag `v<version>`.

    Refuses to run on a dirty working tree. Writes the new version to both
    `__init__.py` and `pyproject.toml`, re-locks `uv.lock` (best-effort), then
    `git commit -m "chore(release): bump to <v>"` + `git tag -a v<v>`. Push
    is left manual: `git push && git push --tags`.
    """
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

    # Also bump pyproject.toml's static `version = "..."` line so wheel
    # metadata + `dots --version` match the tagged release. Codex P2 r1: the
    # T14 "release cut" originally only touched __init__.py, leaving the build
    # backend reading the stale 0.1.0 pin out of pyproject.toml.
    pyproject_toml = cfg.home / "python" / "pyproject.toml"
    uv_lock = cfg.home / "python" / "uv.lock"
    add_paths: list[str] = [str(init_py)]
    if pyproject_toml.is_file():
        py_text = pyproject_toml.read_text()
        new_py_text, n = PYPROJECT_VERSION_RE.subn(f'version = "{new}"', py_text, count=1)
        if n != 1:
            click.echo(
                f'could not locate `version = "..."` line in {pyproject_toml}',
                err=True,
            )
            sys.exit(2)
        pyproject_toml.write_text(new_py_text)
        add_paths.append(str(pyproject_toml))
        # Re-lock so uv.lock records the new editable version. Best-effort:
        # some test/dev environments don't have the `uv` binary on PATH; skip
        # the add in that case rather than fail the cut.
        lock_rc = subprocess.run(
            ["uv", "lock"],
            cwd=str(cfg.home / "python"),
            check=False,
            capture_output=True,
            text=True,
        )
        if lock_rc.returncode == 0 and uv_lock.is_file():
            add_paths.append(str(uv_lock))
        elif lock_rc.returncode != 0:
            click.echo(
                f"warning: `uv lock` failed (rc={lock_rc.returncode}); "
                f"uv.lock not staged. stderr: {lock_rc.stderr.strip()}",
                err=True,
            )

    subprocess.run(["git", "add", *add_paths], cwd=str(cfg.home), check=True)
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
