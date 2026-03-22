#!/usr/bin/env bash
# Custom pip installs from private indexes
# Sourced by build.sh — ENV_PYTHON and ENV_UV must be set before sourcing

set -euo pipefail

if [[ -z "${ENV_PYTHON:-}" ]]; then
    echo "ERROR: ENV_PYTHON must be set" >&2
    exit 1
fi

if [[ -z "${ENV_UV:-}" ]]; then
    echo "ERROR: ENV_UV must be set" >&2
    exit 1
fi

# Bloomberg API (fails gracefully outside Bloomberg network)
if ! "$ENV_UV" pip install --python "$ENV_PYTHON" \
    --index-url=https://bcms.bloomberg.com/pip/simple \
    blpapi 2>/dev/null; then
    echo "WARNING: blpapi install skipped (expected outside Bloomberg network)"
fi
