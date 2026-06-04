# Portable Setup

This repository is the portable governance bundle for the MT5 research workspace.
It is meant to be cloned onto another computer and installed into the local Codex
environment without moving strategy code, test data, backtest outputs, or live logs.

## Repository

Remote:

```powershell
https://github.com/zxiaohua980-sketch/research-standard.git
```

You can clone it anywhere. If the other computer also uses `D:\MT5`, this is the
simple path:

```powershell
git clone https://github.com/zxiaohua980-sketch/research-standard.git D:\MT5\RESEARCH_STANDARD
```

If the other computer uses another directory, clone into that directory instead:

```powershell
git clone https://github.com/zxiaohua980-sketch/research-standard.git E:\Trading\MT5\RESEARCH_STANDARD
```

## What This Repo Owns

Tracked here:

- Canonical research rules such as `AGENTS.md`, `RESEARCH_WORKFLOW.md`,
  `DATA_SPLIT_AND_OOS_POLICY.md`, and `EXIT_RISK_AND_LOGIC_REFINEMENT_STANDARD.md`.
- The Codex skill at `.codex/skills/quant-research`.
- Portable setup helpers under `bootstrap/`.
- Governance examples and pilot artifacts that belong to the standard itself.

Not tracked here:

- Strategy project directories such as `openclaw/`, `H1M5N/`, `MSKD/`, `SBL/`,
  `QH/`, `MA/`, `SMA/`, and similar project folders.
- `D:\MT5\research_registry`, which is its own Git repository.
- Market data, tick data, broker exports, backtest output, optimization output,
  MT5 terminal data folders, runtime packages, logs, secrets, or account configs.

## Install On A New Computer

If the workspace is `D:\MT5`, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
D:\MT5\RESEARCH_STANDARD\bootstrap\install_on_new_pc.ps1
```

If the workspace is somewhere else, pass the real root path:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
E:\Trading\MT5\RESEARCH_STANDARD\bootstrap\install_on_new_pc.ps1 -MT5Root E:\Trading\MT5
```

If the central registry is not under `<MT5Root>\research_registry`, pass it too:

```powershell
E:\Trading\MT5\RESEARCH_STANDARD\bootstrap\install_on_new_pc.ps1 `
  -MT5Root E:\Trading\MT5 `
  -RegistryRoot E:\Trading\registry
```

The script will:

- Create the MT5 root directory if needed.
- Install a generated root entry file from `bootstrap\MT5_ROOT_AGENTS.md` to
  `<MT5Root>\AGENTS.md` when the target does not already exist.
- Write the actual local paths into that generated `AGENTS.md`.
- Install the Codex skill into `%USERPROFILE%\.codex\skills\quant-research`.
- Print a short verification summary.

To replace an existing root entry file intentionally:

```powershell
E:\Trading\MT5\RESEARCH_STANDARD\bootstrap\install_on_new_pc.ps1 `
  -MT5Root E:\Trading\MT5 `
  -ForceRootAgents
```

## Included Skill

Yes, the Codex skill is included in this repository:

```text
.codex\skills\quant-research\SKILL.md
```

The installer copies the whole skill folder to:

```text
%USERPROFILE%\.codex\skills\quant-research
```

## Current Git Topology

The original `D:\MT5` workspace is not a single Git repository. It is a workspace
containing multiple project repositories. Keep the same idea on another machine:
push and pull one repository at a time unless you intentionally redesign the
workspace using submodules or a manifest repo.

The portable governance repo is:

```text
<MT5Root>\RESEARCH_STANDARD -> https://github.com/zxiaohua980-sketch/research-standard.git
```

The central registry is currently separate:

```text
<MT5Root>\research_registry -> local Git repo, no remote configured yet
```

If you want the registry portable too, create a private GitHub repository for it,
then run something like:

```powershell
cd <your-registry-path>
git remote add origin https://github.com/zxiaohua980-sketch/<private-registry-repo>.git
git push -u origin master
```

Use a private repository if the registry contains strategy status, live validation
notes, account paths, machine names, or operational details.

## Safe Sync Rule

Do not upload the whole MT5 workspace as one repository. The workspace contains
nested Git repositories, runtime folders, generated outputs, and potentially
sensitive trading artifacts. Upload only the specific repo you mean to sync.
