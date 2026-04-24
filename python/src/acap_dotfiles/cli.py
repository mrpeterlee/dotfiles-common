"""Click root for the `dots` CLI. Lazy-loads each command module on demand."""

from __future__ import annotations

import importlib
import os
import sys

import click

from acap_dotfiles import __version__

# Map each verb to "module.path:attribute". The attribute MUST be a click.Command
# (a function decorated with @click.command or @click.group).
LAZY_COMMANDS: dict[str, str] = {
    "apply": "acap_dotfiles.commands.apply:apply",
    "update": "acap_dotfiles.commands.update:update",
    "status": "acap_dotfiles.commands.status:status",
    "doctor": "acap_dotfiles.commands.doctor:doctor",
    "backup": "acap_dotfiles.commands.backup:backup",
    "restore": "acap_dotfiles.commands.restore:restore",
    "ssh": "acap_dotfiles.commands.ssh:ssh",
    "host": "acap_dotfiles.commands.host:host",
    "manifest": "acap_dotfiles.commands.manifest:manifest",
    "release": "acap_dotfiles.commands.release:release",
    "migrate-from-legacy": "acap_dotfiles.commands.migrate:migrate_from_legacy",
}


class LazyGroup(click.Group):
    """A click.Group that resolves subcommands via dotted-path lookup on demand."""

    def __init__(
        self, *args: object, lazy_subcommands: dict[str, str] | None = None, **kw: object
    ) -> None:
        super().__init__(*args, **kw)  # type: ignore[arg-type]
        self._lazy = dict(lazy_subcommands or {})

    def list_commands(self, ctx: click.Context) -> list[str]:
        eager = super().list_commands(ctx)
        return sorted({*eager, *self._lazy})

    def get_command(self, ctx: click.Context, name: str) -> click.Command | None:
        if name in self._lazy:
            module_path, attr = self._lazy[name].split(":", 1)
            module = importlib.import_module(module_path)
            cmd = getattr(module, attr)
            assert isinstance(cmd, click.Command), f"{module_path}:{attr} is not a Click command"
            return cmd
        return super().get_command(ctx, name)


@click.command(cls=LazyGroup, lazy_subcommands=LAZY_COMMANDS)
@click.version_option(__version__, prog_name="dots")
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Increase verbosity (-v info, -vv debug, -vvv chezmoi --debug).",
)
@click.option(
    "--no-color",
    is_flag=True,
    default=False,
    help="Disable ANSI colors. Also honors NO_COLOR env var.",
)
@click.option(
    "--dry-run", is_flag=True, default=False, help="Pass --dry-run to mutating chezmoi verbs."
)
@click.pass_context
def main(ctx: click.Context, verbose: int, no_color: bool, dry_run: bool) -> None:
    """Unified cross-platform CLI for the dotfiles-common chezmoi-managed dotfiles.

    Runs on Linux, macOS, and Windows. Wraps chezmoi for apply/update/restore plus
    inventory-as-code helpers (ssh render), release management (release cut), and
    a one-shot migration from the legacy bash `cli` (migrate-from-legacy).
    """
    # Honor NO_COLOR env var (https://no-color.org)
    if no_color or os.environ.get("NO_COLOR"):
        os.environ["NO_COLOR"] = "1"
    from acap_dotfiles.io.log import configure

    configure(verbose=verbose)
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["dry_run"] = dry_run


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
