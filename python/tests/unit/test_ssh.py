from pathlib import Path

import pytest
from click.testing import CliRunner

from acap_dotfiles.cli import main


def _seed_inventory(inv: Path) -> None:
    inv.mkdir(parents=True, exist_ok=True)
    (inv / "alpha.yaml").write_text("name: alpha\naddr: 10.0.0.1\nuser: peter\nrole: acap\n")
    (inv / "beta.yaml").write_text("name: beta\naddr: 10.0.0.2\nport: 2222\nrole: personal\n")


def test_ssh_render_uses_default_inventory_under_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ACAP_DOTFILES_HOME", str(tmp_path))
    _seed_inventory(tmp_path / "inventory" / "hosts")
    result = CliRunner().invoke(main, ["ssh", "render"])
    assert result.exit_code == 0, result.output
    assert "Host alpha" in result.stdout
    assert "Host beta" in result.stdout
    assert "Port 2222" in result.stdout


def test_ssh_render_with_custom_inventory_dir(tmp_path: Path) -> None:
    inv = tmp_path / "custom-inv"
    _seed_inventory(inv)
    result = CliRunner().invoke(main, ["ssh", "render", "--inventory", str(inv)])
    assert result.exit_code == 0, result.output
    assert "Host alpha" in result.stdout
    assert "    HostName 10.0.0.2" in result.stdout


def test_ssh_render_writes_to_out_file(tmp_path: Path) -> None:
    inv = tmp_path / "inv"
    _seed_inventory(inv)
    out = tmp_path / "build" / "ssh.conf"
    result = CliRunner().invoke(main, ["ssh", "render", "--inventory", str(inv), "--out", str(out)])
    assert result.exit_code == 0, result.output
    assert out.is_file()
    body = out.read_text()
    assert "Host alpha" in body
    assert "Host beta" in body
    assert "wrote 2 hosts" in result.stdout


def test_ssh_render_role_filter_excludes_other_roles(tmp_path: Path) -> None:
    inv = tmp_path / "inv"
    _seed_inventory(inv)
    result = CliRunner().invoke(main, ["ssh", "render", "--inventory", str(inv), "--role", "acap"])
    assert result.exit_code == 0, result.output
    assert "Host alpha" in result.stdout
    assert "Host beta" not in result.stdout
