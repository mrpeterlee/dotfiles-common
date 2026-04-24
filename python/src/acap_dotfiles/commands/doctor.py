import click


@click.command()
def doctor() -> None:
    """Run chezmoi doctor + dots health checks."""
    click.echo("doctor: not yet implemented")
