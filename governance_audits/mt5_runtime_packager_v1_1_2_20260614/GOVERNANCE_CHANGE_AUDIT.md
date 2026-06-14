# MT5 Runtime Packager v1.1.2 Governance Change Audit

Date: 2026-06-14

## Scope

This governance/skill update tightens the MT5 runtime packaging deliverable shape. It does not
modify any strategy logic, parameters, backtest result, forward-live evidence, or registry strategy
state.

Affected files:

- `D:\MT5\RESEARCH_STANDARD\MT5_RUNTIME_PACKAGING_STANDARD.md`
- `D:\MT5\RESEARCH_STANDARD\.codex\skills\mt5-runtime-packager\SKILL.md`
- `D:\MT5\RESEARCH_STANDARD\.codex\skills\mt5-runtime-packager\scripts\audit_mt5_runtime_package.py`
- `D:\MT5\RESEARCH_STANDARD\.codex\skills\mt5-runtime-packager\references\portable-runtime-pattern.md`
- `D:\MT5\RESEARCH_STANDARD\.codex\skills\mt5-runtime-packager\agents\openai.yaml`

## User Requirement Captured

The user reported that the latest package contained many BAT files. The desired deliverable is:

```text
package\
  StrategyRuntime.exe
  config.ini
  logs\
```

The EXE must be immediately executable by double-click. The logs directory must be present and
empty. `data_cache\` is allowed only when the runtime config needs it, and it must also be empty.

## Decision

Final operator delivery is now separate from developer/build output:

- BAT/CMD/PowerShell wrappers may exist only outside the operator folder as development or legacy
  helper tools.
- The final user-facing folder must not contain `.bat`, `.cmd`, `.ps1`, `.py`, `.spec`, source
  files, build scripts, historical logs/caches, local test configs, `build\`, `dist\`, or
  `__pycache__\`.
- The package audit now fails operator folders that contain wrappers or build/source artifacts.

## Audit Changes

`audit_mt5_runtime_package.py` now checks:

- exactly one top-level `.exe`;
- beside-EXE `config.ini`;
- empty `logs\`;
- optional empty `data_cache\` when `data_cache_dir` is configured;
- no BAT/CMD/PS1 wrappers or source/build artifacts in the operator folder.

Hash/docs evidence is no longer required inside the operator folder by default. It should be kept
in a build/audit folder unless the user explicitly asks to include it.

## Validation

Required validation:

- skill validation;
- Python compile for the audit script;
- unit-style check that a sample operator folder with a BAT fails the operator-shape check;
- `git diff --check`;
- local installed skill synchronized from the repo copy.

## Residual Risk

This change enforces the package shape in governance and audit tooling. Existing runtime build
scripts still need to be adjusted per-project so they create a separate minimal operator folder
instead of handing the user `dist` or a folder containing helper BAT files.
