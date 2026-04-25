"""Unit tests for ``acap_dotfiles.core.inventory``.

Covers both the P3-era surface (``load_hosts``, ``render_ssh_config``,
``.yml``/``.yaml`` discovery, role filter) — which keeps working through the
new ``@property`` accessors — and the P4 nested schema additions
(``Addresses``, ``SSH``, ``Headscale``, ``TunnelMonitor``, namespaced
sub-maps, ``schema_version``).

Pre-existing P3 bug rationale: P3's ``dots ssh render`` was never smoke-tested
against the real ``~/acap/inventory/hosts/*.yml`` files, which use the nested
schema. Loading any one of them under the old flat-shape model would raise
``KeyError: 'addr'``. ``test_load_real_inventory_files`` is the regression
guard that catches a future drift.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from acap_dotfiles.core.inventory import (
    Headscale,
    Host,
    TunnelMonitor,
    load_hosts,
    render_ssh_config,
)

# ----------------------------------------------------------------------
# P3-era surface (must stay green via @property accessors)
# ----------------------------------------------------------------------


def test_load_hosts_empty_dir_returns_empty_list(tmp_path: Path) -> None:
    assert load_hosts(tmp_path) == []


def test_load_hosts_single_host_uses_defaults(tmp_path: Path) -> None:
    """Minimal nested host — only ``name`` + ``addresses.public`` set."""
    (tmp_path / "alpha.yaml").write_text("name: alpha\naddresses:\n  public: 10.0.0.1\n")
    hosts = load_hosts(tmp_path)
    assert len(hosts) == 1
    h = hosts[0]
    assert h.name == "alpha"
    assert h.addr == "10.0.0.1"
    assert h.port == 22
    assert h.user is None
    assert h.identity_file is None
    assert h.role == "personal"
    assert h.tags == ()


def test_load_hosts_multiple_returns_sorted_by_name(tmp_path: Path) -> None:
    """Loader sorts by ``Host.name`` for deterministic downstream output."""
    (tmp_path / "zeta.yaml").write_text("name: zeta\naddresses:\n  public: 10.0.0.3\n")
    (tmp_path / "alpha.yaml").write_text("name: alpha\naddresses:\n  public: 10.0.0.1\n")
    (tmp_path / "mike.yaml").write_text("name: mike\naddresses:\n  public: 10.0.0.2\n")
    hosts = load_hosts(tmp_path)
    assert [h.name for h in hosts] == ["alpha", "mike", "zeta"]


def test_render_ssh_config_emits_port_when_non_default() -> None:
    hosts = [
        Host(
            name="alpha",
            addresses={"public": "10.0.0.1"},  # type: ignore[arg-type]
            ssh={"port": 2222},  # type: ignore[arg-type]
        )
    ]
    out = render_ssh_config(hosts)
    assert "Host alpha" in out
    assert "    HostName 10.0.0.1" in out
    assert "    Port 2222" in out
    # default-port host omits Port line
    hosts2 = [Host(name="beta", addresses={"public": "10.0.0.2"})]  # type: ignore[arg-type]
    out2 = render_ssh_config(hosts2)
    assert "Port" not in out2


def test_load_hosts_picks_up_yml_alongside_yaml(tmp_path: Path) -> None:
    """``*.yml`` files must load alongside ``*.yaml`` (P3 codex-P2 regression)."""
    (tmp_path / "alpha.yaml").write_text("name: alpha\naddresses:\n  public: 10.0.0.1\n")
    (tmp_path / "beta.yml").write_text("name: beta\naddresses:\n  public: 10.0.0.2\n")
    hosts = load_hosts(tmp_path)
    names = sorted(h.name for h in hosts)
    assert names == ["alpha", "beta"]


def test_render_ssh_config_role_filter_excludes_other_roles(tmp_path: Path) -> None:
    """``role`` is now derived from ``groups``; tailscale_nodes → acap."""
    (tmp_path / "alpha.yaml").write_text(
        "name: alpha\naddresses:\n  public: 10.0.0.1\ngroups: [tailscale_nodes]\n"
    )
    (tmp_path / "beta.yaml").write_text(
        "name: beta\naddresses:\n  public: 10.0.0.2\n"  # no groups → role=personal
    )
    hosts = load_hosts(tmp_path)
    out = render_ssh_config(hosts, role_filter="acap")
    assert "Host alpha" in out
    assert "Host beta" not in out


# ----------------------------------------------------------------------
# P4 namespaced sub-maps + nested schema
# ----------------------------------------------------------------------


def test_load_host_with_namespaced_submaps(tmp_path: Path) -> None:
    """Full nested-schema host with all P4 sub-maps populated."""
    yaml_file = tmp_path / "acap-sg-prod-1.yaml"
    yaml_file.write_text(
        """
