"""Tests for `dots restore` — chezmoi init + apply (pkg install stays bash for P3)."""

from __future__ import annotations

import tomllib
from pathlib import Path, PureWindowsPath
from unittest.mock import patch

from click.testing import CliRunner
from tests.conftest import CHEZMOI_BIN, CHEZMOI_BIN_ARGV

from acap_dotfiles.cli import main


def test_restore_with_tty_invokes_init_then_apply_without_force(
    fake_process: object, tmp_path: Path, monkeypatch: object
) -> None:
    """Bare `dots restore` with TTY → chezmoi init + chezmoi apply (no --force)."""
    monkeypatch.setenv("ACAP_DOTFILES_HOME", str(tmp_path))  # type: ignore[attr-defined]
    fake_process.register(  # type: ignore[attr-defined]
        [
            CHEZMOI_BIN_ARGV,
            "--no-tty",
            "--no-pager",
            "--color=off",
            "--progress=false",
            "--source",
            str(tmp_path),
            "init",
        ],
        stdout=b"",
    )
    fake_process.register(  # type: ignore[attr-defined]
        [
            CHEZMOI_BIN_ARGV,
            "--no-tty",
            "--no-pager",
            "--color=off",
            "--progress=false",
            "--source",
            str(tmp_path),
            "apply",
        ],
        stdout=b"",
    )
    with (
        patch(
            "acap_dotfiles.commands.restore.discover_binary",
            return_value=CHEZMOI_BIN,
        ),
        patch("acap_dotfiles.commands.restore._is_tty", return_value=True),
    ):
        result = CliRunner().invoke(main, ["restore"])
    assert result.exit_code == 0


def test_restore_force_flag_passes_force_to_apply(
    fake_process: object, tmp_path: Path, monkeypatch: object
) -> None:
    """`dots restore --force` → passes --force to chezmoi apply."""
    monkeypatch.setenv("ACAP_DOTFILES_HOME", str(tmp_path))  # type: ignore[attr-defined]
    fake_process.register(  # type: ignore[attr-defined]
        [
            CHEZMOI_BIN_ARGV,
            "--no-tty",
            "--no-pager",
            "--color=off",
            "--progress=false",
            "--source",
            str(tmp_path),
            "init",
        ],
        stdout=b"",
    )
    fake_process.register(  # type: ignore[attr-defined]
        [
            CHEZMOI_BIN_ARGV,
            "--no-tty",
            "--no-pager",
            "--color=off",
            "--progress=false",
            "--source",
            str(tmp_path),
            "apply",
            "--force",
        ],
        stdout=b"",
    )
    with (
        patch(
            "acap_dotfiles.commands.restore.discover_binary",
            return_value=CHEZMOI_BIN,
        ),
        patch("acap_dotfiles.commands.restore._is_tty", return_value=True),
    ):
        result = CliRunner().invoke(main, ["restore", "--force"])
    assert result.exit_code == 0


def test_restore_non_tty_auto_injects_force_and_writes_stub(
    fake_process: object, tmp_path: Path, monkeypatch: object
) -> None:
    """Non-TTY → auto-injects --force, writes stub chezmoi.toml when missing."""
    monkeypatch.setenv("ACAP_DOTFILES_HOME", str(tmp_path))  # type: ignore[attr-defined]
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))  # type: ignore[attr-defined]
    fake_process.register(  # type: ignore[attr-defined]
        [
            CHEZMOI_BIN_ARGV,
            "--no-tty",
            "--no-pager",
            "--color=off",
            "--progress=false",
            "--source",
            str(tmp_path),
            "init",
        ],
        stdout=b"",
    )
    fake_process.register(  # type: ignore[attr-defined]
        [
            CHEZMOI_BIN_ARGV,
            "--no-tty",
            "--no-pager",
            "--color=off",
            "--progress=false",
            "--source",
            str(tmp_path),
            "apply",
            "--force",
        ],
        stdout=b"",
    )
    with (
        patch(
            "acap_dotfiles.commands.restore.discover_binary",
            return_value=CHEZMOI_BIN,
        ),
        patch("acap_dotfiles.commands.restore._is_tty", return_value=False),
    ):
        result = CliRunner().invoke(main, ["restore"])
    assert result.exit_code == 0
    stub_path = fake_home / ".config" / "chezmoi" / "chezmoi.toml"
    assert stub_path.is_file(), "non-TTY should write stub chezmoi.toml"
    content = stub_path.read_text()
    assert "[data]" in content
    # Codex round-4 P2: stub must include root-level sourceDir so subsequent
    # direct chezmoi calls (e.g. `dots status` → `chezmoi managed`) resolve to
    # cfg.home instead of chezmoi's default ~/.local/share/chezmoi.
    assert f'sourceDir = "{tmp_path}"' in content
    # And it must come BEFORE the [data] table (TOML root keys must precede tables).
    assert content.index("sourceDir") < content.index("[data]")


