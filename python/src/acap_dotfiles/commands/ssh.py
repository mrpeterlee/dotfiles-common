"""dots ssh render — emit SSH config from inventory YAML."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from acap_dotfiles.core.config import DotsConfig
from acap_dotfiles.core.inventory import load_hosts, render_ssh_config


@click.group()
def ssh() -> None:
    """SSH-related helpers (config rendering from inventory)."""


@ssh.command()
@click.option(
    "--inventory",
    "inventory_dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Inventory dir (default: $ACAP_DOTFILES_HOME/inventory/hosts).",
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Output file (default: stdout).",
)
@click.option(
    "--role",
    "role_filter",
    type=str,
    default=None,
    help="Only emit hosts matching this role.",
)
def render(inventory_dir: Path | None, out_path: Path | None, role_filter: str | None) -> None:
    """Render an SSH config block from inventory YAML.

    Reads every `*.yml` under `--inventory` (default
    `$ACAP_DOTFILES_HOME/inventory/hosts`), emits a deterministic
    `~/.ssh/config`-shaped block, and writes to `--out` (or stdout). Use
    `--role` to scope output to a single host class (e.g. `--role personal`).
    Safe to pipe into a chezmoi-managed include.
    """
    cfg = DotsConfig()
    inventory = inventory_dir or (cfg.home / "inventory" / "hosts")
    if not inventory.is_dir():
        click.echo(f"inventory dir not found: {inventory}", err=True)
        sys.exit(2)
    hosts = load_hosts(inventory)
    if not hosts:
        click.echo(f"no host yaml files under {inventory}", err=True)
        sys.exit(2)
    output = render_ssh_config(hosts, role_filter=role_filter)
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output)
        click.echo(f"wrote {len(hosts)} hosts → {out_path}")
    else:
        click.echo(output, nl=False)
