import click


@click.group()
def ssh() -> None:
    """SSH config helpers."""


@ssh.command()
def render() -> None:
    """Render ~/.ssh/config from inventory."""
    click.echo("render: not yet implemented")
