---
name: quant-research
description: Three-phase research operating system for MT5 and FX quantitative strategy work. Use when Codex works on exploratory alpha hypothesis testing, OHLC/tick backtests, win-rate/RR testing, MFE/MAE attribution, strategy version iteration, bar-by-bar replay, OOS/holdout governance, forward-live boundaries, or preparing a frozen candidate for MT5 dry-run/demo runtime packaging.
---

# Quant Research

## Purpose

Use this skill to move trading ideas through a phase-aware research pipeline:

1. **Phase 1 - Quick exploration**: turn hypotheses into code, fatal-audit the obvious traps, run quick tests, RR tests, and multi-dimensional attribution. Results are exploratory only.
2. **Phase 2 - Candidate iteration**: register promising ideas, version them, audit execution, compare versions, perform attribution-driven changes, and require bar-by-bar replay before freeze.
3. **Phase 3 - EXE/demo runtime handoff**: hand a frozen candidate to MT5 runtime packaging with dry-run/demo safety gates. REAL trading is out of scope.

This skill may help propose, quantify, implement, test, reject, and iterate exploratory strategy hypotheses. It must not present unverified exploration as alpha, OOS, forward-live, or live-ready evidence.

## Authority Boundary

First read the nearest project `AGENTS.md`. If available, also read the strategy registry.

- If `AGENTS.md` conflicts with this skill, obey `AGENTS.md`.
- If a strategy is unregistered, Phase 1 exploration can continue with `templates/idea_card_template.md`, but formal Phase 2+ research is blocked until a minimal registry record exists.
- Do not touch frozen or forward-live strategy code in place.
- Do not place REAL orders, enable REAL-account trading, or treat demo/runtime logs as OOS-Final evidence.

## Phase Classifier

Before acting, classify the task:

| Phase | Use when | Registry | Evidence label |
|------|----------|----------|----------------|
| Phase 1 exploration | new hypothesis, quick code, quick backtest, RR test, MFE/MAE, loss attribution | optional | `exploratory_not_decision_grade` |
| Phase 2 candidate iteration | promising idea, versioned strategy, formal audit, logic change, parameter/RR platform, bar-by-bar replay | required | `candidate_not_final` until freeze/holdout |
| Phase 3 runtime packaging | frozen candidate, EXE, dry-run/demo scan/order simulation, runtime safety | required | `runtime_validation_not_oos_final` |

If the phase is unclear, choose the lowest-risk phase and state the assumption.

## Phase 1 Workflow

Goal: find whether a profit mechanism may exist.

1. Create or update `idea_card.md` using `templates/idea_card_template.md`.
2. Quantify the hypothesis: market, symbol, timeframe, target win rate, target RR, expected trade count, entry, SL, TP, invalidation.
3. Implement the smallest testable code when asked; keep it separate from frozen/live code.
4. Run a fatal audit before trusting even exploratory output:
   - no future data or same-bar ideal fill;
   - bar-close signals execute no earlier than next executable quote/bar;
   - SL/TP direction is legal;
   - same-bar SL/TP collision has a declared policy;
   - costs are included or conservatively estimated;
   - no duplicate/conflict positions or sample-end distortion.
5. Run quick tests and use `templates/quick_test_report_template.md`.
6. Always include RR testing when exits are part of the idea: 0.5R, 1R, 1.5R, 2R, 3R, 4R, 6R.
7. Attribute winners and losers by structure, session, volatility, trend regime, entry quality, exit failure, cost, concentration, year/month, symbol and timeframe.
8. Decide only: `keep_exploring`, `reject`, or `promote_to_candidate`.

Phase 1 must not use locked final holdout and must not claim OOS, forward-live, or decision-grade validity.

## Phase 2 Workflow

Goal: turn a promising idea into an auditable candidate.

1. Require minimal registry and `version.json`.
2. Record Git state before formal runs.
3. Freeze the candidate's current rules for a baseline.
4. Run full execution audit before using metrics for decisions.
5. Produce baseline results, RR platform analysis, and attribution.
6. For any logic/risk/exit/sizing/cost change, write a bounded change proposal and create a new version or experiment branch.
7. Re-audit after changes and compare parent vs child versions.
8. Maintain data split discipline: discovery/development data can guide iteration; locked final holdout is opened once only after rules are fixed.
9. Before freeze or runtime handoff, run bar-by-bar replay using `templates/bar_by_bar_replay_report_template.md`.
10. Decide only: `continue_iteration`, `return_to_exploration`, `reject`, or `freeze_candidate`.

