"""Build the test Docker image once per session, return the tag."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def docker_image() -> str:
    """Build the test image; skip the test gracefully if Docker is unavailable."""
    tag = "dots-cli-test:latest"
    df = Path(__file__).parent / "Dockerfile.test"
    try:
        subprocess.run(
            ["docker", "build", "-q", "-t", tag, "-f", str(df), str(df.parent)],
            check=True,
            capture_output=True,
        )
    except FileNotFoundError:
        pytest.skip("Docker not available (docker binary not on PATH)")
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode("utf-8", errors="replace") if exc.stderr else ""
        pytest.skip(f"Docker not available (build failed): {stderr.strip()[:200]}")
    return tag
