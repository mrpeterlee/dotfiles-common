"""Host role storage + validation.

Reads/writes ``~/.config/dots/role.toml`` (path supplied by caller). The file
holds a single key, ``role``, whose value is one of ``VALID_ROLES``. Used by
P4 inventory rendering to pick the correct host inventory.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

import tomli_w

VALID_ROLES: Final[frozenset[str]] = frozenset({"acap", "tapai", "personal"})


class RoleError(ValueError):
    """Raised when an invalid role is supplied to :func:`set_role`."""


def get_role(path: Path) -> str | None:
    """Return the host role stored at ``path``, or ``None`` if unset."""
    if not path.is_file():
        return None
    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover  py3.10
        import tomli as tomllib  # type: ignore[no-redef,import-not-found]
    data = tomllib.loads(path.read_text())
    role = data.get("role")
    return str(role) if role else None


def set_role(path: Path, role: str) -> None:
    """Write ``role`` to ``path`` atomically.

    Raises :class:`RoleError` if ``role`` is not in :data:`VALID_ROLES`.
    The write goes to ``<path>.tmp`` first, then ``os.replace`` swaps it in,
    so an interrupted write never leaves a half-written file behind.
    """
    if role not in VALID_ROLES:
        raise RoleError(f"invalid role: {role!r}; must be one of {sorted(VALID_ROLES)}")
    path.parent.mkdir(parents=True, exist_ok=True)
    # Atomic write: tmp file in same dir, then os.replace
    tmp = path.with_suffix(".toml.tmp")
    tmp.write_bytes(tomli_w.dumps({"role": role}).encode())
    os.replace(tmp, path)
