"""dots status — port of lib/status.sh.

Prints a summary of: chezmoi-managed file count, presence of common config
paths, optional installed tools (oh-my-posh, eza, lazygit, etc.).
"""

from __future__ import annotations

import sys
from pathlib import Path

import click

from acap_dotfiles.core.chezmoi import ChezmoiError, Wrapper, discover_binary

# Paths the bash status.sh probes — same list, same order.
_PROBE_DIRS = [
    ("TPM", "~/.tmux/plugins/tpm"),
    ("zinit", "~/.local/share/zinit"),
    ("lazy.nvim", "~/.local/share/nvim/lazy/lazy.nvim"),
    ("fzf install dir", "~/.fzf"),
    ("conda root", "/opt/conda"),
    ("conda prod env", "/opt/conda/envs/prod"),
]
_PROBE_FILES = [
    # Paths reflect what the chezmoi source tree actually renders to —
    # most configs migrated to XDG (~/.config/...) so the legacy bash list
    # (~/.zshrc, ~/.tmux.conf, ~/.gitconfig) probed locations the repo no
    # longer ships. Verified via `chezmoi managed --include=files` against
    # the dotfiles source tree.
    ("zsh config", "~/.config/zsh/.zshrc"),
    ("nvim config", "~/.config/nvim/init.lua"),
    ("tmux config", "~/.config/tmux/tmux.conf"),
    ("git config", "~/.config/git/config"),
    ("wezterm config", "~/.wezterm.lua"),
    ("lazygit config", "~/.config/lazygit/config.yml"),
]


@click.command()
def status() -> None:
    """Show installation status of chezmoi + dotfile-managed tools.

    Reports the chezmoi-managed file count and probes a fixed set of common
    config paths and tool install dirs (TPM, zinit, lazy.nvim, fzf, conda,
    plus shell/editor/git config files). Each probe prints with a check or
    cross mark — useful for verifying a fresh restore landed everything.
    """
    try:
        binary = discover_binary()
    except ChezmoiError as e:
        click.echo(str(e), err=True)
        sys.exit(2)
    w = Wrapper(binary=binary)

    click.secho("== dotfiles status ==", bold=True)
    try:
        result = w.run(["managed", "--include=files"])
        count = len([ln for ln in result.stdout.splitlines() if ln.strip()])
        click.echo(f"  chezmoi-managed files: {count}")
    except ChezmoiError as e:
        click.echo(f"  chezmoi managed: ERROR ({e})", err=True)

    click.echo("")
    click.secho("== probed paths ==", bold=True)
    for label, p in _PROBE_DIRS:
        path = Path(p).expanduser()
        mark = "✓" if path.is_dir() else "✗"
        click.echo(f"  {mark} {label:20s} {p}")
    for label, p in _PROBE_FILES:
        path = Path(p).expanduser()
        mark = "✓" if path.is_file() else "✗"
        click.echo(f"  {mark} {label:20s} {p}")
