"""Tests for `dots restore` — chezmoi init + apply (pkg install stays bash for P3)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from acap_dotfiles.cli import main


def test_restore_with_tty_invokes_init_then_apply_without_force(
    fake_process: object, tmp_path: Path, monkeypatch: object
) -> None:
    """Bare `dots restore` with TTY → chezmoi init + chezmoi apply (no --force)."""
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
            "init",
        ],
        stdout=b"",
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
        ],
        stdout=b"",
    )
    with (
        patch(
            "acap_dotfiles.commands.restore.discover_binary",
            return_value=Path("/usr/bin/chezmoi"),
        ),
        patch("acap_dotfiles.commands.restore._is_tty", return_value=True),
    ):
        result = CliRunner().invoke(main, ["restore"])
    assert result.exit_code == 0


def test_restore_force_flag_passes_force_to_apply(
    fake_process: object, tmp_path: Path, monkeypatch: object
) -> None:
    """`dots restore --force` → passes --force to chezmoi apply."""
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
            "init",
        ],
        stdout=b"",
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
            "--force",
        ],
        stdout=b"",
    )
    with (
        patch(
            "acap_dotfiles.commands.restore.discover_binary",
            return_value=Path("/usr/bin/chezmoi"),
        ),
        patch("acap_dotfiles.commands.restore._is_tty", return_value=True),
    ):
        result = CliRunner().invoke(main, ["restore", "--force"])
    assert result.exit_code == 0


def test_restore_non_tty_auto_injects_force_and_writes_stub(
    fake_process: object, tmp_path: Path, monkeypatch: object
) -> None:
    """Non-TTY → auto-injects --force, writes stub chezmoi.toml when missing."""
    monkeypatch.setenv("ACAP_DOTFILES_HOME", str(tmp_path))  # type: ignore[attr-defined]
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))  # type: ignore[attr-defined]
    fake_process.register(  # type: ignore[attr-defined]
        [
            "/usr/bin/chezmoi",
            "--no-tty",
            "--no-pager",
            "--color=off",
            "--progress=false",
            "--source",
            str(tmp_path),
            "init",
        ],
        stdout=b"",
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
            "--force",
        ],
        stdout=b"",
    )
    with (
        patch(
            "acap_dotfiles.commands.restore.discover_binary",
            return_value=Path("/usr/bin/chezmoi"),
        ),
        patch("acap_dotfiles.commands.restore._is_tty", return_value=False),
    ):
        result = CliRunner().invoke(main, ["restore"])
    assert result.exit_code == 0
    stub_path = fake_home / ".config" / "chezmoi" / "chezmoi.toml"
    assert stub_path.is_file(), "non-TTY should write stub chezmoi.toml"
    content = stub_path.read_text()
    assert "[data]" in content


def test_restore_missing_chezmoi_binary_exits_2(tmp_path: Path, monkeypatch: object) -> None:
    """Missing chezmoi binary → exit 2."""
    monkeypatch.setenv("ACAP_DOTFILES_HOME", str(tmp_path))  # type: ignore[attr-defined]
    from acap_dotfiles.core.chezmoi import ChezmoiError

    with patch(
        "acap_dotfiles.commands.restore.discover_binary",
        side_effect=ChezmoiError("chezmoi binary not found"),
    ):
        result = CliRunner().invoke(main, ["restore"])
    assert result.exit_code == 2


def test_restore_custom_acap_dotfiles_home_overrides_source(
    fake_process: object, tmp_path: Path, monkeypatch: object
) -> None:
    """ACAP_DOTFILES_HOME custom → --source overrides default."""
    custom_home = tmp_path / "custom-dots-home"
    custom_home.mkdir()
    monkeypatch.setenv("ACAP_DOTFILES_HOME", str(custom_home))  # type: ignore[attr-defined]
    fake_process.register(  # type: ignore[attr-defined]
        [
            "/usr/bin/chezmoi",
            "--no-tty",
            "--no-pager",
            "--color=off",
            "--progress=false",
            "--source",
            str(custom_home),
            "init",
        ],
        stdout=b"",
    )
    fake_process.register(  # type: ignore[attr-defined]
        [
            "/usr/bin/chezmoi",
            "--no-tty",
            "--no-pager",
            "--color=off",
            "--progress=false",
            "--source",
            str(custom_home),
            "apply",
        ],
        stdout=b"",
    )
    with (
        patch(
            "acap_dotfiles.commands.restore.discover_binary",
            return_value=Path("/usr/bin/chezmoi"),
        ),
        patch("acap_dotfiles.commands.restore._is_tty", return_value=True),
    ):
        result = CliRunner().invoke(main, ["restore"])
    assert result.exit_code == 0