schema_version: 1
name: acap-sg-prod-1
fqdn: sg-prod-1.acap.cc
hostnames:
  - sg-prod-1
addresses:
  public: sg-prod-1.acap.cc
  lan: 10.1.1.100
  tailscale: 100.64.0.2
ssh:
  port: 55555
  user: peter
  identity: peter_acap
  proxy_jump: null
provider: bare-metal
region: sg
role_tag: prod
roles: [trading, github_runner]
groups: [bare_metal, trading_servers, sg, tailscale_nodes]
headscale:
  tags: ["tag:acap", "tag:bare-metal"]
  routes: ["10.1.1.0/24"]
tunnel_monitor:
  role: relay
  port_txt_fqdn: r1.tunnel.acap.cc
ansible:
  extra_vars:
    alloy_loki_endpoint: https://loki.acap.cc
"""
    )
    hosts = load_hosts(tmp_path)
    assert len(hosts) == 1
    h = hosts[0]
    assert h.schema_version == 1
    # Nested schema accessors
    assert h.addresses.lan == "10.1.1.100"
    assert h.addresses.public == "sg-prod-1.acap.cc"
    assert h.addresses.tailscale == "100.64.0.2"
    assert h.ssh.port == 55555
    assert h.ssh.user == "peter"
    assert h.ssh.identity == "peter_acap"
    # P3 backward-compat properties
    assert h.addr == "10.1.1.100"  # lan wins
    assert h.port == 55555
    assert h.user == "peter"
    assert h.identity_file == "~/.ssh/peter_acap"
    assert h.role == "acap"  # derived from groups (tailscale_nodes)
    # P4 namespaced sub-maps
    assert isinstance(h.headscale, Headscale)
    assert h.headscale.tags == ["tag:acap", "tag:bare-metal"]
    assert h.headscale.routes == ["10.1.1.0/24"]
    assert isinstance(h.tunnel_monitor, TunnelMonitor)
    assert h.tunnel_monitor.role == "relay"
    assert h.tunnel_monitor.port_txt_fqdn == "r1.tunnel.acap.cc"
    assert h.ansible == {"extra_vars": {"alloy_loki_endpoint": "https://loki.acap.cc"}}


def test_load_host_without_submaps(tmp_path: Path) -> None:
    """Minimal nested host — no P4 sub-maps, only required nested fields."""
    yaml_file = tmp_path / "h.yaml"
    yaml_file.write_text(
        """
name: h
addresses:
  public: 1.2.3.4
ssh:
  port: 22
  user: x
"""
    )
    hosts = load_hosts(tmp_path)
    h = hosts[0]
    assert h.headscale is None
    assert h.tunnel_monitor is None
    assert h.ansible == {}
    assert h.schema_version == 1  # default
    assert h.addr == "1.2.3.4"  # public falls through (no lan, no tailscale)
    assert h.role == "personal"  # no group hints


def test_invalid_tunnel_role_rejected(tmp_path: Path) -> None:
    """Pydantic ``Literal`` rejects unknown ``tunnel_monitor.role`` values."""
    yaml_file = tmp_path / "h.yaml"
    yaml_file.write_text(
        """
name: h
addresses:
  public: 1.2.3.4
ssh:
  user: x
groups: [tailscale_nodes]
tunnel_monitor:
  role: BOGUS
  port_txt_fqdn: x.example.com
