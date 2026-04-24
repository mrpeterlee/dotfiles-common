"""Tests for `core/git.py` — narrow git wrapper.

Uses real `git init` in tmp_path (isolated and non-interactive).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from acap_dotfiles.core.git import diff_name_only, remote_url, status_porcelain


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "a.txt").write_text("hi")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=tmp_path, check=True)
    return tmp_path


def test_diff_name_only_empty_when_no_changes(repo: Path) -> None:
    assert diff_name_only(repo) == []


def test_diff_name_only_lists_changed_files(repo: Path) -> None:
    (repo / "a.txt").write_text("changed")
    assert diff_name_only(repo) == ["a.txt"]


def test_remote_url_returns_none_for_no_remote(repo: Path) -> None:
    assert remote_url(repo) is None


def test_remote_url_after_setting(repo: Path) -> None:
    subprocess.run(["git", "remote", "add", "origin", "git@host:p/r.git"], cwd=repo, check=True)
    assert remote_url(repo) == "git@host:p/r.git"


def test_status_porcelain_includes_untracked_and_modified(repo: Path) -> None:
    """status_porcelain must surface untracked files (not just diffs vs HEAD).

    Regression test for the codex P2 finding on `dots backup`: chezmoi re-add
    can drop brand-new files into the source tree as untracked, and
    `git diff --name-only HEAD` would silently miss them.
    """
    # Modify a tracked file
    (repo / "a.txt").write_text("changed")
    # Add a new untracked file
    (repo / "untracked.txt").write_text("brand new")
    # And a nested untracked file under a new subdir (--untracked-files=all coverage)
    nested = repo / "nested"
    nested.mkdir()
    (nested / "deep.txt").write_text("deep")

    result = status_porcelain(repo)
    assert "a.txt" in result
    assert "untracked.txt" in result
    assert "nested/deep.txt" in result
    # diff_name_only by contrast misses the untracked entries
    diff_only = diff_name_only(repo)
    assert "untracked.txt" not in diff_only
    assert "nested/deep.txt" not in diff_only
