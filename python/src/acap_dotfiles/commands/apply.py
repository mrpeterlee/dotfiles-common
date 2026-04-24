"""dots apply — port of lib/apply.sh.

Forwards extra args verbatim to chezmoi apply. Use `dots apply -- <args>` to
ensure Click doesn't swallow chezmoi flags.
"""

from __future__ import annotations

import sys

import click

from acap_dotfiles.core.chezmoi import ChezmoiError, Wrapper, discover_binary
from acap_dotfiles.core.config import DotsConfig
from acap_dotfiles.io.exec import stream


@click.command(context_settings={"ignore_unknown_options": True})
@click.argument("chezmoi_args", nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def apply(ctx: click.Context, chezmoi_args: tuple[str, ...]) -> None:
    """Apply chezmoi state to the destination. Extra args forwarded to chezmoi."""
    cfg = DotsConfig()
    try:
        binary = discover_binary()
    except ChezmoiError as e:
        click.echo(str(e), err=True)
        sys.exit(2)
    w = Wrapper(binary=binary, dry_run=ctx.obj.get("dry_run", False), source=cfg.home)

    # Stream apply output — long-running verb, user wants real-time progress.
    argv = w.build_argv(["apply", *chezmoi_args])
    rc = stream(
        argv,
        on_stdout=lambda line: click.echo(line),
        on_stderr=lambda line: click.echo(line, err=True),
    )
    sys.exit(rc)
