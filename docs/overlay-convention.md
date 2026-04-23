# Overlay Convention

This repo (`MrPeterLee/dotfiles-common`) is the common, org-agnostic
baseline. Organizational content lives in per-org overlays stacked
on top at apply time. See the umbrella design spec in `astro-cap/acap`
under `docs/superpowers/specs/2026-04-23-dotfiles-unification-design.md`
for the full picture.

## Overlay layout

An overlay is a chezmoi source-state tree under
`<repo>/dotfiles-overlay/` (or `<repo>/.overlay/` for hidden personal
overlays). It contains at minimum:

- `.chezmoidata/overlay.yaml` — the overlay's data variables. MUST
  define at least `vault` (a 1Password vault name) and MAY define
  org-specific infra values (AWS account IDs, VPN hosts, etc.).
- Any `dot_*` / `private_dot_*` files the overlay contributes.

Example `.chezmoidata/overlay.yaml`:

    vault: AstroCapital
    infra:
      aws_account_id: "442740305558"
      aws_route53_zone_id: "ZXXXXXXXXXXXXXX"
      base_domain: "acap.cc"

## Secret resolution

Any template that needs a secret MUST access it via
`{{ onepasswordRead (printf "op://%s/Infrastructure/<field>" .vault) }}`.

Base templates (in this repo) MUST NOT reference `.vault` at all —
the variable only exists when an overlay has been applied. If you
find yourself writing `.vault` in a `.files` template, the content
belongs in an overlay instead.

## Stacking

The `dots` CLI (Python/Click, source in `cli/`) applies overlays
sequentially in a deterministic order driven by `host-role`:

    .files (always)
      → ~/acap/dotfiles-overlay      (if host-role == acap)
      → ~/tapai/dotfiles-overlay     (if host-role == tapai)
      → ~/notes/.overlay             (if host-role == personal OR ~/notes is present)

Per-host manifest at `~/.local/state/acap-dotfiles/manifest.json`
tracks which source produced which destination path, so files that
move out of an overlay get cleaned up on the next apply.

## Adding a new overlay

1. Create `<overlay-root>/.chezmoidata/overlay.yaml` with `vault:` + infra.
2. Populate `dot_*` / `private_dot_*` files as usual.
3. On a host that should consume this overlay, set
   `~/.config/acap-bootstrap/host-role` to the matching role name and
   clone the overlay's repo. `dots apply` will pick it up.
