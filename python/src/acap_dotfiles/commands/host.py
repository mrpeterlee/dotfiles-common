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
    """Inspect or set the host role (acap | tapai | personal)."""


@host.group()
def role() -> None:
    """Show or set the host role."""


@role.command()
def show() -> None:
    """Print the current host role (or 'unset')."""
    r = get_role(_config_path())
    click.echo(r or "unset")


@role.command(name="set")
@click.argument("value")
def set_cmd(value: str) -> None:
    """Set the host role to one of {acap, tapai, personal}."""
    try:
        set_role(_config_path(), value)
        click.echo(f"role set to {value}")
    except RoleError as e:
        click.echo(str(e), err=True)
        sys.exit(2)
