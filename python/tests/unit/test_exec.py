import sys

from acap_dotfiles.io.exec import stream


def test_stream_captures_stdout_and_stderr_separately() -> None:
    out_lines: list[str] = []
    err_lines: list[str] = []
    rc = stream(
        [sys.executable, "-c", "import sys; print('hi'); print('warn', file=sys.stderr)"],
        on_stdout=out_lines.append,
        on_stderr=err_lines.append,
    )
    assert rc == 0
    assert out_lines == ["hi"]
    assert err_lines == ["warn"]


def test_stream_propagates_nonzero_exit() -> None:
    rc = stream(
        [sys.executable, "-c", "import sys; sys.exit(42)"],
        on_stdout=lambda _: None,
        on_stderr=lambda _: None,
    )
    assert rc == 42


def test_stream_env_merges_with_os_environ() -> None:
    """Codex P2: passing `env={"FOO": "bar"}` must NOT wipe PATH/HOME/etc.

    Replacing instead of merging breaks long apply/update/init runs that
    rely on PATH, HOME, SSH_AUTH_SOCK, and credential tokens. This test
    asserts the child sees both the inherited PATH and the injected FOO.
    """
    out_lines: list[str] = []
    rc = stream(
        [
            sys.executable,
            "-c",
            "import os; print(os.environ.get('PATH', '<missing>')); "
            "print(os.environ.get('FOO', '<missing>'))",
        ],
        on_stdout=out_lines.append,
        on_stderr=lambda _: None,
        env={"FOO": "bar"},
    )
    assert rc == 0
    assert len(out_lines) == 2
    # PATH must be inherited from os.environ — proves merge, not replace
    assert out_lines[0] != "<missing>"
    assert out_lines[0] != ""
    # FOO must be the injected value — proves the override layer works
    assert out_lines[1] == "bar"
