import click


@click.group()
def host() -> None:
    """Inspect or set the host role (acap | tapai | personal)."""


@host.group()
def role() -> None:
    """Show or set the host role."""


@role.command()
def show() -> None:
    """Print the current host role."""
    click.echo("show: not yet implemented")