"""
    )
    with pytest.raises(ValidationError):
        load_hosts(tmp_path)


def test_extra_top_level_key_rejected(tmp_path: Path) -> None:
    """``extra='forbid'`` catches typos in real inventory files."""
    yaml_file = tmp_path / "h.yaml"
    yaml_file.write_text("name: h\naddresses:\n  public: 1.1.1.1\nbogus_key: oops\n")
    with pytest.raises(ValidationError):
        load_hosts(tmp_path)


def test_addr_property_picks_lan_first(tmp_path: Path) -> None:
    """``addr`` fallback chain: lan > tailscale > private > public > fqdn > name."""
    cases = [
        # (addresses dict, fqdn, expected addr)
        (
            {"lan": "10.1.1.1", "public": "p", "tailscale": "t", "private": "172.31.0.1"},
            "f",
            "10.1.1.1",
        ),
        ({"tailscale": "100.64.0.5", "private": "172.31.0.1", "public": "p"}, "f", "100.64.0.5"),
        ({"private": "172.31.0.1", "public": "p.example.com"}, "f", "172.31.0.1"),
        ({"public": "p.example.com"}, "f.example.com", "p.example.com"),
        ({}, "fallback.example.com", "fallback.example.com"),
        ({}, None, "h"),  # nothing → host name
    ]
    for i, (addrs, fqdn, expected) in enumerate(cases):
        yaml_file = tmp_path / f"h{i}.yaml"
        if addrs:
            addr_block = "\n".join(f"  {k}: {v}" for k, v in addrs.items())
            addr_section = f"addresses:\n{addr_block}\n"
        else:
            addr_section = ""
        fqdn_line = f"fqdn: {fqdn}\n" if fqdn else ""
        yaml_file.write_text(f"name: h\n{fqdn_line}{addr_section}")
        h = load_hosts(tmp_path)[0]
        assert h.addr == expected, f"case {i}: got {h.addr!r}, want {expected!r}"
        yaml_file.unlink()


def test_role_property_derives_from_groups(tmp_path: Path) -> None:
    """``role`` heuristic: tailscale_nodes / acap-* → acap; tapai-* → tapai."""
    cases = [
        ([], "personal"),
        (["tailscale_nodes"], "acap"),
        (["acap_servers", "sg"], "acap"),
        (["tapai_servers"], "tapai"),
        (["random_group"], "personal"),
    ]
    for i, (groups, expected_role) in enumerate(cases):
        yaml_file = tmp_path / f"h{i}.yaml"
        groups_line = f"groups: [{', '.join(groups)}]\n" if groups else ""
        yaml_file.write_text(f"name: h\naddresses:\n  public: 1.1.1.1\n{groups_line}")
        h = load_hosts(tmp_path)[0]
        assert h.role == expected_role, (
            f"case {i}: groups={groups} → got {h.role!r}, want {expected_role!r}"
        )
        yaml_file.unlink()


def test_load_real_inventory_files() -> None:
    """Smoke: every checked-in inventory file in ``~/acap/inventory/hosts/`` loads.

    Catches a pre-existing P3 bug — the loader assumed the flat shape and was
    never tested against real files. Skips when the inventory dir isn't
    available (CI runners without the acap checkout).
    """
    real_dir = Path("/home/peter/acap/inventory/hosts")
    if not real_dir.is_dir():
        pytest.skip("acap inventory not checked out at /home/peter/acap")
    hosts = load_hosts(real_dir)
    assert len(hosts) >= 6, f"expected at least 6 host files, got {len(hosts)}"
    # Spot-check a known host
    by_name = {h.name: h for h in hosts}
    assert "acap-sg-prod-1" in by_name, sorted(by_name)
    sg = by_name["acap-sg-prod-1"]
    assert sg.addr == "10.1.1.100"
    assert sg.port == 55555
    assert sg.user == "peter"
    assert sg.role == "acap"


# ----------------------------------------------------------------------
# P4 codex round-2 regressions
# ----------------------------------------------------------------------


def test_role_picks_acap_from_canonical_hostname_when_groups_lack_tailscale() -> None:
    """Hosts like ``acap-jp-ingress-1`` (groups = [tunnel_servers, reality_ingress, jp])
    must classify as ``acap`` even though no group starts with ``acap`` and
    ``tailscale_nodes`` is absent. Codex round-2 P1.
    """
    h = Host(
        name="acap-jp-ingress-1",
        addresses={"public": "202.182.115.158"},  # type: ignore[arg-type]
        groups=["tunnel_servers", "reality_ingress", "jp"],
    )
    assert h.role == "acap"


def test_role_picks_tapai_from_canonical_hostname() -> None:
    """``tapai-`` prefix → ``tapai`` even when ``groups[]`` carries no tapai-* hint."""
    h = Host(
        name="tapai-sg-admin-1",
        addresses={"public": "1.2.3.4"},  # type: ignore[arg-type]
        groups=["admin", "sg"],
    )
    assert h.role == "tapai"


def test_load_real_inventory_files_all_acap() -> None:
    """All 7 ``acap-*.yml`` files in the real inventory must classify as ``acap``.

    This is the regression guard for the codex round-2 P1: previously
    ``acap-jp-ingress-1`` / ``acap-sg-egress-1`` / ``acap-sg-ingress-{1,2}``
    fell through to ``personal`` because their ``groups[]`` lacks
    ``tailscale_nodes`` and any ``acap*`` prefix.
    """
    real_dir = Path("/home/peter/acap/inventory/hosts")
    if not real_dir.is_dir():
        pytest.skip("acap inventory not checked out at /home/peter/acap")
    hosts = load_hosts(real_dir)
    acap_named = [h for h in hosts if h.name.startswith("acap-") or h.name == "acap"]
    assert len(acap_named) >= 7, f"expected ≥7 acap-* hosts, got {len(acap_named)}"
    misclassified = [h.name for h in acap_named if h.role != "acap"]
    assert misclassified == [], (
        f"these acap-* hosts fell through to a non-acap role: {misclassified}"
    )


def test_render_emits_proxy_jump() -> None:
    """``ssh.proxy_jump`` must surface as ``ProxyJump <hostname>`` in the SSH config.

    Codex round-2 P2: the field was loaded from yaml but silently dropped at
    render time, leaving bastion-only hosts unusable.
    """
    h = Host(
        name="behind-bastion",
        addresses={"public": "10.99.0.1"},  # type: ignore[arg-type]
        ssh={"user": "peter", "proxy_jump": "bastion.example.com"},  # type: ignore[arg-type]
    )
    out = render_ssh_config([h])
    assert "Host behind-bastion" in out
    assert "    ProxyJump bastion.example.com" in out


def test_render_emits_legacy_hostname_aliases() -> None:
    """``hostnames[]`` must merge into the OpenSSH multi-host ``Host`` line.

    Codex round-2 P1 (from plan reviewer): without this, T11's legacy-bookmark
    preservation breaks during the rename window — e.g. ``ssh sg-prod-1`` would
    no longer match the rendered config because only ``Host acap-sg-prod-1``
    is emitted.
    """
    h = Host(
        name="acap-sg-prod-1",
        hostnames=["sg-prod-1"],
        addresses={"lan": "10.1.1.100"},  # type: ignore[arg-type]
    )
    out = render_ssh_config([h])
    assert "Host acap-sg-prod-1 sg-prod-1" in out
    # multi-alias case: both aliases on the same Host line
    h2 = Host(
        name="acap-sg-prod-1",
        hostnames=["sg-prod-1", "sg1"],
        addresses={"lan": "10.1.1.100"},  # type: ignore[arg-type]
    )
    out2 = render_ssh_config([h2])
    assert "Host acap-sg-prod-1 sg-prod-1 sg1" in out2
    # zero-aliases case is unchanged: just ``Host <name>``
    h3 = Host(name="solo", addresses={"public": "1.1.1.1"})  # type: ignore[arg-type]
    out3 = render_ssh_config([h3])
    assert "Host solo\n" in out3
