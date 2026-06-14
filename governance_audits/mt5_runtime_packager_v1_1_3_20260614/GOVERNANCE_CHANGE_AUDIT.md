# MT5 Runtime Packager v1.1.3 Governance Change Audit

Date: 2026-06-14

## Scope

This governance/skill update adds a mandatory post-package EXE smoke and log-error check for MT5
runtime handoff packages. It does not modify any strategy logic, parameters, backtest data,
forward-live evidence, or registry strategy state.

Affected files:

- `D:\MT5\RESEARCH_STANDARD\MT5_RUNTIME_PACKAGING_STANDARD.md`
- `D:\MT5\RESEARCH_STANDARD\.codex\skills\mt5-runtime-packager\SKILL.md`
- `D:\MT5\RESEARCH_STANDARD\.codex\skills\mt5-runtime-packager\scripts\audit_mt5_runtime_package.py`
- `D:\MT5\RESEARCH_STANDARD\.codex\skills\mt5-runtime-packager\scripts\check_runtime_logs_for_errors.py`
- `D:\MT5\RESEARCH_STANDARD\.codex\skills\mt5-runtime-packager\references\portable-runtime-pattern.md`
- `D:\MT5\RESEARCH_STANDARD\.codex\skills\mt5-runtime-packager\agents\openai.yaml`

## User Requirement Captured

After packaging, the final EXE must be tried immediately and logs must be checked for errors.

## Design Decision

The existing split remains:

- offline/static package checks must not open MT5;
- real handoff packages must run the final EXE once from the operator folder or an exact smoke
  copy;
- generated logs must be checked before handoff;
- smoke/log-check evidence must be stored outside the minimal operator folder;
- delivery `logs\` and optional `data_cache\` must be reset to empty after a passing smoke test.

This avoids conflict with the v1.1.2 minimal operator-folder rule.

## Log Error Policy

A package is `runtime_blocked` if the smoke run generates:

- fatal startup logs;
- non-empty error/fatal/exception-named log files;
- traceback output;
- CRITICAL/ERROR/FATAL log lines;
- unhandled exception evidence.

## Tooling Added

Added `scripts/check_runtime_logs_for_errors.py`.

Example:

```powershell
python .\scripts\check_runtime_logs_for_errors.py .\package --report .\post_package_log_check_report.json
```

The report path should be outside the operator folder.

## Audit Changes

`audit_mt5_runtime_package.py` now requires smoke/log-check evidence outside the operator folder
when a portable deliverable exists. Operator folders also reject unexpected top-level files, not
just BAT wrappers.

## Validation

Required validation:

- skill validation;
- Python compile for the audit script and log-check script;
- log-check script test on a clean log folder and an error log folder;
- operator-shape test confirming an extra BAT is rejected;
- `git diff --check`;
- local installed skill synchronized from the repo copy.

## Residual Risk

The log checker is conservative and text-based. Each runtime still needs project-specific review
to confirm the smoke run exercised the expected mode and that any broker/MT5-specific warnings are
interpreted correctly.
