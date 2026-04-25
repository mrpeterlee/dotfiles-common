<#
.SYNOPSIS
    Manage dotfiles with chezmoi on Windows.
.DESCRIPTION
    Windows port of the bash dotfiles CLI.
    Commands: install, reinstall, uninstall, status, help
.EXAMPLE
    .\cli.ps1 install
    .\cli.ps1 status
    .\cli.ps1 help
#>

param(
    [Parameter(Position = 0)]
    [string]$Command = "help",

    [Parameter(Position = 1, ValueFromRemainingArguments)]
    [string[]]$ExtraArgs
)

$ErrorActionPreference = "Stop"

# ============================================================================
# Configuration
# ============================================================================

$Repo = if ($env:CHEZMOI_REPO) { $env:CHEZMOI_REPO } else { "MrPeterLee/dotfiles" }
# This script now lives at lib/cli-legacy.ps1 (post-P3 rename). $PSScriptRoot
# would point at lib/, but Test-LocalSource / Ensure-SourceLink expect
# $ScriptDir to be the repo root (where .chezmoi.toml.tmpl lives). Walk up
# one level to recover the legacy semantics.
$ScriptDir = Split-Path -Parent $PSScriptRoot
$ChezmoiConfigDir = Join-Path $env:USERPROFILE ".config\chezmoi"
$DotfilesLink = Join-Path $env:USERPROFILE ".files"

# ============================================================================
# Helpers
# ============================================================================

function Write-Info  { param([string]$Msg) Write-Host "==> " -ForegroundColor Blue -NoNewline; Write-Host $Msg }
function Write-Ok    { param([string]$Msg) Write-Host "  $([char]0x2713) " -ForegroundColor Green -NoNewline; Write-Host $Msg }
function Write-Warn  { param([string]$Msg) Write-Host "  ! " -ForegroundColor Yellow -NoNewline; Write-Host $Msg }
function Write-Err   { param([string]$Msg) Write-Host "  $([char]0x2717) " -ForegroundColor Red -NoNewline; Write-Host $Msg }

function Test-Tool {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Test-LocalSource {
    return Test-Path (Join-Path $ScriptDir ".chezmoi.toml.tmpl")
}

# Ensure ~/.files junction exists so chezmoi's sourceDir resolves correctly.
# Uses a directory junction (no admin required) rather than a symlink.
function Ensure-SourceLink {
    # If ~/.files already resolves as a valid chezmoi source, nothing to do
    if (Test-Path (Join-Path $DotfilesLink ".chezmoi.toml.tmpl")) { return }

    # Script must be in a valid source dir
    if (-not (Test-LocalSource)) { return }

    # Don't need a link if we're already at ~/.files
    if ($ScriptDir -ieq $DotfilesLink) { return }

    # Create junction (no admin required for directory junctions on NTFS)
    Write-Info "Creating ~/.files junction -> $ScriptDir"
    New-Item -ItemType Junction -Path $DotfilesLink -Target $ScriptDir | Out-Null
}

function Ensure-Chezmoi {
    if (Test-Tool "chezmoi") { return }

    Write-Info "Installing chezmoi via winget..."
    winget install --id twpayne.chezmoi --accept-source-agreements --accept-package-agreements --silent

    # Refresh PATH so the new binary is found
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("PATH", "User")

    if (-not (Test-Tool "chezmoi")) {
        Write-Err "Failed to install chezmoi. Install manually: winget install twpayne.chezmoi"
        exit 1
    }
    Write-Ok "chezmoi installed"
}

# ============================================================================
# Commands
# ============================================================================

function Invoke-Install {
    Write-Host ""
    Write-Host "  Installing Dotfiles" -ForegroundColor Cyan
    Write-Host "  $('=' * 40)"
    Write-Host ""

    Ensure-Chezmoi
    Ensure-SourceLink

    $configFile = Join-Path $ChezmoiConfigDir "chezmoi.toml"

    if (-not (Test-Path $configFile)) {
        # First time: init to process config template and run prompts
        if (Test-LocalSource) {
            Write-Info "Using local source: $DotfilesLink"
            chezmoi init --source $DotfilesLink
        } else {
            Write-Info "Fetching from: $Repo"
            chezmoi init $Repo
        }
    } else {
        Write-Info "chezmoi already initialized"
    }

    Write-Info "Applying dotfiles..."
    chezmoi apply

    if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) {
        Write-Err "chezmoi apply failed"
        exit 1
    }

    Write-Host ""
    Write-Ok "Installation complete!"
    Write-Host ""
    Write-Host "  Run 'cli status' to see what was installed."
    Write-Host "  Run 'chezmoi diff' to see pending changes."
    Write-Host ""
}

