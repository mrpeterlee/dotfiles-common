"""Streaming subprocess helper used by long chezmoi verbs (apply/update/init).

Pattern proven in atlas-onboard (https://github.com/Lunary-Lab/atlas-onboard
payload/src/atlas_onboard/chezmoi.py:140-156): Popen with line-buffered text
output, threads to drain stdout + stderr in real time, SIGINT forwarding to
the child via process group.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
from collections.abc import Callable, Sequence
from pathlib import Path

LineCallback = Callable[[str], None]


def stream(
    argv: Sequence[str],
    *,
    on_stdout: LineCallback,
    on_stderr: LineCallback,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> int:
    """Spawn argv, stream stdout/stderr to callbacks line by line.

    Returns the child's exit code. Forwards SIGINT to the child if Python
    receives it (so Ctrl-C gracefully terminates chezmoi mid-apply).

    When `env` is provided, it is MERGED with `os.environ` (mirroring
    `Wrapper.run`'s behavior) so long apply/update/init runs don't lose
    PATH, HOME, SSH_AUTH_SOCK, and credential tokens. Pass `env=None`
    (default) to inherit os.environ unchanged.
    """
    merged_env = {**os.environ, **env} if env is not None else None
    proc = subprocess.Popen(
        list(argv),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,  # line-buffered
        cwd=str(cwd) if cwd else None,
        env=merged_env,
        # Same process group so SIGINT propagates naturally
        start_new_session=False,
    )
    prior_handler = signal.signal(signal.SIGINT, lambda *_: proc.send_signal(signal.SIGINT))

    def _drain(stream_obj: object, callback: LineCallback) -> None:
        for line in iter(stream_obj.readline, ""):  # type: ignore[attr-defined]
            callback(line.rstrip("\n"))

    t_out = threading.Thread(target=_drain, args=(proc.stdout, on_stdout), daemon=True)
    t_err = threading.Thread(target=_drain, args=(proc.stderr, on_stderr), daemon=True)
    t_out.start()
    t_err.start()
    try:
        rc = proc.wait()
    finally:
        signal.signal(signal.SIGINT, prior_handler)
        t_out.join(timeout=2.0)
        t_err.join(timeout=2.0)
    return rc


if sys.platform == "win32":  # pragma: no cover
    # Windows doesn't have process groups in the POSIX sense; SIGINT becomes CTRL_C_EVENT
    # via subprocess.CREATE_NEW_PROCESS_GROUP. Defer to a stub that lets Ctrl-C bubble up.
    pass
