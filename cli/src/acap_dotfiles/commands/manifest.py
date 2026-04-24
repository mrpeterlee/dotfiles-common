import click


@click.group()
def manifest() -> None:
    """Inspect the dotfiles manifest."""


@manifest.command()
def show() -> None:
    """Print the manifest."""
    click.echo("show: not yet implemented")
