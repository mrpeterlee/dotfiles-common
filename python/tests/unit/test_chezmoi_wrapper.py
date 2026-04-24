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


def test_dry_run_injected_when_mutating_verb_present(fake_process: object) -> None:
    """ANY occurrence of a mutating verb in args triggers --dry-run injection."""
    w = Wrapper(binary=Path("/usr/bin/chezmoi"), dry_run=True)
    for argv_in in [
        ["apply"],
        ["-S", "/tmp/src", "apply"],
        ["--config", "cfg.toml", "update"],
        ["--source-path", "apply"],  # boolean flag — codex P1 r3
        ["--source=/tmp/src", "apply"],
        ["--debug", "-S", "/tmp/src", "--config", "cfg.toml", "apply"],
    ]:
        result = w.build_argv(argv_in)
        assert "--dry-run" in result, f"missed --dry-run for {argv_in}"


def test_dry_run_skipped_when_no_mutating_verb(fake_process: object) -> None:
    """Read-only invocations don't get --dry-run."""
    w = Wrapper(binary=Path("/usr/bin/chezmoi"), dry_run=True)
    for argv_in in [
        ["data"],
        ["-S", "/tmp/src", "data"],
        ["doctor"],
        ["managed", "--include=files"],
        ["status"],
        ["diff"],
    ]:
        result = w.build_argv(argv_in)
        assert "--dry-run" not in result, f"unexpected --dry-run for {argv_in}"


def test_dry_run_not_injected_when_already_present(fake_process: object) -> None:
    """If caller already passed --dry-run, don't double-inject."""
    w = Wrapper(binary=Path("/usr/bin/chezmoi"), dry_run=True)
    result = w.build_argv(["apply", "--dry-run"])
    assert result.count("--dry-run") == 1


def test_no_dry_run_when_wrapper_dry_run_false(fake_process: object) -> None:
    """If wrapper.dry_run is False, never inject."""
    w = Wrapper(binary=Path("/usr/bin/chezmoi"), dry_run=False)
    result = w.build_argv(["apply"])
    assert "--dry-run" not in result


def test_false_positive_acceptable_for_arg_value_named_apply(fake_process: object) -> None:
    """Documented behavior: -c apply.toml does NOT trigger --dry-run injection.

    Per the redesign rationale: false positives are harmless (chezmoi's
    --dry-run on a read verb is just a no-op). The benefit is eliminating
    the "is this arg a verb or operand?" parsing bug class.

    Note: ['apply.toml'] is NOT in _MUTATING_VERBS (only the literal 'apply'
    is). This test should NOT match — it's an edge case worth documenting
    but not actually a false positive.
    """
    w = Wrapper(binary=Path("/usr/bin/chezmoi"), dry_run=True)
    result = w.build_argv(["-c", "apply.toml", "data"])
    assert "--dry-run" not in result  # 'apply.toml' != 'apply' verbatim


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


def test_dry_run_skipped_when_mutating_verb_appears_after_double_dash() -> None:
    """Passthrough args after `--` must not false-positive trigger --dry-run.

    Caught by codex P2 round 4 on 959eec3: `chezmoi git -- grep apply` would
    otherwise inject --dry-run because 'apply' is in args, but it's a grep
    pattern being passed through to git, not a chezmoi verb.
    """
    w = Wrapper(binary=Path("/usr/bin/chezmoi"), dry_run=True)
    result = w.build_argv(["git", "--", "grep", "apply"])
    assert "--dry-run" not in result
    # Sanity: the same args without `--` would inject (apply IS a mutating verb name)
    result2 = w.build_argv(["git", "grep", "apply"])
    assert "--dry-run" in result2


def test_dry_run_inserted_before_passthrough_separator() -> None:
    """Codex P3 r5: when args contain `--`, --dry-run must be inserted BEFORE it.

    Prevents `chezmoi apply -- target --dry-run` (which chezmoi would treat as
    a target name) instead of the correct `chezmoi apply --dry-run -- target`.
    """
    w = Wrapper(binary=Path("/usr/bin/chezmoi"), dry_run=True)
    result = w.build_argv(["apply", "--", "target1", "target2"])
    dash_idx = result.index("--")
    dry_run_idx = result.index("--dry-run")
    assert dry_run_idx < dash_idx, f"--dry-run at {dry_run_idx} must precede -- at {dash_idx}: {result}"
    # Sanity: passthrough args after -- preserved verbatim
    assert result[dash_idx + 1 : dash_idx + 3] == ["target1", "target2"]
