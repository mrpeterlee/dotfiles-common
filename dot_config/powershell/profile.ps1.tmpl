# PowerShell profile — managed by chezmoi
# Symlinked to $PROFILE by chezmoi setup script

# ---------------------------------------------------------------------------
# PATH additions
# ---------------------------------------------------------------------------
$extraPaths = @(
    (Join-Path $env:USERPROFILE ".local\bin")
    "D:\tool\git\cmd"
    "D:\tool\conda\envs\paper\Library\bin"
)
foreach ($p in $extraPaths) {
    if ((Test-Path $p) -and ($env:PATH -notlike "*$p*")) {
        $env:PATH = "$p;$env:PATH"
    }
}

# ---------------------------------------------------------------------------
# PSReadLine
# ---------------------------------------------------------------------------
if (Get-Module -ListAvailable PSReadLine) {
    Set-PSReadLineOption -EditMode Vi
    Set-PSReadLineOption -PredictionSource History
    Set-PSReadLineOption -PredictionViewStyle ListView
    Set-PSReadLineKeyHandler -Key Tab -Function MenuComplete
    Set-PSReadLineKeyHandler -Key UpArrow -Function HistorySearchBackward
    Set-PSReadLineKeyHandler -Key DownArrow -Function HistorySearchForward
}

# ---------------------------------------------------------------------------
# Aliases — mirror zsh where applicable
# ---------------------------------------------------------------------------
Set-Alias -Name g -Value git
Set-Alias -Name lg -Value lazygit
Set-Alias -Name cm -Value chezmoi
Set-Alias -Name e -Value exit

# ---------------------------------------------------------------------------
# eza-based ls/ll/lt (if eza installed)
# ---------------------------------------------------------------------------
if (Get-Command eza -ErrorAction SilentlyContinue) {
    function ls  { eza -l --classify --icons --color=always --group-directories-first @args }
    function ll  { eza -lah --group-directories-first --icons --classify @args }
    function lt  { eza -lah --group-directories-first --icons --classify --tree --level=2 @args }
    function lm  { eza -lahr --color-scale --icons -s=modified @args }
    function lb  { eza -lahr --color-scale --icons -s=size @args }
}

# ---------------------------------------------------------------------------
# bat-based cat (if bat installed)
# ---------------------------------------------------------------------------
if (Get-Command bat -ErrorAction SilentlyContinue) {
    Remove-Item Alias:cat -ErrorAction SilentlyContinue
    function cat { bat --paging=never @args }
}

# ---------------------------------------------------------------------------
# zoxide (z command)
# ---------------------------------------------------------------------------
if (Get-Command zoxide -ErrorAction SilentlyContinue) {
    Invoke-Expression (& { (zoxide init pwsh | Out-String) })
}

# ---------------------------------------------------------------------------
# Navigation helpers
# ---------------------------------------------------------------------------
function .. { Set-Location .. }
function ... { Set-Location ..\.. }
function .... { Set-Location ..\..\.. }

# Git repo root
function cg { Set-Location (git rev-parse --show-toplevel) }

# ---------------------------------------------------------------------------
# External service helpers
# ---------------------------------------------------------------------------
function myip { (Invoke-WebRequest -Uri "https://icanhazip.com" -UseBasicParsing).Content.Trim() }
