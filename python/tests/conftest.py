"""Shared pytest fixtures for unit tests."""

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
def _allow_unregistered_subprocess(fake_process: object) -> None:  # type: ignore[no-untyped-def]
    """Let stdlib subprocess calls pass through pytest-subprocess.

    On Windows, ``platform.uname()`` (transitively called from
    ``platform.system()`` / ``platform.node()`` etc.) subprocesses ``ver``
    to read the OS release. With strict ``fake_process`` interception that
    raises ``ProcessNotRegisteredError("The process 'ver' was not
    registered.")`` and breaks every test that touches the platform module
    via ``acap_dotfiles.commands.restore._platform_data`` etc.

    Calls to chezmoi (and any other binary tests register explicitly) still
    hit the registered fakes — ``allow_unregistered`` only controls what
    happens to UNregistered calls. Letting them through to the real OS is
    the correct semantics for stdlib internals; only the chezmoi argv is
    subject to test assertions anyway.
    """
    fake_process.allow_unregistered(True)  # type: ignore[attr-defined]
