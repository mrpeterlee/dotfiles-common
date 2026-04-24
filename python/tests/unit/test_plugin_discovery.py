"""Verify that LazyGroup discovers third-party verbs via the `dots.commands` entry-point group."""

from __future__ import annotations

from importlib.metadata import EntryPoint, EntryPoints
from unittest.mock import patch

import click
from click.testing import CliRunner

from acap_dotfiles.cli import main


@click.command()
def _stub_plugin() -> None:
    """A test plugin command."""
    click.echo("hello from plugin")


def test_lazy_group_picks_up_entry_points() -> None:
    """An entry point registered under `dots.commands` should be invokable as `dots <name>`."""
    fake_eps = EntryPoints(
        [EntryPoint("kms", "tests.unit.test_plugin_discovery:_stub_plugin", "dots.commands")]
    )
    with patch("acap_dotfiles.cli.entry_points", return_value=fake_eps):
        result = CliRunner().invoke(main, ["kms"])
    assert result.exit_code == 0, result.output
    assert "hello from plugin" in result.output
