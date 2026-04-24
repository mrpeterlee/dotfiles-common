#!/usr/bin/env pwsh
# Deprecation shim. cli.ps1 -> dots (Python CLI).
# Falls through to lib/cli-legacy.ps1 for `conda` and `agents` verbs (out of P3 scope).
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$verb = if ($args.Count -gt 0) { $args[0] } else { "" }

if ($verb -in @("conda", "agents")) {
    & "$ScriptDir\lib\cli-legacy.ps1" @args
    exit $LASTEXITCODE
}

if ($verb -in @("help", "-h", "--help", "")) {
    if (Get-Command dots -ErrorAction SilentlyContinue) {
        & dots --help
        exit $LASTEXITCODE
    } else {
        & "$ScriptDir\lib\cli-legacy.ps1" help
        exit $LASTEXITCODE
    }
}

if (-not (Get-Command dots -ErrorAction SilentlyContinue)) {
    Write-Warning "dots not on PATH - falling back to legacy cli.ps1"
    & "$ScriptDir\lib\cli-legacy.ps1" @args
    exit $LASTEXITCODE
}

Write-Warning "'cli $verb' is deprecated; use 'dots $verb'"
$env:DOTS_LEGACY_SHIM = "1"
& dots @args
exit $LASTEXITCODE
