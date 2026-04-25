"""dots manifest show — print the manifest in human or JSON format."""

from __future__ import annotations

import json as json_lib
import sys
from dataclasses import asdict

import click

from acap_dotfiles.core.config import DotsConfig
from acap_dotfiles.core.manifest import load_manifest


@click.group()
def manifest() -> None:
    """Inspect the chezmoi-managed file manifest.

    The manifest at `$ACAP_DOTFILES_HOME/manifest.yaml` is the canonical
    list of which paths each host role owns. Subcommands here are read-only.
    """


@manifest.command()
@click.option("--json", "as_json", is_flag=True, help="Emit JSON instead of human-readable text.")
def show(as_json: bool) -> None:
    """Print the manifest as `(role, path)` entries.

    Default output is `<role>  <path>` per line, sorted by manifest order.
    Pass `--json` for a machine-readable envelope `{version, entries: [...]}`,
    suitable for piping into `jq` or driving a chezmoi-template generator.
    """
    cfg = DotsConfig()
    path = cfg.home / "manifest.yaml"
    try:
        m = load_manifest(path)
    except FileNotFoundError as e:
        click.echo(str(e), err=True)
        sys.exit(2)
    if as_json:
        click.echo(
            json_lib.dumps(
                {
                    "version": m.version,
                    "entries": [asdict(e) for e in m.entries],
                },
                indent=2,
            )
        )
        return
    click.echo(f"manifest version {m.version} ({len(m.entries)} entries)")
    for e in m.entries:
        click.echo(f"  {e.role:10s} {e.path}")
