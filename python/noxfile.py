"""Nox sessions for matrix testing across Python versions."""

import nox


@nox.session(python=["3.11", "3.12", "3.13"])
def tests(session: nox.Session) -> None:
    session.install("-e", ".[dev]")
    session.run("pytest", "-q", "tests/unit/")


@nox.session(python="3.12")
def lint(session: nox.Session) -> None:
    session.install("ruff", "mypy", "-e", ".")
    session.run("ruff", "check", ".")
    session.run("ruff", "format", "--check", ".")
    session.run("mypy", "src/acap_dotfiles/core", "src/acap_dotfiles/io")


@nox.session(python="3.12")
def integration(session: nox.Session) -> None:
    session.install("-e", ".[dev]")
    session.run("pytest", "-q", "-m", "integration", "tests/integration/")