Bar-by-bar replay is mandatory before Phase 3. It must compare batch vs replay signals, trades and equity, and explain every material difference.

## Phase 3 Workflow

Goal: package and verify a frozen candidate as a safe dry-run/demo runtime.

1. Require frozen candidate identity: strategy id, version, commit, config hash, and bar-by-bar replay report.
2. Create runtime handoff using `templates/runtime_handoff_template.md`.
3. Use the `mt5-runtime-packager` skill for EXE packaging, MT5 path portability, dry-run/demo safety gates, order-intent journaling, signal execution ledger, startup reconciliation and portable deliverables.
4. Default to dry-run. Demo order execution requires explicit user authorization and must remain DEMO-only with REAL hard rejection.
5. Record EXE hash, config hash, build command, runtime audit, safety state and smoke-test result.
6. Decide only: `runtime_blocked`, `dry_run_ready`, `demo_ready`, or `portable_package_ready`.

Phase 3 validates runtime behavior, not strategy profitability. Demo/runtime logs are not OOS-Final.

## Governance Gates

Apply gates by phase:

- Phase 1: fatal audit and evidence label are mandatory; full registry/data ledger is not mandatory.
- Phase 2: registry, Git/version identity, execution audit, attribution, data split discipline and bar-by-bar replay are mandatory.
- Phase 3: frozen candidate handoff, runtime safety gates, REAL rejection and portable package audit are mandatory.

If a guard blocks formal research, do not stop all work automatically. Either downgrade to Phase 1 exploration with explicit labels or ask for the missing formal artifact when the user wants decision-grade output.

## References

Load only what is needed:

- `THREE_PHASE_RESEARCH_PIPELINE.md`: primary phase model.
- `RESEARCH_WORKFLOW.md`: formal Stage 0-13 details for Phase 2+.
- `DATA_SPLIT_AND_OOS_POLICY.md`: OOS, holdout and data-consumption rules.
- `EXIT_RISK_AND_LOGIC_REFINEMENT_STANDARD.md`: execution, SL/TP, sizing, logic changes and bar-by-bar replay.
- `references/lookahead-bias-standard.md`: timing and future-data audit.
- `references/strategy-attribution-standard.md`: attribution before formal rule changes.
- `references/backtest-interpretation-standard.md`: interpreting metrics without overclaiming.
- `references/data-ledger-standard.md`: machine-readable data use guard.
- `references/frozen-baseline-registry-standard.md`: frozen candidates and archived hypotheses.
- `references/research-stage-gate-standard.md`: formal stage permissions.

## Templates

Use:

- `templates/idea_card_template.md` for Phase 1 ideas.
- `templates/quick_test_report_template.md` for Phase 1 quick tests and RR matrix.
- `templates/audit_report_template.md` for execution audits.
- `templates/logic_change_proposal_template.md` before formal Phase 2 rule changes.
- `templates/strategy_report_template.md` for candidate reports.
- `templates/bar_by_bar_replay_report_template.md` before freezing a candidate.
- `templates/runtime_handoff_template.md` before EXE/demo packaging.
- `templates/research_data_ledger.yaml`, `templates/frozen_candidates_template.yaml`, and `templates/research_stage_state.yaml` for formal governance.

## Read-Only Scripts

Scripts are diagnostic helpers, not proof of validity:

- `scripts/signal_timing_check.py`
- `scripts/session_timezone_check.py`
- `scripts/lookahead_audit.py`
- `scripts/trade_consistency_check.py`
- `scripts/data_split_ledger_check.py`
- `scripts/output_integrity_check.py`
- `scripts/report_required_fields_check.py`
- `scripts/data_ledger_guard.py`
- `scripts/frozen_registry_check.py`
- `scripts/stage_gate_check.py`

## Output Contract

Keep output phase-appropriate.

Phase 1:

- phase and evidence label;
- hypothesis tested;
- fatal audit status;
- key metrics/RR matrix summary;
- winner/loss attribution;
- decision and next iteration.

Phase 2:

- registry/version/Git status;
- audit status;
- data evidence type;
- attribution/change rationale;
- bar-by-bar replay status when near freeze;
- whether code/parameters may change;
- decision and next action.

Phase 3:

- frozen candidate identity;
- runtime handoff status;
- dry-run/demo safety status;
- REAL rejection status;
- EXE/config hash status;
- runtime decision.

Never present weak or exploratory evidence as alpha. If evidence fails, say whether to reject, iterate, downgrade to exploration, or block formal promotion.
