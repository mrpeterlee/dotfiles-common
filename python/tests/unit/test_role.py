from pathlib import Path

from acap_dotfiles.core.role import (
    VALID_ROLES,
    RoleError,
    get_role,
    set_role,
)


def test_get_role_returns_none_when_unset(tmp_path: Path) -> None:
    assert get_role(tmp_path / "role.toml") is None


def test_set_then_get_role_roundtrip(tmp_path: Path) -> None:
    set_role(tmp_path / "role.toml", "acap")
    assert get_role(tmp_path / "role.toml") == "acap"


def test_set_role_atomic_write(tmp_path: Path) -> None:
    p = tmp_path / "role.toml"
    set_role(p, "tapai")
    assert p.read_text().strip() == 'role = "tapai"'


def test_invalid_role_rejected(tmp_path: Path) -> None:
    import pytest

    with pytest.raises(RoleError):
        set_role(tmp_path / "role.toml", "not-a-role")


def test_valid_roles_includes_all_expected() -> None:
    # Sanity: the constant exposes the expected role set
    assert frozenset({"acap", "tapai", "personal"}) == VALID_ROLES
