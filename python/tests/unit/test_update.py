"""Tests for `dots update` — port of lib/update.sh phases 1-2."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from acap_dotfiles.cli import main


def test_update_runs_apply_then_refresh_externals(
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
    )
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
            "--refresh-externals",
        ],
    )
    with patch(
        "acap_dotfiles.commands.update.discover_binary",
        return_value=Path("/usr/bin/chezmoi"),
    ):
        result = CliRunner().invoke(main, ["update"])
    assert result.exit_code == 0


def test_update_apply_failure_aborts(
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
        stderr=b"err\n",
    )
    with patch(
        "acap_dotfiles.commands.update.discover_binary",
        return_value=Path("/usr/bin/chezmoi"),
    ):
        result = CliRunner().invoke(main, ["update"])
    assert result.exit_code != 0


def test_update_refresh_externals_failure_warns_but_succeeds(
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
    )
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
            "--refresh-externals",
        ],
        returncode=1,
        stderr=b"network err\n",
    )
    with patch(
        "acap_dotfiles.commands.update.discover_binary",
        return_value=Path("/usr/bin/chezmoi"),
    ):
        result = CliRunner().invoke(main, ["update"])
    assert result.exit_code == 0  # refresh-externals failure is best-effort
    assert "warn" in result.stderr.lower()
