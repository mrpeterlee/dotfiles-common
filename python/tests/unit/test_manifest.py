import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from acap_dotfiles.cli import main
from acap_dotfiles.core.manifest import Manifest, load_manifest


def test_load_manifest_parses_yaml(tmp_path: Path) -> None:
    p = tmp_path / "manifest.yaml"
    p.write_text("version: 1\nentries:\n  - path: ~/.zshrc\n    role: common\n")
    m = load_manifest(p)
    assert isinstance(m, Manifest)
    assert m.version == 1
    assert len(m.entries) == 1
    assert m.entries[0].path == "~/.zshrc"


def test_manifest_show_emits_human_readable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    p = tmp_path / "manifest.yaml"
    p.write_text("version: 1\nentries:\n  - path: ~/.zshrc\n    role: common\n")
    monkeypatch.setenv("ACAP_DOTFILES_HOME", str(tmp_path))
    result = CliRunner().invoke(main, ["manifest", "show"])
    assert result.exit_code == 0
    assert "~/.zshrc" in result.stdout
    assert "common" in result.stdout


def test_manifest_show_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    p = tmp_path / "manifest.yaml"
    p.write_text("version: 1\nentries:\n  - path: ~/.zshrc\n    role: common\n")
    monkeypatch.setenv("ACAP_DOTFILES_HOME", str(tmp_path))
    result = CliRunner().invoke(main, ["manifest", "show", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["version"] == 1
    assert payload["entries"][0]["path"] == "~/.zshrc"


def test_manifest_show_missing_file_exits_nonzero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ACAP_DOTFILES_HOME", str(tmp_path))
    result = CliRunner().invoke(main, ["manifest", "show"])
    assert result.exit_code != 0
    assert "manifest.yaml not found" in result.stderr
