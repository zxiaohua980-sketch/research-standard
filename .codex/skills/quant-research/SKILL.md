---
name: quant-research
description: Research governance operating system for MT5 and FX quantitative research. Use when Codex works on foreign-exchange quant tasks involving OHLC/tick data, event studies, backtests, market microstructure, liquidity sweeps, walk-forward, OOS validation, lookahead audits, survivorship checks, data ledger guards, frozen baseline registries, research stage gates, parameter freeze management, strategy attribution, or Chinese diagnostic reports.
---

# Quant Research

## Overview

Use this skill as a research operating system, not as an alpha generator. The goal is to turn a market hypothesis into reproducible evidence and decide whether the hypothesis should continue, be weakened, or be archived.

This skill must not develop trading strategies by itself, run hidden optimization, produce broker instructions, or convert market narratives into alpha claims. It coordinates workflow, references, templates, read-only audit scripts, and v1.2 governance gates.

## Authority Boundary

Before any strategy or research work, find and read the nearest project `AGENTS.md`. In this repository, `AGENTS.md` is the project-level highest rule. This skill must not copy or weaken those hard rules; it only operationalizes them by selecting workflow steps, references, templates, and read-only checks.

If `AGENTS.md` and this skill conflict, obey `AGENTS.md`. If a project has a central strategy registry, query it before changing or evaluating a strategy. If a strategy is unregistered, treat formal research as blocked until registration exists.

## Main Workflow

For every applicable task:

1. Read project `AGENTS.md` and the strategy registry.
2. Identify the task type and research Stage 0-13.
3. Check Git state, machine-readable data ledger state, frozen baseline registry state, research stage gate state, and forward-live contamination risk.
4. Require a written hypothesis before any backtest or parameter search.
5. Run event study before strategy-level performance evaluation when the task concerns a market pattern or event.
6. Require execution audit before trusting any backtest metric.
7. Require attribution before modifying filters, SL, TP, trailing, timeout, sizing, entry timing, or cost assumptions.
8. Separate IS, OOS-Dev, locked_final_holdout, and forward-live; never use the same data both to choose and to prove.
9. Run the relevant read-only audit scripts when input artifacts exist.
10. Use templates for reports and mark whether the conclusion is decision-grade.
11. Accept `REJECT`, `WEAK`, `AUDIT_FAIL`, or `NOT_DECISION_GRADE` as valid final outcomes.

## Governance Gates

Apply these guards before ordinary audit scripts whenever the required state files exist:

1. **Data Ledger Guard**: use `references/data-ledger-standard.md`, `templates/research_data_ledger.yaml`, and `scripts/data_ledger_guard.py` to prevent consumed OOS, reused holdout, or untracked datasets from being treated as decision-grade.
2. **Frozen Baseline Registry**: use `references/frozen-baseline-registry-standard.md`, `templates/frozen_candidates_template.yaml`, `templates/archived_hypotheses_template.yaml`, and `scripts/frozen_registry_check.py` to verify frozen candidates, archived hypotheses, and blocked actions.
3. **Research Stage Gate**: use `references/research-stage-gate-standard.md`, `templates/research_stage_state.yaml`, and `scripts/stage_gate_check.py` to decide whether the requested action is allowed at the current stage.

If a guard blocks the action, stop formal research and produce a failure or guard report. Do not continue by calling the run "temporary" unless the user explicitly requests exploratory work and accepts that it is not decision-grade.

## Task Classifier

- New research idea: create or request `hypothesis.md`, event-study plan, data contract, and ledger entry.
- Event study: load `references/event-study-standard.md` and use `templates/event_study_template.md`.
- Backtest review: load `references/backtest-interpretation-standard.md`, run timing/integrity checks, and use `templates/strategy_report_template.md`.
- Execution audit: load `references/lookahead-bias-standard.md`, `references/session-timezone-standard.md`, and use `templates/audit_report_template.md`.
- Filter, exit, SL, TP, trailing, sizing, or entry timing change: load `references/strategy-attribution-standard.md` and require `templates/logic_change_proposal_template.md`.
- Microstructure or liquidity sweep research: load `references/microstructure-liquidity-standard.md` and event-study standard.
- Survivorship, missing trades, failed orders, or universe issues: load `references/survivorship-bias-standard.md`.
- Failed or weak evidence: use `templates/failure_report_template.md`.
- Data contamination or data-use uncertainty: load `references/data-ledger-standard.md` and run `scripts/data_ledger_guard.py`.
- Frozen, OOS, forward-live, or archived-hypothesis questions: load `references/frozen-baseline-registry-standard.md` and run `scripts/frozen_registry_check.py` when registry files exist.
- Any action whose stage permissions are unclear: load `references/research-stage-gate-standard.md` and run `scripts/stage_gate_check.py`.

