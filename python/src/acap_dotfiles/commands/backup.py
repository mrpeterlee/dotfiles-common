"""dots backup — port of lib/backup.sh.

Runs chezmoi re-add to sync ~/.claude (and other managed paths) back into the
source dir, then prints what git would commit.
"""

from __future__ import annotations

import sys

import click

from acap_dotfiles.core.chezmoi import ChezmoiError, Wrapper, discover_binary
from acap_dotfiles.core.config import DotsConfig
from acap_dotfiles.core.git import GitError, diff_name_only
from acap_dotfiles.io.exec import stream


@click.command()
@click.pass_context
def backup(ctx: click.Context) -> None:
    """chezmoi re-add then `git diff --name-only` to preview commit."""
    cfg = DotsConfig()
    try:
        binary = discover_binary()
    except ChezmoiError as e:
        click.echo(str(e), err=True)
        sys.exit(2)
    w = Wrapper(binary=binary, dry_run=ctx.obj.get("dry_run", False), source=cfg.home)

    rc = stream(
        w.build_argv(["re-add"]),
        on_stdout=lambda line: click.echo(line),
        on_stderr=lambda line: click.echo(line, err=True),
    )
    if rc != 0:
        click.echo(f"chezmoi re-add failed (rc={rc})", err=True)
        sys.exit(rc)

    try:
        files = diff_name_only(cfg.home)
    except GitError as e:
        click.echo(f"git diff failed: {e}", err=True)
        sys.exit(2)

    if not files:
        click.echo("\nNo changes — backup would be a no-op commit.")
        return
    click.secho(f"\nFiles updated ({len(files)}):", bold=True)
    for f in files:
        click.echo(f"  {f}")
    click.echo("\nNext: cd ~/.files && git add -A && git commit -m '...' && git push")
