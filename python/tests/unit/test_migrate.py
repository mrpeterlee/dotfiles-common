"""Tests for `dots migrate-from-legacy` — one-shot detection + warning."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from acap_dotfiles.cli import main


def _patch_home(monkeypatch: pytest.MonkeyPatch, fake_home: Path) -> None:
    """Redirect ``Path.home()`` to ``fake_home`` regardless of OS.

    `Path.home()` on Linux honours `$HOME`; on Windows it reads
    `%USERPROFILE%` first. Setting only `HOME` leaves Windows pointing at
    the runner's real home, so a `.migrated` marker from a previous test
    leaks across cases. Patching `Path.home` directly is platform-portable.
    """
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setenv("USERPROFILE", str(fake_home))
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))


def test_migrate_first_run_with_legacy_on_path_prints_banner_and_writes_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_home(monkeypatch, tmp_path)
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
    _patch_home(monkeypatch, tmp_path)
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
    _patch_home(monkeypatch, tmp_path)
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
