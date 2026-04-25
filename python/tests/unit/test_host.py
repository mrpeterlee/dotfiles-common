from pathlib import Path

import pytest
from click.testing import CliRunner

from acap_dotfiles.cli import main


def test_host_role_show_unset(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    result = CliRunner().invoke(main, ["host", "role", "show"])
    assert result.exit_code == 0
    assert "unset" in result.stdout


def test_host_role_set_then_show(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    r = CliRunner().invoke(main, ["host", "role", "set", "acap"])
    assert r.exit_code == 0
    r2 = CliRunner().invoke(main, ["host", "role", "show"])
    assert r2.exit_code == 0
    assert "acap" in r2.stdout


def test_host_role_set_invalid_rejects(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    r = CliRunner().invoke(main, ["host", "role", "set", "bogus"])
    assert r.exit_code != 0
    assert "invalid role" in r.stderr
