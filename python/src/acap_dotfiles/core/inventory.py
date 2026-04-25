"""Inventory data model — single canonical Host shape used by dots, ac, and tp.

P3 introduced the basic loader for ``dots ssh render`` but assumed a flat
``addr/port/user`` yaml shape. The real inventory files at
``~/acap/inventory/hosts/*.yml`` use a **nested** schema
(``addresses.{public,lan,tailscale}``, ``ssh.{port,user,identity,proxy_jump}``,
``provider``, ``region``, ``role_tag``, ``roles[]``, ``groups[]``). This module
models the nested schema as the source of truth and exposes ``@property``
accessors (``addr``, ``port``, ``user``, ``identity_file``, ``role``, ``tags``)
so P3's ``render_ssh_config`` and every downstream renderer keep working.

P4 adds ``schema_version`` + namespaced sub-maps (``headscale``,
``tunnel_monitor``, ``ansible``) so ``render-ansible`` / ``render-headscale`` /
``render-tunnel-monitor`` can pull their tool-specific knobs from the same
per-host yaml file.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field


class Addresses(BaseModel):
    """Per-host network addresses. All optional; at least one is expected.

    ``lan`` is host-network (10.x / 192.168.x) reachable from the same physical
    LAN. ``private`` is cloud-private (e.g. AWS VPC 172.31.x) reachable from
    inside the same VPC. ``tailscale`` is the 100.64.x mesh address.
    ``public`` is the internet-facing FQDN/IP.
    """

    public: str | None = None
    lan: str | None = None
    private: str | None = None  # cloud-private (AWS VPC, etc.)
    tailscale: str | None = None

    model_config = ConfigDict(extra="forbid")


class SSH(BaseModel):
    """SSH connection params for the canonical (target-state) hostname."""

    port: int = 22
    user: str | None = None
    identity: str | None = None  # key NAME under ~/.ssh/, NOT a path
    proxy_jump: str | None = None

    model_config = ConfigDict(extra="forbid")


class Headscale(BaseModel):
    """Headscale ACL/policy config for a host."""

    tags: list[str] = Field(default_factory=list)  # e.g. ["tag:acap", "tag:bare-metal"]
    routes: list[str] = Field(default_factory=list)  # e.g. ["10.1.1.0/24"]

    model_config = ConfigDict(extra="forbid")


class TunnelMonitor(BaseModel):
    """CN-SG tunnel-monitor config for a host."""

    role: Literal["ingress", "egress", "relay", "client"]
    port_txt_fqdn: str  # FQDN whose TXT record carries the dynamic port

    model_config = ConfigDict(extra="forbid")


class Host(BaseModel):
    """Canonical per-host model. Loaded from ``inventory/hosts/<name>.yml``."""

    schema_version: int = 1

    # Identity
    name: str
    fqdn: str | None = None
    hostnames: list[str] = Field(default_factory=list)  # legacy aliases

    # Connection
    addresses: Addresses = Field(default_factory=Addresses)
    ssh: SSH = Field(default_factory=SSH)

    # Classification (drives ansible groups, dotfiles overlay, etc.)
    provider: str | None = None  # bare-metal | vultr | oracle | aws | ...
    region: str | None = None  # sg | jp | cn | us | ...
    role_tag: str | None = None  # prod | ingress | egress | admin | ...
    roles: list[str] = Field(default_factory=list)  # e.g. [trading, vm_host, ...]
    groups: list[str] = Field(default_factory=list)  # e.g. [tailscale_nodes, sg, ...]

    # P4 namespaced sub-maps — each consumer reads only its own key.
    headscale: Headscale | None = None
    tunnel_monitor: TunnelMonitor | None = None
    ansible: dict[str, dict[str, object]] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")  # reject unknown top-level keys

    # ------------------------------------------------------------------
    # Convenience accessors. Keep P3 callers (``render_ssh_config``)
    # working without rewriting them — and give P4 renderers a single
    # best-fit value rather than duplicating the fallback logic.
    # ------------------------------------------------------------------
    @property
    def addr(self) -> str:
        """Best-fit SSH-reachable address.

        Fallback chain: ``lan`` > ``tailscale`` > ``private`` > ``public`` >
        ``fqdn`` > ``name``. ``private`` (cloud-VPC) ranks above ``public`` so
        the same renderer works from inside or outside the VPC: callers running
        inside the VPC pick the cheap private hop, callers outside fall through
        to the public address.
        """
        return (
            self.addresses.lan
            or self.addresses.tailscale
            or self.addresses.private
            or self.addresses.public
            or self.fqdn
            or self.name
        )

    @property
    def port(self) -> int:
        """SSH port (alias for ``self.ssh.port``)."""
        return self.ssh.port

    @property
    def user(self) -> str | None:
        """SSH user (alias for ``self.ssh.user``)."""
        return self.ssh.user

    @property
    def identity_file(self) -> str | None:
        """Map ``ssh.identity`` (key name) to ``~/.ssh/<name>`` path for OpenSSH config."""
        return f"~/.ssh/{self.ssh.identity}" if self.ssh.identity else None

    @property
    def role(self) -> str:
        """Derive org-role from ``groups``.

        Heuristic: ``tailscale_nodes`` or any group starting with ``acap`` → ``acap``;
        any group starting with ``tapai`` → ``tapai``; else ``personal``. Tunable
        later if we add more orgs.
        """
        if "tailscale_nodes" in self.groups or any(g.startswith("acap") for g in self.groups):
            return "acap"
        if any(g.startswith("tapai") for g in self.groups):
            return "tapai"
        return "personal"

    @property
    def tags(self) -> tuple[str, ...]:
        """Combined ``roles`` + ``groups`` for legacy callers expecting a flat tag list."""
        return tuple(self.roles + self.groups)


def load_hosts(inventory_dir: Path) -> list[Host]:
    """Read every ``*.yaml`` + ``*.yml`` under ``inventory_dir`` and return ``list[Host]``.

    Both extensions are accepted so users can drop in either form (the
    ``dots ssh render`` help text advertises the ``*.yml`` shorthand). Hosts
    are returned sorted by ``name`` for deterministic downstream output.
    """
    hosts: list[Host] = []
    yaml_files = sorted(list(inventory_dir.glob("*.yaml")) + list(inventory_dir.glob("*.yml")))
    for yaml_file in yaml_files:
        raw = yaml.safe_load(yaml_file.read_text()) or {}
        hosts.append(Host.model_validate(raw))
    return sorted(hosts, key=lambda h: h.name)


def render_ssh_config(hosts: list[Host], role_filter: str | None = None) -> str:
    """Emit OpenSSH config block for the given hosts.

    Unchanged from P3 thanks to the ``@property`` accessors on ``Host`` — every
    field referenced here (``name``, ``addr``, ``port``, ``user``,
    ``identity_file``, ``role``) resolves through the convenience properties
    that wrap the new nested schema.
    """
    lines = [
        "# AUTO-GENERATED by `dots ssh render` — do not edit.",
        f"# Source: dots inventory ({len(hosts)} hosts)",
        "",
    ]
    for h in hosts:
        if role_filter and h.role != role_filter:
            continue
        lines.append(f"Host {h.name}")
        lines.append(f"    HostName {h.addr}")
        if h.port != 22:
            lines.append(f"    Port {h.port}")
        if h.user:
            lines.append(f"    User {h.user}")
        if h.identity_file:
            lines.append(f"    IdentityFile {h.identity_file}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