function Invoke-Reinstall {
    Write-Host ""
    Write-Host "  Force Reinstalling Dotfiles" -ForegroundColor Cyan
    Write-Host "  $('=' * 40)"
    Write-Host ""

    # Step 1: Clean state (forces run_once scripts to re-run)
    Write-Info "Cleaning chezmoi state..."
    $stateDb = Join-Path $ChezmoiConfigDir "chezmoistate.boltdb"
    if (Test-Path $stateDb) { Remove-Item $stateDb -Force }

    $defaultSource = Join-Path $env:USERPROFILE ".local\share\chezmoi"
    if (Test-Path $defaultSource) { Remove-Item $defaultSource -Recurse -Force }

    # Step 2: Ensure chezmoi and source link
    Ensure-Chezmoi
    Ensure-SourceLink

    # Step 3: Initialize
    Write-Info "Initializing chezmoi..."
    if (Test-LocalSource) {
        chezmoi init --source $DotfilesLink
    } else {
        chezmoi init $Repo --prompt=false
    }

    # Step 4: Force apply
    Write-Info "Applying dotfiles..."
    chezmoi apply --force

    if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) {
        Write-Err "chezmoi apply failed"
        exit 1
    }

    # Step 5: Refresh externals
    Write-Info "Refreshing external dependencies..."
    chezmoi apply --refresh-externals 2>&1 | Out-Null

    Write-Host ""
    Write-Ok "Reinstall complete!"
    Write-Host ""
    Invoke-Status
}

function Invoke-Uninstall {
    param([string[]]$Args)

    Write-Host ""
    Write-Host "  Uninstalling Dotfiles" -ForegroundColor Red
    Write-Host "  $('=' * 40)"
    Write-Host ""

    $force = "--force" -in $Args

    if (-not $force) {
        Write-Host "  Warning: This will remove all chezmoi-managed files." -ForegroundColor Yellow
        $reply = Read-Host "  Continue? [y/N]"
        if ($reply -notmatch '^[Yy]') {
            Write-Host "  Aborted."
            return
        }
    }

    if (Test-Tool "chezmoi") {
        Write-Info "Removing managed files..."
        $managed = chezmoi managed --include=files 2>$null
        if ($managed) {
            foreach ($file in $managed) {
                $target = Join-Path $env:USERPROFILE $file
                if (Test-Path $target) {
                    Remove-Item $target -Force -ErrorAction SilentlyContinue
                }
            }
        }

        Write-Info "Removing empty directories..."
        $dirs = chezmoi managed --include=dirs 2>$null
        if ($dirs) {
            $dirs | Sort-Object -Descending | ForEach-Object {
                $target = Join-Path $env:USERPROFILE $_
                if (Test-Path $target) {
                    $children = Get-ChildItem $target -Force -ErrorAction SilentlyContinue
                    if (-not $children) {
                        Remove-Item $target -Force -ErrorAction SilentlyContinue
                    }
                }
            }
        }
    }

    Write-Info "Removing chezmoi config..."
    if (Test-Path $ChezmoiConfigDir) { Remove-Item $ChezmoiConfigDir -Recurse -Force }

    $defaultSource = Join-Path $env:USERPROFILE ".local\share\chezmoi"
    if (Test-Path $defaultSource) {
        Write-Info "Removing chezmoi source..."
        Remove-Item $defaultSource -Recurse -Force
    }

    Write-Host ""
    Write-Ok "Uninstall complete!"
    Write-Host ""
    Write-Host "  Note: Packages installed via winget were not removed."
    Write-Host ""
}