def test_restore_dry_run_passes_dry_run_to_chezmoi(
    fake_process: object, tmp_path: Path, monkeypatch: object
) -> None:
    """`dots --dry-run restore` must inject --dry-run into both init and apply.

    Regression test for the codex P2 finding on `dots restore`: previously the
    Wrapper was constructed without dry_run, so the safety flag was silently
    dropped. apply/update/backup pass it through; restore must too.
    """
    monkeypatch.setenv("ACAP_DOTFILES_HOME", str(tmp_path))  # type: ignore[attr-defined]
    fake_process.register(  # type: ignore[attr-defined]
        [
            CHEZMOI_BIN_ARGV,
            "--no-tty",
            "--no-pager",
            "--color=off",
            "--progress=false",
            "--source",
            str(tmp_path),
            "init",
            "--dry-run",
        ],
        stdout=b"",
    )
    fake_process.register(  # type: ignore[attr-defined]
        [
            CHEZMOI_BIN_ARGV,
            "--no-tty",
            "--no-pager",
            "--color=off",
            "--progress=false",
            "--source",
            str(tmp_path),
            "apply",
            "--dry-run",
        ],
        stdout=b"",
    )
    with (
        patch(
            "acap_dotfiles.commands.restore.discover_binary",
            return_value=CHEZMOI_BIN,
        ),
        patch("acap_dotfiles.commands.restore._is_tty", return_value=True),
    ):
        result = CliRunner().invoke(main, ["--dry-run", "restore"])
    assert result.exit_code == 0


def test_restore_stub_chezmoi_toml_contains_required_keys(
    fake_process: object, tmp_path: Path, monkeypatch: object
) -> None:
    """Non-TTY stub chezmoi.toml must populate every key the templates dereference.

    Regression test for the codex P1 finding on `dots restore`: previously the
    stub only set ``email``, but repo templates dereference ``.pkgmgr`` /
    ``.name`` / ``.isWindows`` / ``.hasOp`` / ``.isLinux`` / ``.isDarwin`` /
    ``.isWSL`` / ``.opSignedIn`` / ``.osid`` / ``.arch`` / ``.hostname`` /
    ``.personal``, causing ``chezmoi apply --force`` to abort with template
    errors on a fresh CI host.
    """
    monkeypatch.setenv("ACAP_DOTFILES_HOME", str(tmp_path))  # type: ignore[attr-defined]
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))  # type: ignore[attr-defined]
    fake_process.register(  # type: ignore[attr-defined]
        [
            CHEZMOI_BIN_ARGV,
            "--no-tty",
            "--no-pager",
            "--color=off",
            "--progress=false",
            "--source",
            str(tmp_path),
            "init",
        ],
        stdout=b"",
    )
    fake_process.register(  # type: ignore[attr-defined]
        [
            CHEZMOI_BIN_ARGV,
            "--no-tty",
            "--no-pager",
            "--color=off",
            "--progress=false",
            "--source",
            str(tmp_path),
            "apply",
            "--force",
        ],
        stdout=b"",
    )
    with (
        patch(
            "acap_dotfiles.commands.restore.discover_binary",
            return_value=CHEZMOI_BIN,
        ),
        patch("acap_dotfiles.commands.restore._is_tty", return_value=False),
    ):
        result = CliRunner().invoke(main, ["restore"])
    assert result.exit_code == 0
    stub_path = fake_home / ".config" / "chezmoi" / "chezmoi.toml"
    content = stub_path.read_text()
    # All keys the chezmoi templates dereference must be present
    for key in (
        "email",
        "name",
        "hostname",
        "personal",
        "osid",
        "arch",
        "isLinux",
        "isDarwin",
        "isWindows",
        "isWSL",
        "pkgmgr",
        "hasOp",
        "opSignedIn",
    ):
        assert f"{key} =" in content, f"stub chezmoi.toml is missing key: {key}"
    # Booleans must serialize as bare true/false (chezmoi rejects "true" / "false" strings)
    assert "isLinux = true" in content or "isLinux = false" in content
    assert "hasOp = true" in content or "hasOp = false" in content


