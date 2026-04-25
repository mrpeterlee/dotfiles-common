"""Tests for `dots backup` — chezmoi re-add + git diff --name-only preview."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner
from tests.conftest import CHEZMOI_BIN, CHEZMOI_BIN_ARGV

from acap_dotfiles.cli import main


def _re_add_argv(tmp_path: Path) -> list[str]:
    return [
        CHEZMOI_BIN_ARGV,
        "--no-tty",
        "--no-pager",
        "--color=off",
        "--progress=false",
        "--source",
        str(tmp_path),
        "re-add",
    ]


def test_backup_runs_re_add_then_prints_changed_files(
    fake_process: object, tmp_path: Path, monkeypatch: object
) -> None:
    monkeypatch.setenv("ACAP_DOTFILES_HOME", str(tmp_path))  # type: ignore[attr-defined]
    fake_process.register(_re_add_argv(tmp_path), stdout=b"")  # type: ignore[attr-defined]
    with (
        patch(
            "acap_dotfiles.commands.backup.discover_binary",
            return_value=CHEZMOI_BIN,
        ),
        patch(
            "acap_dotfiles.commands.backup.status_porcelain",
            return_value=["dot_claude/CLAUDE.md", "dot_zshrc"],
        ),
    ):
        result = CliRunner().invoke(main, ["backup"])
    assert result.exit_code == 0
    assert "Files updated (2)" in result.output
    assert "dot_claude/CLAUDE.md" in result.output
    assert "dot_zshrc" in result.output


def test_backup_no_changes_prints_no_op_message(
    fake_process: object, tmp_path: Path, monkeypatch: object
) -> None:
    monkeypatch.setenv("ACAP_DOTFILES_HOME", str(tmp_path))  # type: ignore[attr-defined]
    fake_process.register(_re_add_argv(tmp_path), stdout=b"")  # type: ignore[attr-defined]
    with (
        patch(
            "acap_dotfiles.commands.backup.discover_binary",
            return_value=CHEZMOI_BIN,
        ),
        patch(
            "acap_dotfiles.commands.backup.status_porcelain",
            return_value=[],
        ),
    ):
        result = CliRunner().invoke(main, ["backup"])
    assert result.exit_code == 0
    assert "No changes" in result.output


def test_backup_re_add_failure_exits_nonzero(
    fake_process: object, tmp_path: Path, monkeypatch: object
) -> None:
    monkeypatch.setenv("ACAP_DOTFILES_HOME", str(tmp_path))  # type: ignore[attr-defined]
    fake_process.register(  # type: ignore[attr-defined]
        _re_add_argv(tmp_path),
        returncode=1,
        stderr=b"chezmoi re-add: boom\n",
    )
    with patch(
        "acap_dotfiles.commands.backup.discover_binary",
        return_value=CHEZMOI_BIN,
    ):
        result = CliRunner().invoke(main, ["backup"])
    assert result.exit_code != 0
    assert "chezmoi re-add failed" in result.output


def test_backup_next_step_hint_uses_cfg_home(
    fake_process: object, tmp_path: Path, monkeypatch: object
) -> None:
    """The 'Next: cd ...' hint should interpolate cfg.home, not hardcode ~/.files.

    Regression test for the codex P3 finding on `dots backup`: when
    ACAP_DOTFILES_HOME points elsewhere, the printed cd path must follow.
    """
    custom_home = tmp_path / "custom-dots-home"
    custom_home.mkdir()
    monkeypatch.setenv("ACAP_DOTFILES_HOME", str(custom_home))  # type: ignore[attr-defined]
    fake_process.register(  # type: ignore[attr-defined]
        [
            CHEZMOI_BIN_ARGV,
            "--no-tty",
            "--no-pager",
            "--color=off",
            "--progress=false",
            "--source",
            str(custom_home),
            "re-add",
        ],
        stdout=b"",
    )
    with (
        patch(
            "acap_dotfiles.commands.backup.discover_binary",
            return_value=CHEZMOI_BIN,
        ),
        patch(
            "acap_dotfiles.commands.backup.status_porcelain",
            return_value=["dot_zshrc"],
        ),
    ):
        result = CliRunner().invoke(main, ["backup"])
    assert result.exit_code == 0
    assert f"cd {custom_home}" in result.output
    assert "cd ~/.files" not in result.output


def test_backup_git_diff_failure_exits_2(
    fake_process: object, tmp_path: Path, monkeypatch: object
) -> None:
    from acap_dotfiles.core.git import GitError

    monkeypatch.setenv("ACAP_DOTFILES_HOME", str(tmp_path))  # type: ignore[attr-defined]
    fake_process.register(_re_add_argv(tmp_path), stdout=b"")  # type: ignore[attr-defined]
    with (
        patch(
            "acap_dotfiles.commands.backup.discover_binary",
            return_value=CHEZMOI_BIN,
        ),
        patch(
            "acap_dotfiles.commands.backup.status_porcelain",
            side_effect=GitError("not a git repository"),
        ),
    ):
        result = CliRunner().invoke(main, ["backup"])
    assert result.exit_code == 2
    assert "git status failed" in result.output
