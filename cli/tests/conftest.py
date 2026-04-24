"""Shared pytest fixtures for unit tests."""

import pytest

# pytest-subprocess provides the fake_process fixture; just import the marker
pytest_plugins = ["pytest_subprocess"]


@pytest.fixture(autouse=True)
def _no_color(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force NO_COLOR for all tests so output assertions are stable."""
    monkeypatch.setenv("NO_COLOR", "1")
