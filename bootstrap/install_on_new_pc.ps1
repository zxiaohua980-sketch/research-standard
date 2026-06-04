param(
    [string]$MT5Root = "D:\MT5",
    [string]$RegistryRoot = "",
    [switch]$ForceRootAgents,
    [switch]$SkipSkillInstall
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = [System.IO.Path]::GetFullPath((Split-Path -Parent $ScriptDir))
$MT5Root = [System.IO.Path]::GetFullPath($MT5Root)

if ([string]::IsNullOrWhiteSpace($RegistryRoot)) {
    $RegistryRoot = Join-Path $MT5Root "research_registry"
}
else {
    $RegistryRoot = [System.IO.Path]::GetFullPath($RegistryRoot)
}

$RootAgentsSource = Join-Path $ScriptDir "MT5_ROOT_AGENTS.md"
$RootAgentsTarget = Join-Path $MT5Root "AGENTS.md"
$SkillSource = Join-Path $RepoRoot ".codex\skills\quant-research"
$SkillTarget = Join-Path $env:USERPROFILE ".codex\skills\quant-research"
$RegistryFile = Join-Path $RegistryRoot "strategy_registry.yaml"

function Write-Step {
    param([string]$Message)
    Write-Host "[setup] $Message"
}

Write-Step "Repository root: $RepoRoot"
Write-Step "MT5 root: $MT5Root"
Write-Step "Registry root: $RegistryRoot"

if (-not (Test-Path -LiteralPath $MT5Root)) {
    Write-Step "Creating MT5 root directory."
    New-Item -ItemType Directory -Path $MT5Root | Out-Null
}

if (-not (Test-Path -LiteralPath $RootAgentsSource)) {
    throw "Missing root AGENTS template: $RootAgentsSource"
}

$RootAgentsContent = Get-Content -LiteralPath $RootAgentsSource -Raw
$RootAgentsContent = $RootAgentsContent.Replace("{{MT5_ROOT}}", $MT5Root)
$RootAgentsContent = $RootAgentsContent.Replace("{{RESEARCH_STANDARD_ROOT}}", $RepoRoot)
$RootAgentsContent = $RootAgentsContent.Replace("{{REGISTRY_FILE}}", $RegistryFile)

if (Test-Path -LiteralPath $RootAgentsTarget) {
    if ($ForceRootAgents) {
        $Backup = "$RootAgentsTarget.backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
        Write-Step "Backing up existing root AGENTS.md to $Backup"
        Copy-Item -LiteralPath $RootAgentsTarget -Destination $Backup -Force
        Set-Content -LiteralPath $RootAgentsTarget -Value $RootAgentsContent -Encoding UTF8
        Write-Step "Updated root AGENTS.md."
    }
    else {
        Write-Step "Root AGENTS.md already exists. Leaving it unchanged."
        Write-Step "Use -ForceRootAgents if the existing file points to old paths."
    }
}
else {
    Set-Content -LiteralPath $RootAgentsTarget -Value $RootAgentsContent -Encoding UTF8
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

    $SkillManifest = Join-Path $SkillTarget "SKILL.md"
    if (Test-Path -LiteralPath $SkillManifest) {
        Write-Step "Skill manifest verified: $SkillManifest"
    }
    else {
        throw "Skill install failed: SKILL.md was not found at $SkillManifest"
    }
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
