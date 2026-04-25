"""Runtime configuration for `dots`.

Precedence: CLI flags (init kwargs) > env vars > config file > defaults.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DotsConfig(BaseSettings):
    """User-facing configuration. Constructed once per `dots` invocation."""

    model_config = SettingsConfigDict(
        env_prefix="ACAP_DOTFILES_",
        env_file=None,  # we take config from a TOML file, not dotenv
        case_sensitive=False,
        extra="ignore",
    )

    home: Path = Field(default_factory=lambda: Path.home() / ".files")
    channel: Literal["stable", "edge"] = "stable"
    role: str | None = None
