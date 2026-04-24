import click


@click.command(name="migrate-from-legacy")
def migrate_from_legacy() -> None:
    """One-shot migration from the legacy bash cli."""
    click.echo("migrate-from-legacy: not yet implemented")
