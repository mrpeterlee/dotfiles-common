from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from acap_dotfiles.cli import main


def test_status_runs_chezmoi_managed_and_prints_count(fake_process: object) -> None:
    fake_process.register(  # type: ignore[attr-defined]
        [
            "/usr/bin/chezmoi",
            "--no-tty",
            "--no-pager",
            "--color=off",
            "--progress=false",
            "managed",
            "--include=files",
        ],
        stdout=b"file1\nfile2\nfile3\n",
    )
    with patch(
        "acap_dotfiles.commands.status.discover_binary",
        return_value=Path("/usr/bin/chezmoi"),
    ):
        result = CliRunner().invoke(main, ["status"])
    assert result.exit_code == 0
    assert "3" in result.stdout  # chezmoi-managed file count
    assert "chezmoi" in result.stdout.lower()


def test_status_handles_chezmoi_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    from acap_dotfiles.core.chezmoi import ChezmoiError

    with patch(
        "acap_dotfiles.commands.status.discover_binary",
        side_effect=ChezmoiError("chezmoi binary not found"),
    ):
        result = CliRunner().invoke(main, ["status"])
    assert result.exit_code != 0
    assert "chezmoi binary not found" in result.stderr
