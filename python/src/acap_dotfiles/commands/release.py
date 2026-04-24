import click


@click.group()
def release() -> None:
    """Release management commands."""


@release.command()
@click.argument("level", type=click.Choice(["patch", "minor", "major"]))
def cut(level: str) -> None:
    """Cut a new release at the given semver level."""
    click.echo(f"cut {level}: not yet implemented")