def test_restore_non_tty_skips_init_when_stub_written(
    fake_process: object, tmp_path: Path, monkeypatch: object
) -> None:
    """Non-TTY → skip `chezmoi init` once the stub config is in place.

    Regression test for the codex P1 finding: even after the richer stub,
    `chezmoi init` re-renders ``.chezmoi.toml.tmpl`` which contains
    ``promptStringOnce`` calls that fail with EOF on stdin in non-TTY
    contexts. Expectation: the command writes the stub, then jumps straight
    to ``apply --force`` — `init` is never invoked. Verified by registering
    ONLY the apply call with fake_process; if init runs, fake_process raises
    ``ProcessNotRegisteredError`` and the test fails loudly.
    """
    monkeypatch.setenv("ACAP_DOTFILES_HOME", str(tmp_path))  # type: ignore[attr-defined]
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))  # type: ignore[attr-defined]
    # Note: NO init registration. If init runs, pytest-subprocess raises.
    fake_process.register(  # type: ignore[attr-defined]
        [
            CHEZMOI_BIN_ARGV,
            "--no-tty",
            "--no-pager",
            "--color=off",
            "--progress=false",
            "--source",
            str(tmp_path),
            "apply",
            "--force",
        ],
        stdout=b"",
    )
    with (
        patch(
            "acap_dotfiles.commands.restore.discover_binary",
            return_value=CHEZMOI_BIN,
        ),
        patch("acap_dotfiles.commands.restore._is_tty", return_value=False),
    ):
        result = CliRunner().invoke(main, ["restore"])
    assert result.exit_code == 0
    stub_path = fake_home / ".config" / "chezmoi" / "chezmoi.toml"
    assert stub_path.is_file(), "non-TTY should write stub chezmoi.toml"


def test_restore_missing_chezmoi_binary_exits_2(tmp_path: Path, monkeypatch: object) -> None:
    """Missing chezmoi binary → exit 2."""
    monkeypatch.setenv("ACAP_DOTFILES_HOME", str(tmp_path))  # type: ignore[attr-defined]
    from acap_dotfiles.core.chezmoi import ChezmoiError

    with patch(
        "acap_dotfiles.commands.restore.discover_binary",
        side_effect=ChezmoiError("chezmoi binary not found"),
    ):
        result = CliRunner().invoke(main, ["restore"])
    assert result.exit_code == 2


