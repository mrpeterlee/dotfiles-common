import click


@click.command()
def backup() -> None:
    """Snapshot the destination state."""
    click.echo("backup: not yet implemented")
