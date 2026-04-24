import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from acap_dotfiles.core.chezmoi import (
    ChezmoiError,
    ChezmoiResult,
    Wrapper,
    discover_binary,
)


def test_discover_binary_returns_first_match_in_path(tmp_path: Path) -> None:
    fake = tmp_path / "chezmoi"
    fake.write_text("#!/bin/sh\necho fake")
    fake.chmod(0o755)
    with patch("acap_dotfiles.core.chezmoi.shutil.which", return_value=str(fake)):
        assert discover_binary() == fake


def test_discover_binary_falls_back_to_local_bin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    bindir = tmp_path / ".local" / "bin"
    bindir.mkdir(parents=True)
    fallback = bindir / "chezmoi"
    fallback.write_text("#!/bin/sh\necho fallback")
    fallback.chmod(0o755)
    with patch("acap_dotfiles.core.chezmoi.shutil.which", return_value=None):
        assert discover_binary() == fallback


def test_discover_binary_raises_chezmoierror_when_nothing_found(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    with (
        patch("acap_dotfiles.core.chezmoi.shutil.which", return_value=None),
        pytest.raises(ChezmoiError, match="chezmoi binary not found"),
    ):
        discover_binary()


def test_env_override_takes_priority(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    custom = tmp_path / "custom-chezmoi"
    custom.write_text("#!/bin/sh\necho custom")
    custom.chmod(0o755)
    monkeypatch.setenv("DOTS_CHEZMOI_BIN", str(custom))
    # shutil.which would return something else, but env override wins
    with patch("acap_dotfiles.core.chezmoi.shutil.which", return_value="/usr/bin/chezmoi"):
        assert discover_binary() == custom


def test_wrapper_run_calls_subprocess_with_canonical_args(fake_process: object) -> None:
    """Verify the wrapper always passes --no-tty --no-pager --color=off --progress=false."""
    fake_process.register(  # type: ignore[attr-defined]
        [
            "/usr/bin/chezmoi",
            "--no-tty",
            "--no-pager",
            "--color=off",
            "--progress=false",
            "data",
            "--format=json",
        ],
        stdout=b'{"role":"acap"}\n',
    )
    w = Wrapper(binary=Path("/usr/bin/chezmoi"))
    result: ChezmoiResult = w.run(["data", "--format=json"])
    assert result.returncode == 0
    assert result.stdout == '{"role":"acap"}\n'


def test_wrapper_run_raises_on_nonzero_when_check_true(fake_process: object) -> None:
    fake_process.register(  # type: ignore[attr-defined]
        ["/usr/bin/chezmoi", "--no-tty", "--no-pager", "--color=off", "--progress=false", "apply"],
        returncode=1,
        stderr=b"chezmoi: template error\n",
    )
    w = Wrapper(binary=Path("/usr/bin/chezmoi"))
    with pytest.raises(ChezmoiError, match="template error"):
        w.run(["apply"])


def test_wrapper_run_returns_result_when_check_false(fake_process: object) -> None:
    fake_process.register(  # type: ignore[attr-defined]
        ["/usr/bin/chezmoi", "--no-tty", "--no-pager", "--color=off", "--progress=false", "diff"],
        returncode=1,
        stdout=b"--- a\n+++ b\n",
    )
    w = Wrapper(binary=Path("/usr/bin/chezmoi"))
    result = w.run(["diff"], check=False)
    assert result.returncode == 1
    assert "--- a" in result.stdout


def test_wrapper_dry_run_injects_flag_for_mutating_verbs(fake_process: object) -> None:
    fake_process.register(  # type: ignore[attr-defined]
        [
            "/usr/bin/chezmoi",
            "--no-tty",
            "--no-pager",
            "--color=off",
            "--progress=false",
            "apply",
            "--dry-run",
        ],
        stdout=b"would apply\n",
    )
    w = Wrapper(binary=Path("/usr/bin/chezmoi"), dry_run=True)
    result = w.run(["apply"])
    assert result.returncode == 0
    assert "would apply" in result.stdout


def test_wrapper_dry_run_does_NOT_inject_flag_for_read_verbs(fake_process: object) -> None:
    fake_process.register(  # type: ignore[attr-defined]
        ["/usr/bin/chezmoi", "--no-tty", "--no-pager", "--color=off", "--progress=false", "data"],
        stdout=b"{}\n",
    )
    w = Wrapper(binary=Path("/usr/bin/chezmoi"), dry_run=True)
    w.run(["data"])  # would crash if --dry-run were injected


def test_build_argv_dry_run_injects_when_global_flag_precedes_mutating_verb() -> None:
    """Codex P1: `chezmoi --debug apply` must still get --dry-run.

    Old logic only checked args[0]; with a global flag in front, the verb
    moves to args[1] and the mutation would silently run for real.
    """
    w = Wrapper(binary=Path("/usr/bin/chezmoi"), dry_run=True)
    argv = w.build_argv(["--debug", "apply"])
    assert "--dry-run" in argv
    # And it should come after the user args, not in the middle of canonical args
    assert argv[-1] == "--dry-run"


def test_build_argv_dry_run_does_not_inject_for_read_verb_with_global_flag() -> None:
    """`chezmoi -v data` should NOT get --dry-run (data is read-only)."""
    w = Wrapper(binary=Path("/usr/bin/chezmoi"), dry_run=True)
    argv = w.build_argv(["-v", "data"])
    assert "--dry-run" not in argv


def test_build_argv_dry_run_still_works_for_bare_mutating_verb() -> None:
    """Existing behavior: `apply` with no preceding flags still gets --dry-run."""
    w = Wrapper(binary=Path("/usr/bin/chezmoi"), dry_run=True)
    argv = w.build_argv(["apply"])
    assert "--dry-run" in argv


def test_discover_binary_skips_non_executable_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Codex P3: a non-executable ~/.local/bin/chezmoi must NOT be returned.

    Returning it causes a later PermissionError. The function should treat
    the candidate as absent and (since ~/bin is also missing) raise.
    """
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("DOTS_CHEZMOI_BIN", raising=False)
    bindir = tmp_path / ".local" / "bin"
    bindir.mkdir(parents=True)
    fallback = bindir / "chezmoi"
    fallback.write_text("#!/bin/sh\necho fallback")
    fallback.chmod(0o644)  # readable but NOT executable
    with (
        patch("acap_dotfiles.core.chezmoi.shutil.which", return_value=None),
        pytest.raises(ChezmoiError, match="chezmoi binary not found"),
    ):
        discover_binary()


# Silence unused-import: shutil is referenced via the patch target string only.
_ = shutil
