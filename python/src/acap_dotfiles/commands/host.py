"""dots host role show|set — read/write ~/.config/dots/role.toml."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from acap_dotfiles.core.role import RoleError, get_role, set_role


def _config_path() -> Path:
    base = Path.home() / ".config" / "dots"
    return base / "role.toml"


@click.group()
def host() -> None:
    """Inspect or modify per-host metadata (currently: role).

    The host role gates which chezmoi templates render and which 1Password
    vault `op` reads from. Persisted in `~/.config/dots/role.toml` so it
    survives chezmoi re-applies.
    """


@host.group()
def role() -> None:
    """Show or set the host role (acap | tapai | personal)."""


@role.command()
def show() -> None:
    """Print the current host role (or 'unset' if never set).

    Reads `~/.config/dots/role.toml`. Useful as a guard in shell scripts —
    e.g. `[[ "$(dots host role show)" == acap ]] && op-use acap`.
    """
    r = get_role(_config_path())
    click.echo(r or "unset")


@role.command(name="set")
@click.argument("value")
def set_cmd(value: str) -> None:
    """Set the host role to one of {acap, tapai, personal}.

    Writes `~/.config/dots/role.toml` atomically. Re-run `dots apply`
    afterwards so chezmoi templates pick up the new role.
    """
    try:
        set_role(_config_path(), value)
        click.echo(f"role set to {value}")
    except RoleError as e:
        click.echo(str(e), err=True)
        sys.exit(2)
