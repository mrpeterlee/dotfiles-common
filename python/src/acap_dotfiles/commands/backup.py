"""dots backup — port of lib/backup.sh.

Runs chezmoi re-add to sync ~/.claude (and other managed paths) back into the
source dir, then prints what git would commit.
"""

from __future__ import annotations

import sys

import click

from acap_dotfiles.core.chezmoi import ChezmoiError, Wrapper, discover_binary
from acap_dotfiles.core.config import DotsConfig
from acap_dotfiles.core.git import GitError, status_porcelain
from acap_dotfiles.io.exec import stream


@click.command()
@click.pass_context
def backup(ctx: click.Context) -> None:
    """Capture live system changes back into the chezmoi source repo.

    Runs `chezmoi re-add` to pull modified managed files (e.g. updated
    `~/.claude/CLAUDE.md`) back into `$ACAP_DOTFILES_HOME`, then prints a
    `git status --porcelain` preview of what would be committed. Stops short
    of the actual commit/push so you can review before sealing — the next-step
    hint is printed at the end.
    """
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

    # Use `git status --porcelain --untracked-files=all` (not `git diff --name-only HEAD`):
    # chezmoi re-add can drop brand-new files into the source tree as untracked,
    # which `git diff` would silently miss.
    try:
        files = status_porcelain(cfg.home)
    except GitError as e:
        click.echo(f"git status failed: {e}", err=True)
        sys.exit(2)

    if not files:
        click.echo("\nNo changes — backup would be a no-op commit.")
        return
    click.secho(f"\nFiles updated ({len(files)}):", bold=True)
    for f in files:
        click.echo(f"  {f}")
    click.echo(f"\nNext: cd {cfg.home} && git add -A && git commit -m '...' && git push")
