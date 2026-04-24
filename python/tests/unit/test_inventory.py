from pathlib import Path

from acap_dotfiles.core.inventory import Host, load_hosts, render_ssh_config


def test_load_hosts_empty_dir_returns_empty_list(tmp_path: Path) -> None:
    assert load_hosts(tmp_path) == []


def test_load_hosts_single_host_uses_defaults(tmp_path: Path) -> None:
    (tmp_path / "alpha.yaml").write_text("name: alpha\naddr: 10.0.0.1\n")
    hosts = load_hosts(tmp_path)
    assert hosts == [Host(name="alpha", addr="10.0.0.1")]
    h = hosts[0]
    assert h.port == 22
    assert h.user is None
    assert h.identity_file is None
    assert h.role == "personal"
    assert h.tags == ()


def test_load_hosts_multiple_returns_sorted_by_filename(tmp_path: Path) -> None:
    (tmp_path / "zeta.yaml").write_text("name: zeta\naddr: 10.0.0.3\n")
    (tmp_path / "alpha.yaml").write_text("name: alpha\naddr: 10.0.0.1\n")
    (tmp_path / "mike.yaml").write_text("name: mike\naddr: 10.0.0.2\n")
    hosts = load_hosts(tmp_path)
    assert [h.name for h in hosts] == ["alpha", "mike", "zeta"]


def test_render_ssh_config_emits_port_when_non_default() -> None:
    hosts = [Host(name="alpha", addr="10.0.0.1", port=2222)]
    out = render_ssh_config(hosts)
    assert "Host alpha" in out
    assert "    HostName 10.0.0.1" in out
    assert "    Port 2222" in out
    # default-port host omits Port line
    hosts2 = [Host(name="beta", addr="10.0.0.2")]
    out2 = render_ssh_config(hosts2)
    assert "Port" not in out2


def test_render_ssh_config_role_filter_excludes_other_roles() -> None:
    hosts = [
        Host(name="alpha", addr="10.0.0.1", role="acap"),
        Host(name="beta", addr="10.0.0.2", role="personal"),
    ]
    out = render_ssh_config(hosts, role_filter="acap")
    assert "Host alpha" in out
    assert "Host beta" not in out
