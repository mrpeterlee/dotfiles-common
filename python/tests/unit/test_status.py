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


def test_status_probes_xdg_paths_after_migration() -> None:
    """Status must probe ~/.config/<tool>/... — not the legacy ~/.zshrc tree.

    Regression test for the codex P2 finding: the bash list checked
    ~/.zshrc, ~/.tmux.conf, ~/.gitconfig — none of which the repo renders
    after the XDG migration. Verified by importing the probe table directly
    so a future revert can't silently re-introduce the bare-home paths.
    """
    from acap_dotfiles.commands.status import _PROBE_FILES

    paths = {label: path for label, path in _PROBE_FILES}
    assert paths["zsh config"] == "~/.config/zsh/.zshrc"
    assert paths["tmux config"] == "~/.config/tmux/tmux.conf"
    assert paths["git config"] == "~/.config/git/config"
    # Legacy bare-home paths must NOT appear anywhere in the probe table.
    bare = {p for _, p in _PROBE_FILES}
    assert "~/.zshrc" not in bare
    assert "~/.tmux.conf" not in bare
    assert "~/.gitconfig" not in bare
