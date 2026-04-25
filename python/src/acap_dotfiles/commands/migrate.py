"""dots migrate-from-legacy — print migration banner + write marker."""

from __future__ import annotations

import shutil
from pathlib import Path

import click


@click.command(name="migrate-from-legacy")
def migrate_from_legacy() -> None:
    """Acknowledge the migration from legacy bash `cli` to `dots`.

    Idempotent: prints the verb-mapping banner (cli apply → dots apply, etc.)
    and which subcommands stay bash-only (`cli conda`, `cli agents`), then
    drops a marker at `~/.config/dots/.migrated` so subsequent invocations
    are silent. Run once after upgrading to the P3 shim.
    """
    marker = Path.home() / ".config" / "dots" / ".migrated"
    if marker.exists():
        click.echo("already migrated; nothing to do")
        return
    legacy = shutil.which("cli")
    if not legacy:
        click.echo("legacy `cli` not detected on PATH; you're all set")
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.touch()
        return
    click.echo("Migration from legacy bash cli")
    click.echo("==============================")
    click.echo(f"Detected legacy: {legacy}")
    click.echo("")
    click.echo("Mapping:")
    click.echo("  cli apply      → dots apply")
    click.echo("  cli update     → dots update")
    click.echo("  cli status     → dots status")
    click.echo("  cli backup     → dots backup")
    click.echo("  cli restore    → dots restore")
    click.echo("")
    click.echo("Still bash-only (no migration):")
    click.echo("  cli conda <subcommand>")
    click.echo("  cli agents <subcommand>")
    click.echo("")
    click.echo("Re-run `cli` from a fresh shell after this PR lands — it now exec's `dots`.")
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.touch()