def test_restore_custom_acap_dotfiles_home_overrides_source(
    fake_process: object, tmp_path: Path, monkeypatch: object
) -> None:
    """ACAP_DOTFILES_HOME custom → --source overrides default."""
    custom_home = tmp_path / "custom-dots-home"
    custom_home.mkdir()
    monkeypatch.setenv("ACAP_DOTFILES_HOME", str(custom_home))  # type: ignore[attr-defined]
    fake_process.register(  # type: ignore[attr-defined]
        [
            CHEZMOI_BIN_ARGV,
            "--no-tty",
            "--no-pager",
            "--color=off",
            "--progress=false",
            "--source",
            str(custom_home),
            "init",
        ],
        stdout=b"",
    )
    fake_process.register(  # type: ignore[attr-defined]
        [
            CHEZMOI_BIN_ARGV,
            "--no-tty",
            "--no-pager",
            "--color=off",
            "--progress=false",
            "--source",
            str(custom_home),
            "apply",
        ],
        stdout=b"",
    )
    with (
        patch(
            "acap_dotfiles.commands.restore.discover_binary",
            return_value=CHEZMOI_BIN,
        ),
        patch("acap_dotfiles.commands.restore._is_tty", return_value=True),
    ):
        result = CliRunner().invoke(main, ["restore"])
    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# PR #20 deferred P2 regression tests
# ---------------------------------------------------------------------------


def test_stub_chezmoi_toml_windows_path_produces_valid_toml() -> None:
    """PR #20 deferred P2 #1: Windows `sourceDir` must round-trip through tomllib.

    Raw backslashes in a TOML basic-string trigger escape processing
    (`\\U` → unicode escape, `\\n` → newline). Before the fix, a path like
    `C:\\Users\\me\\.files` produced invalid TOML that either failed to
    parse or silently mangled the path. Regression test: the serialized
    stub must parse cleanly AND the parsed `sourceDir` must equal the
    input string character-for-character.
    """
    from acap_dotfiles.commands.restore import _stub_chezmoi_toml

    win_path = PureWindowsPath(r"C:\Users\me\.files")
    content = _stub_chezmoi_toml(win_path)  # type: ignore[arg-type]
    parsed = tomllib.loads(content)
    assert parsed["sourceDir"] == str(win_path)


def test_stub_chezmoi_toml_path_with_quotes_produces_valid_toml(
    tmp_path: Path,
) -> None:
    """Edge case alongside P2 #1: literal double-quotes in a path must not
    break TOML parsing either (basic-string escape handling)."""
    from acap_dotfiles.commands.restore import _stub_chezmoi_toml

    weird_path = tmp_path / 'dir"with"quotes'
    weird_path.mkdir()
    content = _stub_chezmoi_toml(weird_path)
    parsed = tomllib.loads(content)
    assert parsed["sourceDir"] == str(weird_path)


def test_platform_data_detects_wsl_from_proc_version(monkeypatch: object, tmp_path: Path) -> None:
    """PR #20 deferred P2 #2: WSL hosts must report `isWSL=True`.

    Repo templates gate on `(.isLinux and not .isWSL)` — e.g.
    `run_once_after_52-setup-zsh.sh.tmpl` which only runs on native Linux.
    Without WSL detection, WSL hosts running `dots restore` non-interactively
    hit the native-linux-only branch and try to modify `/etc/zsh/zshenv`.
    Fix: read `/proc/version`, match `Microsoft` / `WSL` case-insensitively.
    """
    from acap_dotfiles.commands import restore as restore_module

    proc_version = tmp_path / "version"
    proc_version.write_text("Linux version 5.15.153.1-microsoft-standard-WSL2 (x86_64)\n")
    monkeypatch.setattr(  # type: ignore[attr-defined]
        restore_module, "_PROC_VERSION_PATH", proc_version
    )
    monkeypatch.setattr(  # type: ignore[attr-defined]
        restore_module._platform, "system", lambda: "Linux"
    )
    data = restore_module._platform_data()
    assert data["isWSL"] is True
    assert data["isLinux"] is True


def test_platform_data_native_linux_keeps_wsl_false(monkeypatch: object, tmp_path: Path) -> None:
    """Negative case: native Linux kernel must NOT be flagged as WSL."""
    from acap_dotfiles.commands import restore as restore_module

    proc_version = tmp_path / "version"
    proc_version.write_text("Linux version 6.8.0-51-generic (buildd@lcy02-amd64-071)\n")
    monkeypatch.setattr(  # type: ignore[attr-defined]
        restore_module, "_PROC_VERSION_PATH", proc_version
    )
    monkeypatch.setattr(  # type: ignore[attr-defined]
        restore_module._platform, "system", lambda: "Linux"
    )
    data = restore_module._platform_data()
    assert data["isWSL"] is False


