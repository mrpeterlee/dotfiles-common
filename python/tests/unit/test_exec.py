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
