"""Shared pytest fixtures for unit tests."""

import platform as _platform
from pathlib import Path

import pytest

# pytest-subprocess provides the fake_process fixture; just import the marker
pytest_plugins = ["pytest_subprocess"]


# Platform-native representations of the canonical chezmoi binary path.
#
# Production code (`Wrapper.build_argv`) builds argv via `str(self.binary)`,
# which on Windows turns a `Path("/usr/bin/chezmoi")` into the backslash
# form `\usr\bin\chezmoi`. `pytest_subprocess.fake_process.register([...])`
# matches the registered argv against the spawned argv exactly — so test
# files that register `"/usr/bin/chezmoi"` (forward slash) miss on Windows
# and raise `ProcessNotRegisteredError`.
#
# Use these constants in every test:
#   - `CHEZMOI_BIN` for `discover_binary` mock return values
#   - `CHEZMOI_BIN_ARGV` as the first element of `fake_process.register([...])`
# Both produce the platform's native form, so tests pass identically on
# Linux/macOS (forward slash) and Windows (backslash).
CHEZMOI_BIN: Path = Path("/usr/bin/chezmoi")
CHEZMOI_BIN_ARGV: str = str(CHEZMOI_BIN)


@pytest.fixture(autouse=True)
def _no_color(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force NO_COLOR for all tests so output assertions are stable."""
    monkeypatch.setenv("NO_COLOR", "1")


@pytest.fixture(autouse=True)
def _stable_platform_uname(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pin ``platform.uname()`` and its companions to a static Linux-shaped
    result so tests are deterministic across runners.

    On Windows ``platform.uname()`` subprocesses ``ver`` to read the OS
    release. ``pytest-subprocess`` strict-mode treats that as an
    unregistered call and raises ``ProcessNotRegisteredError("The process
    'ver' was not registered.")``, which broke every test that exercises
    ``acap_dotfiles.commands.restore._platform_data`` (transitively
    ``platform.system()`` etc).

    Codex round-1 P2: an earlier draft used
    ``fake_process.allow_unregistered(True)`` instead, which weakened
    ``test_restore_non_tty_skips_init_when_stub_written``'s
    "init-must-not-run" regression — an unregistered chezmoi-init call
    would silently pass through to the real binary if installed. Faking
    the platform module is narrower: it removes the offending stdlib
    subprocess at its source, leaving ``fake_process`` strict for every
    other call.

    Tests that need OS-specific behaviour (e.g. WSL detection) override
    these per-test by patching ``acap_dotfiles.commands.restore._platform``
    directly.
    """

    # Duck-typed uname result. Avoids `_platform.uname_result(...)` whose
    # constructor signature differs across Python versions (`processor`
    # field was removed in 3.13). The application code reads
    # `.system` / `.node` / `.machine` only — every other consumer uses
    # the dedicated functions which we patch separately below.
    class _FakeUname:
        system = "Linux"
        node = "test-host"
        release = "0.0.0-test"
        version = "#1"
        machine = "x86_64"

    monkeypatch.setattr(_platform, "uname", lambda: _FakeUname())
    monkeypatch.setattr(_platform, "system", lambda: "Linux")
    monkeypatch.setattr(_platform, "node", lambda: "test-host")
    monkeypatch.setattr(_platform, "machine", lambda: "x86_64")