function Invoke-Status {
    Write-Host ""
    Write-Host "  Dotfiles Status" -ForegroundColor Cyan
    Write-Host "  $('=' * 40)"
    Write-Host ""

    # Check chezmoi
    if (Test-Tool "chezmoi") {
        Write-Ok "chezmoi installed"
    } else {
        Write-Err "chezmoi not installed"
        Write-Host ""
        Write-Host "  Run 'cli restore' to get started."
        return
    }

    # Managed files count
    $fileCount = 0
    try {
        $managed = chezmoi managed --include=files 2>$null
        if ($managed) { $fileCount = ($managed | Measure-Object).Count }
    } catch {}
    Write-Host "  Managed files: $fileCount"
    Write-Host ""

    # Tools
    Write-Host "  Tools:"
    $tools = @("bat", "rg", "lazygit", "eza", "zoxide", "op")
    foreach ($tool in $tools) {
        if (Test-Tool $tool) { Write-Ok $tool } else { Write-Err $tool }
    }
    Write-Host ""

    # Config files
    Write-Host "  Config files:"
    $configs = @(
        @{ Name = "git";        Path = Join-Path $env:USERPROFILE ".config\git\config" }
        @{ Name = "powershell"; Path = Join-Path $env:USERPROFILE ".config\powershell\profile.ps1" }
        @{ Name = "lazygit";    Path = Join-Path $env:USERPROFILE ".config\lazygit\config.yml" }
        @{ Name = "wezterm";    Path = Join-Path $env:USERPROFILE ".wezterm.lua" }
    )
    foreach ($cfg in $configs) {
        if (Test-Path $cfg.Path) { Write-Ok $cfg.Name } else { Write-Err $cfg.Name }
    }
    Write-Host ""

    # Symlinks
    Write-Host "  Symlinks:"
    $symlinks = @(
        @{ Name = "Windows Terminal"; Path = Join-Path $env:LOCALAPPDATA "Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json" }
        @{ Name = "GlazeWM";         Path = Join-Path $env:USERPROFILE ".glzr\glazewm\config.yaml" }
        @{ Name = ".files";           Path = Join-Path $env:USERPROFILE ".files" }
    )
    foreach ($sym in $symlinks) {
        $item = Get-Item $sym.Path -ErrorAction SilentlyContinue
        if ($item -and ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint)) {
            Write-Ok "$($sym.Name) -> $($item.Target)"
        } elseif (Test-Path $sym.Path) {
            Write-Warn "$($sym.Name) (exists but not a symlink)"
        } else {
            Write-Err $sym.Name
        }
    }
    Write-Host ""
}

function Invoke-Help {
    Write-Host @"

  +-------------------------------------------------------------+
  |                   DOTFILES CLI (Windows)                     |
  |                                                              |
  |  Manage your dotfiles with chezmoi                           |
  +-------------------------------------------------------------+

  USAGE:
      cli <command>

  COMMANDS:
      install       Install dotfiles on a new machine
      reinstall     Force reinstall (clean slate)
      uninstall     Remove all managed files
      status        Show installation status
      help          Show this help message

  QUICK START:

      # Clone and install:
      git clone https://github.com/MrPeterLee/dotfiles.git D:\lab\.files
      cd D:\lab\.files
      .\cli.bat restore

      # Or from PowerShell directly:
      pwsh .\cli.ps1 restore

  COMMON WORKFLOWS:

      # First time setup
      > cli restore

      # Something broke? Start fresh
      > cli restore --force

      # See what chezmoi would change
      > chezmoi diff

      # Apply pending changes
      > chezmoi apply

      # Edit a managed file
      > chezmoi edit ~\.config\git\config

  ENVIRONMENT VARIABLES:
      CHEZMOI_REPO     Override GitHub repo (default: MrPeterLee/dotfiles)
      DOTFILES_DEBUG   Set to 1 for verbose output

  NOTE:
      Linux-only commands (prereq, env) are not available on Windows.
      Packages are managed via winget (see run_once install script).

  MORE INFO:
      https://github.com/MrPeterLee/dotfiles
      https://www.chezmoi.io/

"@
}

# ============================================================================
# Main
# ============================================================================

switch ($Command) {
    "install"                           { Invoke-Install }
    "reinstall"                         { Invoke-Reinstall }
    "uninstall"                         { Invoke-Uninstall -Args $ExtraArgs }
    "status"                            { Invoke-Status }
    { $_ -in "help", "--help", "-h" }   { Invoke-Help }
    default {
        Write-Err "Unknown command: $Command"
        Write-Host ""
        Write-Host "  Run 'cli help' for usage."
        exit 1
    }
}
