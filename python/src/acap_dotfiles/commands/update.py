import click


@click.command()
def update() -> None:
    """Pull, then apply chezmoi state."""
    click.echo("update: not yet implemented")
