"""Tests for `dots migrate-from-legacy` — one-shot detection + warning."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from acap_dotfiles.cli import main


def test_migrate_first_run_with_legacy_on_path_prints_banner_and_writes_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    with patch(
        "acap_dotfiles.commands.migrate.shutil.which",
        return_value="/usr/local/bin/cli",
    ):
        result = CliRunner().invoke(main, ["migrate-from-legacy"])
    assert result.exit_code == 0, result.output
    assert "Migration from legacy bash cli" in result.output
    assert "/usr/local/bin/cli" in result.output
    assert "cli apply" in result.output and "dots apply" in result.output
    marker = tmp_path / ".config" / "dots" / ".migrated"
    assert marker.exists()


def test_migrate_already_migrated_marker_present_skips_banner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    marker = tmp_path / ".config" / "dots" / ".migrated"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.touch()
    with patch(
        "acap_dotfiles.commands.migrate.shutil.which",
        return_value="/usr/local/bin/cli",
    ):
        result = CliRunner().invoke(main, ["migrate-from-legacy"])
    assert result.exit_code == 0, result.output
    assert "already migrated" in result.output
    assert "Migration from legacy bash cli" not in result.output


def test_migrate_no_legacy_on_path_writes_marker_and_reports_clear(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    with patch(
        "acap_dotfiles.commands.migrate.shutil.which",
        return_value=None,
    ):
        result = CliRunner().invoke(main, ["migrate-from-legacy"])
    assert result.exit_code == 0, result.output
    assert "not detected" in result.output
    assert "Migration from legacy bash cli" not in result.output
    marker = tmp_path / ".config" / "dots" / ".migrated"
    assert marker.exists()