## Required References

- `references/data-contracts.md`: required fields for signals, trades, event studies, summaries, and audit output.
- `references/lookahead-bias-standard.md`: future-function and timing audit rules.
- `references/survivorship-bias-standard.md`: missing trade, failed order, truncation, and abnormal data checks.
- `references/backtest-interpretation-standard.md`: how to interpret metrics without overstating evidence.
- `references/strategy-attribution-standard.md`: attribution before rule changes.
- `references/event-study-standard.md`: event-study-first research design.
- `references/microstructure-liquidity-standard.md`: London/NY, liquidity sweep, failed breakout, volatility, and cross-symbol rules.
- `references/session-timezone-standard.md`: UTC, broker time, local time, DST, rollover, and cross-day session handling.
- `references/data-ledger-standard.md`: machine-readable dataset usage and contamination guard.
- `references/frozen-baseline-registry-standard.md`: frozen candidates and archived hypotheses governance.
- `references/research-stage-gate-standard.md`: allowed and blocked actions by research stage.

## Templates

Use:

- `templates/strategy_report_template.md` for full strategy reports.
- `templates/event_study_template.md` for pure event-study reports.
- `templates/audit_report_template.md` for read-only audit reports.
- `templates/data_usage_ledger_template.yaml` when a strategy lacks a data usage ledger.
- `templates/logic_change_proposal_template.md` before any strategy rule change.
- `templates/failure_report_template.md` for rejected, weak, or unauditable results.
- `templates/research_data_ledger.yaml` for machine-readable dataset consumption tracking.
- `templates/frozen_candidates_template.yaml` for frozen baseline candidates.
- `templates/archived_hypotheses_template.yaml` for rejected or superseded hypotheses.
- `templates/research_stage_state.yaml` for current stage, allowed actions, blocked actions, and next gate.

Templates define mandatory fields. Do not omit required fields silently; write `missing`, `not available`, or `not decision-grade` explicitly.

## Read-Only Scripts

Scripts are first-pass audit helpers. They do not repair files, tune parameters, or generate trading advice. Prefer running them on copied or generated artifacts and treat their output as diagnostic evidence, not as proof that the strategy is valid.

- `scripts/signal_timing_check.py`: signal/entry ordering and bar index checks.
- `scripts/session_timezone_check.py`: session, timezone, boundary, rollover, and cross-day checks.
- `scripts/lookahead_audit.py`: suspicious column names and same-bar timing risk.
- `scripts/trade_consistency_check.py`: SL/TP direction, duplicate IDs, costs, open trades, exit reasons.
- `scripts/data_split_ledger_check.py`: ledger presence, final holdout openings, and split status.
- `scripts/output_integrity_check.py`: non-empty reports/CSVs, hashes, row counts, timestamps.
- `scripts/report_required_fields_check.py`: mandatory report sections.
- `scripts/data_ledger_guard.py`: data consumption and holdout reuse guard.
- `scripts/frozen_registry_check.py`: frozen candidate and archived hypothesis guard.
- `scripts/stage_gate_check.py`: current-stage allowed/blocked action guard.

## Output Contract

Every final research response must state:

- task type and stage;
- registry and AGENTS status;
- data ledger guard status;
- frozen registry guard status when applicable;
- stage gate decision;
- data evidence type used;
- audit status;
- whether code or parameters may be changed;
- whether the result is decision-grade;
- allowed next action.

Never present weak evidence as alpha. If evidence fails, report why it failed and stop at the correct stage.
