# Governance Change Audit — quant-research v1.5.0

- generated_at: 2026-06-14
- repository: `D:\MT5\RESEARCH_STANDARD`
- branch: `main`
- previous_release: `quant-research-v1.4.0`
- planned_release: `quant-research-v1.5.0`
- audit_status: PASS
- evidence_grade: governance_change_only

## Scope

This audit covers a governance and Codex-skill update only. It does not touch any strategy
signal engine, strategy parameters, backtest input data, forward-live logs, runtime order
state, or registered strategy result.

User prompt source:

```text
C:\Users\86640\.codex\attachments\408bed3c-cc80-48a5-a23e-105dddb18928\pasted-text.txt
```

The prompt was converted into `STRICT_AUDIT_ENFORCEMENT_STANDARD.md` and integrated into the
existing three-phase research system without replacing the prior registry, OOS, attribution,
MTF, version-isolation, cost-model or runtime-packaging rules.

## Governance Stage / Permission Statement

- Applicable strategy stage: not a single strategy Stage 0-13 task; this is a framework
  governance revision.
- Strategy code changes permitted: not applicable; none made.
- Strategy parameter changes permitted: not applicable; none made.
- Execution audit required for strategy metrics: unchanged; still required before metrics are
  decision-grade.
- Forward-live contamination risk: none from this governance update, because no forward-live
  signals/trades/logs or frozen strategy files were modified.

## Main Changes

### Strict Audit Enforcement

Added mandatory audit-only/minimal-patch mode for:

- lookahead/future-function repair;
- MTF timing leakage;
- pivot/swing/structure confirm-order integrity;
- execution timing and same-bar assumptions;
- batch-vs-incremental replay determinism;
- survivorship reporting;
- data/version/cache contamination;
- runtime safety review.

The new invariant is:

```text
bar_open_time <= feature_available_at <= signal_time <= execution_time
MT5 bar_close_time = next_bar_open_time
```

Audit mode forbids mixing safety fixes with performance optimization, parameter search, RR/PF
improvement or strategy-logic changes.

### Integrated Standards

Updated:

- `AGENTS.md`
- `CLAUDE.md`
- `THREE_PHASE_RESEARCH_PIPELINE.md`
- `MTF_LOOKAHEAD_AND_VERSION_ISOLATION_STANDARD.md`
- `EXIT_RISK_AND_LOGIC_REFINEMENT_STANDARD.md`
- `README.md`
- `CHEATSHEET.md`
- `START_TODAY.md`
- `STRATEGY_DEVELOPMENT_QUICKSTART.md`
- `bootstrap\MT5_ROOT_AGENTS.md`
- local root pointer `D:\MT5\AGENTS.md`

Also preserved and included the existing governance additions for:

- `BROKER_COST_MODEL_STANDARD.md`
- `MT5_RUNTIME_PACKAGING_STANDARD.md`

### Skill Update

Updated `quant-research` to v1.5.0:

- `D:\MT5\RESEARCH_STANDARD\.codex\skills\quant-research\SKILL.md`
- `D:\MT5\RESEARCH_STANDARD\.codex\skills\quant-research\agents\openai.yaml`
- `D:\MT5\RESEARCH_STANDARD\.codex\skills\quant-research\references\lookahead-bias-standard.md`
- `D:\MT5\RESEARCH_STANDARD\.codex\skills\quant-research\templates\audit_report_template.md`
- `D:\MT5\RESEARCH_STANDARD\.codex\skills\quant-research\templates\mtf_timing_audit_template.md`
- `D:\MT5\RESEARCH_STANDARD\.codex\skills\quant-research\templates\bar_by_bar_replay_report_template.md`
- `D:\MT5\RESEARCH_STANDARD\.codex\skills\quant-research\templates\strict_audit_enforcement_report_template.md`

Installed local skill copy:

```text
C:\Users\86640\.codex\skills\quant-research
```

## Validation Commands

```powershell
git diff --check
```

Result: PASS. Only line-ending normalization warnings were emitted.

```powershell
$env:PYTHONUTF8='1'
python C:\Users\86640\.codex\skills\.system\skill-creator\scripts\quick_validate.py D:\MT5\RESEARCH_STANDARD\.codex\skills\quant-research
```

Result: PASS — `Skill is valid!`

```powershell
$env:PYTHONUTF8='1'
python C:\Users\86640\.codex\skills\.system\skill-creator\scripts\quick_validate.py C:\Users\86640\.codex\skills\quant-research
```

Result: PASS — `Skill is valid!`

## Blocking Findings

None for governance release.

## Non-Blocking Notes

- This audit does not certify any strategy as profitable or decision-grade.
- Existing strategy records in `D:\MT5\research_registry\strategy_registry.yaml` remain
  authoritative.
- Any actual strategy audit must still inspect that strategy's version root, data ledger,
  code, MTF timing, replay output and Git state.

## Release Decision

```text
release_decision: READY_TO_COMMIT_AND_TAG
tag: quant-research-v1.5.0
```
