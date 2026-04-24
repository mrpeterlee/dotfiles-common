"""Tests for `core/git.py` — narrow git wrapper.

Uses real `git init` in tmp_path (isolated and non-interactive).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from acap_dotfiles.core.git import diff_name_only, remote_url


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
