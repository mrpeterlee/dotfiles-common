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
    """Update all installed components: apply dotfiles, then refresh externals.

    Two-phase update: (1) `chezmoi apply` — hard fails on error; (2) `chezmoi
    apply --refresh-externals` — best-effort, warns on failure. Conda env
    rebuild and essential-tools install (Phases 3-4 in the legacy bash
    `update`) stay in bash for P3 — see the printed Note for routing.
    """
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

    # Phase 3-4: conda env rebuild + essential tools install — out of P3 scope.
    # Direct users at the legacy bash entry-point (lib/cli-legacy.sh), NOT
    # `~/.files/cli` — the cli shim now delegates `restore` to dots restore
    # (also out of P3 scope as a stub for the install_essential_tools phase).
    # Codex P2 caught the routing mismatch on bce3f1b. `cli conda` still
    # works through the shim because the shim explicitly forwards `conda`
    # and `agents` to lib/cli-legacy.sh.
    click.echo("\nNote: conda env rebuild and essential-tools install stay in bash for P3.")
    click.echo("  conda env: ~/.files/cli conda build  (routed through legacy shim)")
    click.echo("  essential tools: ~/.files/lib/cli-legacy.sh restore  (direct invocation)")
