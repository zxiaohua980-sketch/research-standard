# Portable Setup

This repository is the portable governance bundle for the MT5 research workspace.
It is meant to be cloned onto another computer and installed into the local Codex
environment without moving strategy code, test data, backtest outputs, or live logs.

## Repository

Remote:

```powershell
https://github.com/zxiaohua980-sketch/research-standard.git
```

Recommended clone path on a new Windows machine:

```powershell
git clone https://github.com/zxiaohua980-sketch/research-standard.git D:\MT5\RESEARCH_STANDARD
```

The absolute path matters because the MT5 research entry files currently point to
`D:\MT5\RESEARCH_STANDARD` and `D:\MT5\research_registry`.

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

After cloning, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
D:\MT5\RESEARCH_STANDARD\bootstrap\install_on_new_pc.ps1
```

The script will:

- Create `D:\MT5` if needed.
- Install the root entry file from `bootstrap\MT5_ROOT_AGENTS.md` to
  `D:\MT5\AGENTS.md` when the target does not already exist.
- Install the Codex skill into `%USERPROFILE%\.codex\skills\quant-research`.
- Print a short verification summary.

To replace an existing root entry file intentionally:

```powershell
D:\MT5\RESEARCH_STANDARD\bootstrap\install_on_new_pc.ps1 -ForceRootAgents
```

## Current Git Topology

`D:\MT5` is not a single Git repository. It is a workspace containing multiple
project repositories. Keep it that way unless you intentionally redesign the
workspace using submodules or a manifest repo.

The portable governance repo is:

```text
D:\MT5\RESEARCH_STANDARD -> https://github.com/zxiaohua980-sketch/research-standard.git
```

The central registry is currently separate:

```text
D:\MT5\research_registry -> local Git repo, no remote configured yet
```

If you want the registry portable too, create a private GitHub repository for it,
then run something like:

```powershell
cd D:\MT5\research_registry
git remote add origin https://github.com/zxiaohua980-sketch/<private-registry-repo>.git
git push -u origin master
```

Use a private repository if the registry contains strategy status, live validation
notes, account paths, machine names, or operational details.

## Safe Sync Rule

Do not upload all of `D:\MT5` as one repository. The workspace contains nested Git
repositories, runtime folders, generated outputs, and potentially sensitive
trading artifacts. Upload only the specific repo you mean to sync.