def test_platform_data_wsl_detection_tolerates_missing_proc_version(
    monkeypatch: object, tmp_path: Path
) -> None:
    """Non-Linux hosts (macOS, Windows) have no `/proc/version`; the detector
    must fall back to `isWSL=False` without raising."""
    from acap_dotfiles.commands import restore as restore_module

    missing = tmp_path / "nope"  # not created
    monkeypatch.setattr(  # type: ignore[attr-defined]
        restore_module, "_PROC_VERSION_PATH", missing
    )
    monkeypatch.setattr(  # type: ignore[attr-defined]
        restore_module._platform, "system", lambda: "Darwin"
    )
    data = restore_module._platform_data()
    assert data["isWSL"] is False


def test_stub_chezmoi_toml_path_with_backslashes_and_quotes_together(
    tmp_path: Path,
) -> None:
    """pr-test-analyzer MEDIUM #1: paths with BOTH backslashes AND quotes must
    round-trip. Locks in the "use a real TOML serializer, never hand-roll"
    invariant — a hand-rolled escape that forgets either axis would regress."""
    from acap_dotfiles.commands.restore import _stub_chezmoi_toml

    # Construct a string that contains both escape-sensitive characters.
    # Use PureWindowsPath for the backslash side (Linux-host safe) and
    # then join a quote-bearing segment via str manipulation so the path
    # object stays valid — `PureWindowsPath` accepts quotes in segments.
    weird = PureWindowsPath(r'C:\Users\me\dir"quoted"') / ".files"
    content = _stub_chezmoi_toml(weird)  # type: ignore[arg-type]
    parsed = tomllib.loads(content)
    assert parsed["sourceDir"] == str(weird)


def test_detect_wsl_is_case_insensitive_for_microsoft_capital_m(
    monkeypatch: object, tmp_path: Path
) -> None:
    """pr-test-analyzer MEDIUM #3: WSL1's classic kernel marker uses capital
    `Microsoft` (`Microsoft@...` in the compiler signature). The detector
    must match regardless of case."""
    from acap_dotfiles.commands import restore as restore_module

    proc_version = tmp_path / "version"
    proc_version.write_text(
        "Linux version 4.4.0-19041-Microsoft (Microsoft@Microsoft.com) (gcc version 5.4.0) #2311\n"
    )
    monkeypatch.setattr(  # type: ignore[attr-defined]
        restore_module, "_PROC_VERSION_PATH", proc_version
    )
    monkeypatch.setattr(  # type: ignore[attr-defined]
        restore_module._platform, "system", lambda: "Linux"
    )
    data = restore_module._platform_data()
    assert data["isWSL"] is True


def test_platform_data_non_linux_host_with_wsl_marker_is_not_flagged(
    monkeypatch: object, tmp_path: Path
) -> None:
    """pr-test-analyzer MEDIUM #2: a Darwin / Windows host that happens to have
    a `/proc/version` shim (Cygwin, Git Bash, sandbox runtime) containing
    WSL markers must still report `isWSL=False`, because the code gates on
    `is_linux and _detect_wsl()`. Pins the Linux-gate explicitly."""
    from acap_dotfiles.commands import restore as restore_module

    proc_version = tmp_path / "version"
    proc_version.write_text("Linux version 5.15.153.1-microsoft-standard-WSL2\n")
    monkeypatch.setattr(  # type: ignore[attr-defined]
        restore_module, "_PROC_VERSION_PATH", proc_version
    )
    monkeypatch.setattr(  # type: ignore[attr-defined]
        restore_module._platform, "system", lambda: "Darwin"
    )
    data = restore_module._platform_data()
    assert data["isWSL"] is False
    assert data["isLinux"] is False
