"""Manifest loader. The manifest declares which target paths chezmoi manages."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class ManifestEntry:
    path: str
    role: str = "common"


@dataclass(frozen=True)
class Manifest:
    version: int
    entries: tuple[ManifestEntry, ...]


def load_manifest(path: Path) -> Manifest:
    if not path.is_file():
        raise FileNotFoundError(f"manifest.yaml not found at {path}")
    raw = yaml.safe_load(path.read_text()) or {}
    return Manifest(
        version=int(raw.get("version", 1)),
        entries=tuple(
            ManifestEntry(path=e["path"], role=e.get("role", "common"))
            for e in raw.get("entries", [])
        ),
    )
