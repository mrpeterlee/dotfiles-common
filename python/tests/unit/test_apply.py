"""Tests for `dots apply` — REMAINDER passthrough to `chezmoi apply`."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from acap_dotfiles.cli import main


def test_apply_invokes_chezmoi_apply_with_source(
    fake_process: object, tmp_path: Path, monkeypatch: object
) -> None:
    monkeypatch.setenv("ACAP_DOTFILES_HOME", str(tmp_path))  # type: ignore[attr-defined]
    fake_process.register(  # type: ignore[attr-defined]
        [
            "/usr/bin/chezmoi",
            "--no-tty",
            "--no-pager",
            "--color=off",
            "--progress=false",
            "--source",
            str(tmp_path),
            "apply",
        ],
        stdout=b"",
    )
    with patch(
        "acap_dotfiles.commands.apply.discover_binary",
        return_value=Path("/usr/bin/chezmoi"),
    ):
        result = CliRunner().invoke(main, ["apply"])
    assert result.exit_code == 0


def test_apply_dry_run_propagates(
    fake_process: object, tmp_path: Path, monkeypatch: object
) -> None:
    monkeypatch.setenv("ACAP_DOTFILES_HOME", str(tmp_path))  # type: ignore[attr-defined]
    fake_process.register(  # type: ignore[attr-defined]
        [
            "/usr/bin/chezmoi",
            "--no-tty",
            "--no-pager",
            "--color=off",
            "--progress=false",
            "--source",
            str(tmp_path),
            "apply",
            "--dry-run",
        ],
        stdout=b"",
    )
    with patch(
        "acap_dotfiles.commands.apply.discover_binary",
        return_value=Path("/usr/bin/chezmoi"),
    ):
        result = CliRunner().invoke(main, ["--dry-run", "apply"])
    assert result.exit_code == 0


def test_apply_forwards_extra_args_verbatim(
    fake_process: object, tmp_path: Path, monkeypatch: object
) -> None:
    monkeypatch.setenv("ACAP_DOTFILES_HOME", str(tmp_path))  # type: ignore[attr-defined]
    fake_process.register(  # type: ignore[attr-defined]
        [
            "/usr/bin/chezmoi",
            "--no-tty",
            "--no-pager",
            "--color=off",
            "--progress=false",
            "--source",
            str(tmp_path),
            "apply",
            "--include=executable",
            "~/.local/bin",
        ],
        stdout=b"",
    )
    with patch(
        "acap_dotfiles.commands.apply.discover_binary",
        return_value=Path("/usr/bin/chezmoi"),
    ):
        result = CliRunner().invoke(main, ["apply", "--", "--include=executable", "~/.local/bin"])
    assert result.exit_code == 0


def test_apply_propagates_chezmoi_nonzero_exit(
    fake_process: object, tmp_path: Path, monkeypatch: object
) -> None:
    monkeypatch.setenv("ACAP_DOTFILES_HOME", str(tmp_path))  # type: ignore[attr-defined]
    fake_process.register(  # type: ignore[attr-defined]
        [
            "/usr/bin/chezmoi",
            "--no-tty",
            "--no-pager",
            "--color=off",
            "--progress=false",
            "--source",
            str(tmp_path),
            "apply",
        ],
        returncode=1,
        stderr=b"chezmoi: template error\n",
    )
    with patch(
        "acap_dotfiles.commands.apply.discover_binary",
        return_value=Path("/usr/bin/chezmoi"),
    ):
        result = CliRunner().invoke(main, ["apply"])
    assert result.exit_code != 0
