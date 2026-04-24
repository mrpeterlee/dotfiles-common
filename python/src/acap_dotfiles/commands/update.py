"""dots update — port of lib/update.sh (Phases 1-2 only; conda + tools are bash-only for P3)."""

from __future__ import annotations

import sys

import click

from acap_dotfiles.core.chezmoi import ChezmoiError, Wrapper, discover_binary
from acap_dotfiles.core.config import DotsConfig
from acap_dotfiles.io.exec import stream


@click.command()
@click.pass_context
def update(ctx: click.Context) -> None:
    """Apply, then refresh externals (best-effort), then prompt for conda/tools (out of scope for P3)."""
    cfg = DotsConfig()
    try:
        binary = discover_binary()
    except ChezmoiError as e:
        click.echo(str(e), err=True)
        sys.exit(2)
    w = Wrapper(binary=binary, dry_run=ctx.obj.get("dry_run", False), source=cfg.home)

    # Phase 1: apply (HARD failure aborts)
    rc = stream(
        w.build_argv(["apply"]),
        on_stdout=lambda line: click.echo(line),
        on_stderr=lambda line: click.echo(line, err=True),
    )
    if rc != 0:
        click.echo(f"chezmoi apply failed (rc={rc})", err=True)
        sys.exit(rc)

    # Phase 2: refresh-externals (best-effort, WARN on failure)
    rc2 = stream(
        w.build_argv(["apply", "--refresh-externals"]),
        on_stdout=lambda line: click.echo(line),
        on_stderr=lambda line: click.echo(line, err=True),
    )
    if rc2 != 0:
        click.echo(f"WARN: --refresh-externals exited {rc2} (best-effort, continuing)", err=True)

    # Phase 3-4: conda env rebuild + essential tools install — out of P3 scope
    click.echo("\nNote: conda env rebuild and essential-tools install are still in bash `cli`.")
    click.echo("Run `~/.files/cli conda build` and `~/.files/cli restore` manually if needed.")
