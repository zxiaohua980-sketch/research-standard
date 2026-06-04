param(
    [string]$MT5Root = "D:\MT5",
    [switch]$ForceRootAgents,
    [switch]$SkipSkillInstall
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir

$RootAgentsSource = Join-Path $ScriptDir "MT5_ROOT_AGENTS.md"
$RootAgentsTarget = Join-Path $MT5Root "AGENTS.md"
$SkillSource = Join-Path $RepoRoot ".codex\skills\quant-research"
$SkillTarget = Join-Path $env:USERPROFILE ".codex\skills\quant-research"
$RegistryFile = Join-Path $MT5Root "research_registry\strategy_registry.yaml"

function Write-Step {
    param([string]$Message)
    Write-Host "[setup] $Message"
}

Write-Step "Repository root: $RepoRoot"
Write-Step "MT5 root: $MT5Root"

if (-not (Test-Path -LiteralPath $MT5Root)) {
    Write-Step "Creating MT5 root directory."
    New-Item -ItemType Directory -Path $MT5Root | Out-Null
}

if (-not (Test-Path -LiteralPath $RootAgentsSource)) {
    throw "Missing root AGENTS template: $RootAgentsSource"
}

if (Test-Path -LiteralPath $RootAgentsTarget) {
    if ($ForceRootAgents) {
        $Backup = "$RootAgentsTarget.backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
        Write-Step "Backing up existing root AGENTS.md to $Backup"
        Copy-Item -LiteralPath $RootAgentsTarget -Destination $Backup -Force
        Copy-Item -LiteralPath $RootAgentsSource -Destination $RootAgentsTarget -Force
        Write-Step "Updated root AGENTS.md."
    }
    else {
        Write-Step "Root AGENTS.md already exists. Leaving it unchanged."
    }
}
else {
    Copy-Item -LiteralPath $RootAgentsSource -Destination $RootAgentsTarget
    Write-Step "Installed root AGENTS.md."
}

if (-not $SkipSkillInstall) {
    if (-not (Test-Path -LiteralPath $SkillSource)) {
        throw "Missing skill source: $SkillSource"
    }

    $SkillParent = Split-Path -Parent $SkillTarget
    if (-not (Test-Path -LiteralPath $SkillParent)) {
        Write-Step "Creating Codex skills directory."
        New-Item -ItemType Directory -Path $SkillParent | Out-Null
    }

    Copy-Item -LiteralPath $SkillSource -Destination $SkillParent -Recurse -Force
    Write-Step "Installed Codex skill: $SkillTarget"
}
else {
    Write-Step "Skipped Codex skill install."
}

if (Test-Path -LiteralPath $RegistryFile) {
    Write-Step "Registry found: $RegistryFile"
}
else {
    Write-Step "Registry not found yet: $RegistryFile"
    Write-Step "Clone or copy the private research_registry repository separately if needed."
}

Write-Step "Done."

