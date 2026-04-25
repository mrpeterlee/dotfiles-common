from pathlib import Path

import pytest
from click.testing import CliRunner

from acap_dotfiles.cli import main


def _seed_inventory(inv: Path) -> None:
    """Seed a tmp inventory with two nested-schema hosts.

    The P4 nested schema replaces the P3 flat ``addr/port/user`` keys with
    ``addresses.{public,lan,private,tailscale}`` + ``ssh.{port,user,...}`` +
    a ``groups[]`` list that drives the derived ``role`` property
    (``tailscale_nodes`` → ``acap``).
    """
    inv.mkdir(parents=True, exist_ok=True)
    (inv / "alpha.yaml").write_text(
        "name: alpha\n"
        "addresses:\n"
        "  public: 10.0.0.1\n"
        "ssh:\n"
        "  user: peter\n"
        "groups: [tailscale_nodes]\n"  # → role=acap
    )
    (inv / "beta.yaml").write_text(
        "name: beta\naddresses:\n  public: 10.0.0.2\nssh:\n  port: 2222\n"
        # no groups → role=personal
    )


def test_ssh_render_uses_default_inventory_under_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ACAP_DOTFILES_HOME", str(tmp_path))
    _seed_inventory(tmp_path / "inventory" / "hosts")
    result = CliRunner().invoke(main, ["ssh", "render"])
    assert result.exit_code == 0, result.output
    assert "Host alpha" in result.stdout
    assert "Host beta" in result.stdout
    assert "Port 2222" in result.stdout


def test_ssh_render_with_custom_inventory_dir(tmp_path: Path) -> None:
    inv = tmp_path / "custom-inv"
    _seed_inventory(inv)
    result = CliRunner().invoke(main, ["ssh", "render", "--inventory", str(inv)])
    assert result.exit_code == 0, result.output
    assert "Host alpha" in result.stdout
    assert "    HostName 10.0.0.2" in result.stdout


def test_ssh_render_writes_to_out_file(tmp_path: Path) -> None:
    inv = tmp_path / "inv"
    _seed_inventory(inv)
    out = tmp_path / "build" / "ssh.conf"
    result = CliRunner().invoke(main, ["ssh", "render", "--inventory", str(inv), "--out", str(out)])
    assert result.exit_code == 0, result.output
    assert out.is_file()
    body = out.read_text()
    assert "Host alpha" in body
    assert "Host beta" in body
    assert "wrote 2 hosts" in result.stdout


def test_ssh_render_role_filter_excludes_other_roles(tmp_path: Path) -> None:
    inv = tmp_path / "inv"
    _seed_inventory(inv)
    result = CliRunner().invoke(main, ["ssh", "render", "--inventory", str(inv), "--role", "acap"])
    assert result.exit_code == 0, result.output
    assert "Host alpha" in result.stdout
    assert "Host beta" not in result.stdout


# ----------------------------------------------------------------------
# P4 T11 — legacy_aliases[] CLI-surface coverage
# ----------------------------------------------------------------------


def test_legacy_alias_emits_separate_host_block_with_same_params(tmp_path: Path) -> None:
    """A host with ``legacy_aliases: [old-name]`` must produce TWO Host blocks
    in the rendered config (canonical + alias), with identical
    ``HostName``/``Port``/``User``/``IdentityFile`` lines on both.
    """
    inv = tmp_path / "inv"
    inv.mkdir(parents=True)
    (inv / "acap-sg-prod-1.yaml").write_text(
        "name: acap-sg-prod-1\n"
        "addresses:\n"
        "  lan: 10.1.1.100\n"
        "ssh:\n"
        "  port: 55555\n"
        "  user: peter\n"
        "  identity: peter_acap\n"
        "legacy_aliases:\n"
        "  - sg-prod-1\n"
    )
    result = CliRunner().invoke(main, ["ssh", "render", "--inventory", str(inv)])
    assert result.exit_code == 0, result.output
    out = result.stdout
    # Two Host stanzas, NOT a multi-host `Host canonical alias` line.
    assert "Host acap-sg-prod-1" in out
    assert "Host sg-prod-1" in out
    assert "Host acap-sg-prod-1 sg-prod-1" not in out
    # Both stanzas carry identical connection params.
    assert out.count("    HostName 10.1.1.100") == 2
    assert out.count("    Port 55555") == 2
    assert out.count("    User peter") == 2
    assert out.count("    IdentityFile ~/.ssh/peter_acap") == 2
    # Spec-format legacy comment line precedes the alias stanza.
    assert "# Legacy alias for acap-sg-prod-1 — remove when SSH bookmarks are migrated" in out


def test_legacy_alias_inherits_proxy_jump(tmp_path: Path) -> None:
    """The alias Host block also includes ``ProxyJump`` when the canonical
    has ``ssh.proxy_jump`` set, so the bookmark behaves identically to the
    canonical entry from the user's shell.
    """
    inv = tmp_path / "inv"
    inv.mkdir(parents=True)
    (inv / "behind-bastion.yaml").write_text(
        "name: behind-bastion\n"
        "addresses:\n"
        "  public: 10.99.0.1\n"
        "ssh:\n"
        "  user: peter\n"
        "  proxy_jump: bastion.example.com\n"
        "legacy_aliases:\n"
        "  - legacy-alias\n"
    )
    result = CliRunner().invoke(main, ["ssh", "render", "--inventory", str(inv)])
    assert result.exit_code == 0, result.output
    out = result.stdout
    # ProxyJump appears twice — once in the canonical stanza, once in the alias.
    assert out.count("    ProxyJump bastion.example.com") == 2


def test_no_legacy_aliases_emits_only_canonical(tmp_path: Path) -> None:
    """A host with empty (or unset) ``legacy_aliases`` emits only the
    canonical Host stanza — no spurious alias blocks, no legacy comment
    line. Regression for the 7 acap hosts that don't yet have
    ``legacy_aliases`` populated in their inventory yaml.
    """
    inv = tmp_path / "inv"
    inv.mkdir(parents=True)
    (inv / "alpha.yaml").write_text(
        "name: alpha\naddresses:\n  public: 10.0.0.1\nssh:\n  user: peter\n"
    )
    result = CliRunner().invoke(main, ["ssh", "render", "--inventory", str(inv)])
    assert result.exit_code == 0, result.output
    out = result.stdout
    # Exactly one `Host ` line in the rendered config.
    assert out.count("Host ") == 1
    # No legacy-alias annotation.
    assert "Legacy alias" not in out
