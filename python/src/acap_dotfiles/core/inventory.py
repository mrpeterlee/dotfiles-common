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
    hostnames: list[str] = Field(
        default_factory=list,
        description=(
            "Historical names this host has had. NOT rendered by "
            "render_ssh_config — use legacy_aliases for that. May be "
            "deprecated in a future schema_version bump."
        ),
    )

    # Connection
    addresses: Addresses = Field(default_factory=Addresses)
    ssh: SSH = Field(default_factory=SSH)

    # Classification (drives ansible groups, dotfiles overlay, etc.)
    provider: str | None = None  # bare-metal | vultr | oracle | aws | ...
    region: str | None = None  # sg | jp | cn | us | ...
    role_tag: str | None = None  # prod | ingress | egress | admin | ...
    roles: list[str] = Field(default_factory=list)  # e.g. [trading, vm_host, ...]
    groups: list[str] = Field(default_factory=list)  # e.g. [tailscale_nodes, sg, ...]

    # P4 T11: legacy SSH bookmark names that must keep resolving with the
    # canonical host's connection params during the rename window. Each entry
    # gets emitted as a SEPARATE Host stanza in render_ssh_config so muscle-memory
    # `ssh sg-prod-1` keeps working after the canonical name moves to
    # `acap-sg-prod-1`. This is distinct from `hostnames[]` (which historically
    # documented all names a host has had — and may include names that need
    # DIFFERENT user/key/port than the canonical, e.g. oracle-a/oracle-b/
    # acap-admin pre-rename). Use `legacy_aliases` ONLY for aliases that share
    # the canonical host's SSH params.
    legacy_aliases: list[str] = Field(default_factory=list)

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
        """Derive org-role from canonical hostname prefix (most reliable), then groups.

        We control the canonical hostname (``<org>-<region>-<role>-<n>``), so the
        ``acap-`` / ``tapai-`` prefix is the most reliable signal. Group-based
        fallback handles legacy hosts not yet renamed (e.g. anything pre-P4 that
        only has ``tailscale_nodes`` to identify it). Hosts that match neither
        signal default to ``personal``.

        Codex round-2 caught the prior groups-only heuristic misclassifying
        ``acap-jp-ingress-1`` / ``acap-sg-egress-1`` / ``acap-sg-ingress-{1,2}``
        as ``personal`` because their ``groups[]`` lacks ``tailscale_nodes`` and
        any ``acap*``-prefixed group.
        """
        # Canonical hostnames are <org>-<region>-<role>-<n>; extract the org prefix.
        if self.name.startswith("acap-") or self.name == "acap":
            return "acap"
        if self.name.startswith("tapai-") or self.name == "tapai":
            return "tapai"
        # Group-based fallback for legacy hosts not yet renamed.
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

    Mostly unchanged from P3 thanks to the ``@property`` accessors on ``Host`` —
    every field referenced here (``name``, ``addr``, ``port``, ``user``,
    ``identity_file``, ``role``) resolves through the convenience properties
    that wrap the new nested schema.

    P4 codex round-2 additions:

    - ``ProxyJump`` is now emitted from ``ssh.proxy_jump`` (was loaded but
      silently dropped, leaving bastion-only hosts unusable).

    P4 T11 (Option A): each entry in ``legacy_aliases[]`` is emitted as a
    SEPARATE ``Host`` stanza that points at the canonical host's connection
    params (HostName, Port, User, IdentityFile, ProxyJump). Multi-host syntax
    (``Host canonical alias1 alias2``) is intentionally avoided so that an
    alias entry can later diverge into its own inventory file with
    different params without breaking SSH config — and so per-alias
    matching in tools like ``ssh -G alias`` stays unambiguous.

    ``hostnames[]`` is treated as historical-documentation only: those names
    may need DIFFERENT user/key/port/ProxyJump than the canonical (e.g.
    pre-P4-rename ``oracle-a``/``oracle-b``/``acap-admin`` that legacy SSH
    fragments still service with their own user/identity), so this renderer
    deliberately ignores it. A later cleanup may either (a) merge the safe
    subset of ``hostnames[]`` into ``legacy_aliases[]``, or (b) drop the field
    entirely. Whichever wins, the change is mechanical once the rename window
    closes.
    """
    lines = [
        "# AUTO-GENERATED by `dots ssh render` — do not edit.",
        f"# Source: dots inventory ({len(hosts)} hosts)",
        "",
    ]
    for h in hosts:
        if role_filter and h.role != role_filter:
            continue
        # Canonical stanza.
        lines.append(f"Host {h.name}")
        lines.append(f"    HostName {h.addr}")
        if h.port != 22:
            lines.append(f"    Port {h.port}")
        if h.user:
            lines.append(f"    User {h.user}")
        if h.identity_file:
            lines.append(f"    IdentityFile {h.identity_file}")
        if h.ssh.proxy_jump:
            lines.append(f"    ProxyJump {h.ssh.proxy_jump}")
        lines.append("")
        # P4 T11 — one alias stanza per legacy bookmark, all pointing at the
        # same connection params as the canonical entry.
        for alias in h.legacy_aliases:
            lines.append(f"# Legacy alias for {h.name} — remove when SSH bookmarks are migrated")
            lines.append(f"Host {alias}")
            lines.append(f"    HostName {h.addr}")
            if h.port != 22:
                lines.append(f"    Port {h.port}")
            if h.user:
                lines.append(f"    User {h.user}")
            if h.identity_file:
                lines.append(f"    IdentityFile {h.identity_file}")
            if h.ssh.proxy_jump:
                lines.append(f"    ProxyJump {h.ssh.proxy_jump}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"
