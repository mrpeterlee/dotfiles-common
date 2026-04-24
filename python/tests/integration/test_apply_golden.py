"""End-to-end: dots apply against a real chezmoi source in a container."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


@pytest.mark.integration
def test_apply_renders_zshrc(docker_image: str, tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / ".chezmoi.toml.tmpl").write_text("# minimal\n")
    (src / "dot_zshrc").write_text("export PATH=$HOME/.local/bin:$PATH\n")
    python_path = Path(__file__).resolve().parents[2]  # python/ root
    try:
        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "-v",
                f"{src}:/src",
                "-v",
                f"{python_path}:/python",
                "-e",
                "ACAP_DOTFILES_HOME=/src",
                "-w",
                "/python",
                docker_image,
                "bash",
                "-c",
                "uv pip install --system -e . && dots apply",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        pytest.skip("Docker not available (docker binary not on PATH)")
    assert result.returncode == 0, f"stderr:\n{result.stderr}"
