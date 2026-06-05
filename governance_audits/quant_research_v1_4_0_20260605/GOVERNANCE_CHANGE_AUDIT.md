# Governance Change Audit - quant-research v1.4.0

## Metadata

- audit_date: 2026-06-05
- timezone: Asia/Shanghai
- target_repo: `D:\MT5\RESEARCH_STANDARD`
- change_type: governance_and_skill_revision
- old_release_tag: `quant-research-v1.3.0`
- new_release_tag: `quant-research-v1.4.0`
- audit_result: PASS

## Scope

This audit covers a governance and Codex skill update only.

Included:

- MTF lookahead and higher-timeframe availability rules.
- Phase 2+ one-version-one-folder isolation rules.
- Updated AGENTS/CLAUDE/README/CHEATSHEET workflow references.
- Updated `quant-research` skill metadata, instructions, templates and read-only scripts.

Excluded:

- No strategy signal code was modified.
- No strategy parameters were modified.
- No backtest, optimization, holdout or forward-live metric was generated.
- No frozen candidate, runtime package, Git tag for a strategy, or forward-live branch was changed.
- No `D:\MT5\research_registry\strategy_registry.yaml` record was edited.

## Governance Findings

### Finding 1 - MTF lookahead risk required a hard gate

Prior governance required generic lookahead checks and bar-by-bar replay, but did not make
multi-timeframe feature availability a separate blocking artifact. This allowed a batch
backtest to pass while using incomplete higher-timeframe bars, especially when open-time
labels were merged into lower-timeframe rows.

Resolution:

- Added `MTF_LOOKAHEAD_AND_VERSION_ISOLATION_STANDARD.md`.
- Required `feature_available_at <= decision_time`.
- Required `mtf_timing_audit.md` for Phase 2+ MTF candidates.
- Required MTF feature diffs in bar-by-bar replay before freeze/runtime handoff.
- Added `scripts/mtf_lookahead_audit.py` as a read-only diagnostic helper.

### Finding 2 - Version output contamination required a hard gate

Prior governance required versioning, but did not force backtest outputs, records and caches
to live inside a single version root. This left room for a current version to accidentally
read another version's trades, reports, saved runs or cached data.

Resolution:

- Required `versions/<version>/` for Phase 2+ candidates.
- Required `version_manifest.yaml`.
- Blocked sibling-version `backtests/`, `reports/`, `cache/`, `trades.csv`, `signals.csv`
  and loose `saved_runs` as current-version backtest inputs.
- Added `scripts/version_isolation_check.py` as a read-only diagnostic helper.

## Validation Performed

Commands run:

```text
python -m py_compile .codex/skills/quant-research/scripts/mtf_lookahead_audit.py .codex/skills/quant-research/scripts/version_isolation_check.py
python .codex/skills/quant-research/scripts/mtf_lookahead_audit.py --inputs <temp_safe_mtf_csv>
python .codex/skills/quant-research/scripts/version_isolation_check.py --version-root <temp_versions/v0_1> --manifest <temp_manifest> --scan <temp_versions/v0_1>
python C:\Users\86640\.codex\skills\.system\skill-creator\scripts\quick_validate.py .codex/skills/quant-research
rg -n "十大禁区|七个问题" D:\MT5\RESEARCH_STANDARD
git diff --check
```

Results:

- Python syntax check: PASS.
- MTF safe sample audit: PASS.
- Version isolation safe sample audit: PASS.
- Skill validation: PASS.
- Outdated `十大禁区` / `七个问题` wording scan: PASS, no matches.
- `git diff --check`: PASS, only expected Windows LF/CRLF warnings.

## Stage / Permission / Contamination Statement

- Applicable stage: governance-layer revision, not a single strategy Stage 0-13 task.
- Code changes permitted: yes, for governance docs and skill files only.
- Strategy code changes permitted: not applicable; no strategy code was touched.
- Parameter changes permitted: not applicable; no strategy parameters were touched.
- Execution audit required: governance change audit only; no strategy execution audit was run.
- Forward-live contamination risk: none from this change, because no strategy runtime, forward-live
  branch, signal log, trade log, registry record or frozen candidate was modified.

## Release Decision

PASS.

The revised governance may be committed and tagged as `quant-research-v1.4.0`. The older
`quant-research-v1.3.0` tag remains the preserved previous release.
