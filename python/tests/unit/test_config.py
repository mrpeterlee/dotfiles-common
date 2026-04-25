from pathlib import Path

import pytest

from acap_dotfiles.core.config import DotsConfig


def test_defaults() -> None:
    cfg = DotsConfig()
    assert cfg.home == Path.home() / ".files"
    assert cfg.channel == "stable"
    assert cfg.role is None


def test_env_var_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ACAP_DOTFILES_HOME", str(tmp_path))
    monkeypatch.setenv("ACAP_DOTFILES_CHANNEL", "edge")
    monkeypatch.setenv("ACAP_DOTFILES_ROLE", "acap")
    cfg = DotsConfig()
    assert cfg.home == tmp_path
    assert cfg.channel == "edge"
    assert cfg.role == "acap"


def test_init_kwargs_beat_env_vars(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """CLI flag (passed as init kwarg) > env > file > default."""
    monkeypatch.setenv("ACAP_DOTFILES_CHANNEL", "edge")
    cfg = DotsConfig(channel="stable")
    assert cfg.channel == "stable"  # CLI wins


def test_invalid_channel_rejected() -> None:
    with pytest.raises(ValueError, match="Input should be"):
        DotsConfig(channel="not-a-channel")
