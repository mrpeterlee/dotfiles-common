"""Tests for `dots release cut {patch|minor|major|pre}` — semver bump + tag."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from acap_dotfiles.cli import main


@pytest.fixture
def tmp_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a real git repo with a fake `python/src/acap_dotfiles/__init__.py`.

    The fixture also points DotsConfig.home at this temp repo via the
    ACAP_DOTFILES_HOME env var so the `release cut` command operates on it.
    """
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "tag.gpgsign", "false"], cwd=tmp_path, check=True)

    init_dir = tmp_path / "python" / "src" / "acap_dotfiles"
    init_dir.mkdir(parents=True)
    init_py = init_dir / "__init__.py"
    init_py.write_text('"""dotfiles."""\n\n__version__ = "0.1.0"\n')

    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=tmp_path, check=True)

    monkeypatch.setenv("ACAP_DOTFILES_HOME", str(tmp_path))
    return tmp_path


def _read_version(repo: Path) -> str:
    text = (repo / "python" / "src" / "acap_dotfiles" / "__init__.py").read_text()
    for line in text.splitlines():
        if line.startswith("__version__"):
            # __version__ = "X.Y.Z"  or  __version__ = "X.Y.Z-rc.N"
            return line.split('"')[1]
    raise AssertionError("no __version__ line")


def _tag_exists(repo: Path, tag: str) -> bool:
    res = subprocess.run(
        ["git", "tag", "--list", tag], cwd=repo, text=True, capture_output=True, check=True
    )
    return res.stdout.strip() == tag


def test_release_cut_patch_bumps_to_0_1_1(tmp_repo: Path) -> None:
    result = CliRunner().invoke(main, ["release", "cut", "patch"])
    assert result.exit_code == 0, result.output
    assert _read_version(tmp_repo) == "0.1.1"
    assert _tag_exists(tmp_repo, "v0.1.1")


def test_release_cut_minor_bumps_to_0_2_0(tmp_repo: Path) -> None:
    result = CliRunner().invoke(main, ["release", "cut", "minor"])
    assert result.exit_code == 0, result.output
    assert _read_version(tmp_repo) == "0.2.0"
    assert _tag_exists(tmp_repo, "v0.2.0")


def test_release_cut_major_bumps_to_1_0_0(tmp_repo: Path) -> None:
    result = CliRunner().invoke(main, ["release", "cut", "major"])
    assert result.exit_code == 0, result.output
    assert _read_version(tmp_repo) == "1.0.0"
    assert _tag_exists(tmp_repo, "v1.0.0")


def test_release_cut_pre_bumps_to_0_1_1_rc_1(tmp_repo: Path) -> None:
    result = CliRunner().invoke(main, ["release", "cut", "pre"])
    assert result.exit_code == 0, result.output
    assert _read_version(tmp_repo) == "0.1.1-rc.1"
    assert _tag_exists(tmp_repo, "v0.1.1-rc.1")


def test_release_cut_refuses_dirty_tree(tmp_repo: Path) -> None:
    # Make the tree dirty
    (tmp_repo / "scratch.txt").write_text("uncommitted")
    subprocess.run(["git", "add", "scratch.txt"], cwd=tmp_repo, check=True)

    result = CliRunner().invoke(main, ["release", "cut", "patch"])
    assert result.exit_code != 0
    assert "dirty" in result.output.lower()
    # Version unchanged, no tag
    assert _read_version(tmp_repo) == "0.1.0"
    assert not _tag_exists(tmp_repo, "v0.1.1")
