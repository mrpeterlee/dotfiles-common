from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from acap_dotfiles.cli import main


def test_doctor_passes_when_all_checks_green(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ACAP_DOTFILES_HOME", str(tmp_path))
    (tmp_path / ".chezmoi.toml.tmpl").write_text("# valid")
    with (
        patch(
            "acap_dotfiles.commands.doctor.discover_binary",
            return_value=Path("/usr/bin/chezmoi"),
        ),
        patch("acap_dotfiles.commands.doctor._has_op", return_value=True),
        patch(
            "acap_dotfiles.commands.doctor._git_remote_url",
            return_value="git@github.com:MrPeterLee/dotfiles-common.git",
        ),
    ):
        result = CliRunner().invoke(main, ["doctor"])
    assert result.exit_code == 0
    assert "all checks passed" in result.stdout.lower()


def test_doctor_fails_on_missing_chezmoi_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ACAP_DOTFILES_HOME", str(tmp_path))
    # No .chezmoi.toml.tmpl
    with (
        patch(
            "acap_dotfiles.commands.doctor.discover_binary",
            return_value=Path("/usr/bin/chezmoi"),
        ),
        patch("acap_dotfiles.commands.doctor._has_op", return_value=True),
        patch(
            "acap_dotfiles.commands.doctor._git_remote_url",
            return_value="git@github.com:MrPeterLee/dotfiles-common.git",
        ),
    ):
        result = CliRunner().invoke(main, ["doctor"])
    assert result.exit_code != 0
    assert "chezmoi source" in result.stdout.lower()


def test_doctor_warns_when_op_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ACAP_DOTFILES_HOME", str(tmp_path))
    (tmp_path / ".chezmoi.toml.tmpl").write_text("")
    with (
        patch(
            "acap_dotfiles.commands.doctor.discover_binary",
            return_value=Path("/usr/bin/chezmoi"),
        ),
        patch("acap_dotfiles.commands.doctor._has_op", return_value=False),
        patch(
            "acap_dotfiles.commands.doctor._git_remote_url",
            return_value="git@github.com:MrPeterLee/dotfiles-common.git",
        ),
    ):
        result = CliRunner().invoke(main, ["doctor"])
    # WARN, not FAIL — op is optional
    assert result.exit_code == 0
    assert "warn" in result.stdout.lower()
    assert "op" in result.stdout.lower()
