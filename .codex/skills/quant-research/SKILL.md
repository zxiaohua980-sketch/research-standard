---
name: quant-research
description: Three-phase research operating system for MT5 and FX quantitative strategy work. Use when Codex works on exploratory alpha hypothesis testing, OHLC/tick backtests, strict audit enforcement, future-function/lookahead repair, multi-timeframe timing audits, pivot/swing/structure integrity, version-folder isolation, new-version active-Python-file copying, new thread/context reset for version iteration, temporary-file cleanup, win-rate/RR testing, MFE/MAE attribution, bar-by-bar replay determinism, OOS/holdout governance, forward-live boundaries, or preparing a frozen candidate for MT5 dry-run/demo/live runtime packaging.
---

# Quant Research

## Purpose

Use this skill to move trading ideas through a phase-aware research pipeline:

1. **Phase 1 - Quick exploration**: turn hypotheses into code, fatal-audit the obvious traps, run quick tests, RR tests, and multi-dimensional attribution. Results are exploratory only.
2. **Phase 2 - Candidate iteration**: register promising ideas, isolate each version folder, audit execution/MTF timing, compare versions, perform attribution-driven changes, and require bar-by-bar replay before freeze.
3. **Phase 3 - EXE demo/live runtime handoff**: hand a frozen candidate to MT5 runtime packaging with dry-run/demo safety gates and, when the user explicitly authorizes it, a controlled `live_trade` real-money path.

Keep the system research-first: Phase 1 should stay fast and lightly gated; Phase 2 should
be version-isolated and auditable; Phase 3 should be strict. Do not turn registry or ledger
work into busywork that blocks hypothesis coding, attribution, and iteration.

Use **Strict Audit Enforcement Mode** whenever the task is audit, hardening, future-function
repair, replay-difference investigation, candidate approval, MTF/pivot/execution safety, or
runtime safety review. In that mode, do audit-only minimal patches and do not optimize
performance or change strategy intent.

This skill may help propose, quantify, implement, test, reject, and iterate exploratory strategy hypotheses. It must not present unverified exploration as alpha, OOS, forward-live, or live-ready evidence. Live trading is a user capital decision; Codex should enforce technical safeguards, not impose a blanket ban once the user explicitly authorizes live use.

## Authority Boundary

First read the nearest project `AGENTS.md`. If available, also read the strategy registry.

- If `AGENTS.md` conflicts with this skill, obey `AGENTS.md`.
- If a strategy is unregistered, Phase 1 exploration can continue with `templates/idea_card_template.md`, but formal Phase 2+ research is blocked until a minimal registry record exists.
- If a Phase 2+ version lacks its own `versions/<version>/` root and manifest, formal metrics are blocked as `version_isolation_unverified`.
- If a Phase 2+ new version has not copied the parent active `.py` into its own version root, formal metrics are blocked as `active_py_not_isolated`.
- If a Phase 2+ new version reused an old long conversation without a new thread or handoff restart, mark `context_contamination_risk`.
- If a multi-timeframe strategy lacks MTF timing evidence, formal metrics are blocked as `mtf_timing_unverified`.
- If an audit task has not satisfied Strict Audit Enforcement Mode, promotion/approval is blocked as `strict_audit_unverified`.
- Do not touch frozen or forward-live strategy code in place.
- Do not place REAL orders or enable REAL-account trading unless the user explicitly authorizes this specific runtime and the package satisfies `LIVE_TRADING_AUTHORIZATION_STANDARD.md`; never treat demo/runtime logs as OOS-Final evidence.
- Clean temporary and invalid outputs promptly, but never delete raw data, manifests, audits,
  frozen/forward logs, runtime order/reconciliation evidence, or user-supplied source files
  without explicit approval and an archival note.

## Phase Classifier

Before acting, classify the task:

| Phase | Use when | Registry | Evidence label |
|------|----------|----------|----------------|
| Phase 1 exploration | new hypothesis, quick code, quick backtest, RR test, MFE/MAE, loss attribution | optional | `exploratory_not_decision_grade` |
| Phase 2 candidate iteration | promising idea, isolated version root, formal audit, MTF timing audit, logic change, parameter/RR platform, bar-by-bar replay | required | `candidate_not_final` until freeze/holdout |
| Phase 3 runtime packaging | frozen candidate, EXE, dry-run/demo/live scan/order execution, runtime safety | required | `runtime_validation_not_oos_final` or `live_trial_active` when user-authorized REAL trading starts |

If the phase is unclear, choose the lowest-risk phase and state the assumption.

## Strict Audit Enforcement Mode

Trigger this mode for: audit, verify, harden, approve, fix future-function/lookahead,
ordinary-vs-bar-by-bar mismatch, batch-vs-incremental mismatch, MTF timing, pivot/swing/
structure confirmation, execution timing, survivorship, data/version contamination, or runtime
safety.

Allowed:

- fix lookahead/leakage, time alignment, missing time metadata, assertions, replay checks,
  and version/data path guards;
- add or update audit reports and templates;
- remove only dead parameters that are definitely not decision logic.

Forbidden:

- change entry/exit logic, indicators, formulas, parameters, RR, PF, win rate, trade count,
  or optimization objective;
- mix audit fixes with strategy improvement;
- relabel invalid old metrics as decision-grade.

Required checks:

- `bar_open_time <= feature_available_at <= signal_time <= execution_time`;
- MT5 `bar_close_time = next_bar_open_time`;
- no future indices, negative shifts, centered windows, current unclosed bar, or same-bar
  signal/execution for bar-close systems;
- MTF features use completed higher-timeframe bars only and store `feature_available_at`;
- pivot/swing/structure signals satisfy detect/confirm/signal ordering;
- batch and incremental replay match or fail as `REPAINTING_OR_LOOKAHEAD_FAIL`;
- universe omissions and version/cached-input paths are reported.

Output: `AUDIT_STATUS`, issue list, file/function locations, minimal patches only, and
`batch_vs_incremental` replay result (`PASS`, `FAIL`, `NOT_RUN`, or `NOT_APPLICABLE`).

## Phase 1 Workflow

Goal: find whether a profit mechanism may exist.

1. Create or update `idea_card.md` using `templates/idea_card_template.md`.
2. Quantify the hypothesis: market, symbol, timeframe, target win rate, target RR, expected trade count, entry, SL, TP, invalidation.
3. Implement the smallest testable code when asked; keep it separate from frozen/live code.
4. Run a fatal audit before trusting even exploratory output:
   - no future data or same-bar ideal fill;
   - no incomplete higher-timeframe bar used in lower-timeframe decisions;
   - global time model `bar_open_time <= feature_available_at <= signal_time <= execution_time`;
   - pivot/swing/structure confirmation is complete before signal, if applicable;
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
At the end of each quick iteration, delete obvious temporary files and failed partial outputs.
Keep only the smallest code/config/result summary needed for the next attribution loop.

## Phase 2 Workflow

Goal: turn a promising idea into an auditable candidate.

1. Require minimal registry, `version.json`, and one isolated `versions/<version>/` root.
2. When opening a new version, create a new subdirectory, copy the parent active `.py` into a
   new standalone active `.py` file, and do not modify the parent active `.py`.
3. Start a new thread/conversation for the child version; if unavailable, create
   `NEW_VERSION_HANDOFF.md` and restart context from it, marking `context_contamination_risk`.
4. Record Git state before formal runs.
5. Freeze the copied baseline's current rules, then re-audit before changing logic.
6. Run full execution audit before using metrics for decisions.
7. For audit/hardening/approval tasks, apply Strict Audit Enforcement Mode before any optimization or promotion.
8. If MTF/resampling/higher-timeframe features are used, run `templates/mtf_timing_audit_template.md` and block unless `feature_available_at <= decision_time` is proven.
9. Run version isolation check before formal backtests; outputs must stay inside the active version root and mutable inputs must not come from sibling versions.
10. Produce baseline results, RR platform analysis, and attribution.
11. For any logic/risk/exit/sizing/cost change, write a bounded change proposal and create a new version or experiment branch.
12. Re-audit after changes and compare parent vs child versions.
13. Clean temporary/invalid outputs, move uncertain files to `_trash_review/`, and record `CLEANUP_LOG.md`.
14. Maintain data split discipline: discovery/development data can guide iteration; locked final holdout is opened once only after rules are fixed.
15. Before freeze or runtime handoff, run bar-by-bar replay using `templates/bar_by_bar_replay_report_template.md`.
16. Decide only: `continue_iteration`, `return_to_exploration`, `reject`, or `freeze_candidate`.

Bar-by-bar replay is mandatory before Phase 3. It must compare batch vs replay MTF features, signals, trades and equity, and explain every material difference.

## Phase 3 Workflow

Goal: package and verify a frozen candidate as a safe dry-run/demo runtime, or as a user-authorized `live_trade` runtime when the user explicitly accepts real-money risk.

1. Require frozen candidate identity: strategy id, version, version root, commit, config hash, MTF timing audit if applicable, version isolation check, and bar-by-bar replay report.
2. Create runtime handoff using `templates/runtime_handoff_template.md`.
3. Use the `mt5-runtime-packager` skill for EXE packaging, MT5 path portability, dry-run/demo/live safety gates, order-intent journaling, signal execution ledger, startup reconciliation and portable deliverables.
4. Default to dry-run. Demo order execution requires explicit user authorization. REAL order execution is allowed only when the user explicitly requests live/实盘 and `config.ini` has `mode=live_trade`, `allow_live_trade=true`, and `live_trade_ack=I_ACCEPT_REAL_MONEY_RISK`.
5. Record EXE hash, config hash, build command, runtime audit, safety state and smoke-test result.
6. Decide only: `runtime_blocked`, `dry_run_ready`, `demo_ready`, `user_authorized_live_ready`, `live_trial_active`, or `portable_package_ready`.

Phase 3 validates runtime behavior, not strategy profitability. Demo/runtime logs are not OOS-Final. User-authorized live logs are real-money operational evidence from activation time onward, not backtest/OOS-Final proof.

## Governance Gates

Apply gates by phase:

- Phase 1: light gates only: fatal audit, evidence label, independent exploration file/folder,
  and cleanup of obvious temporary outputs. Full registry/data ledger is not mandatory.
- Phase 2: version gates: minimal registry milestone, Git/version identity, isolated version
  root, copied active `.py`, context reset/handoff, execution audit, MTF timing audit when
  applicable, attribution, cleanup log, data split discipline and bar-by-bar replay.
- Phase 3: strict gates: frozen candidate handoff, strict audit clean status, runtime safety
  gates, explicit live authorization when applicable, portable package audit and clean deliverable folder.

If a guard blocks formal research, do not stop all work automatically. Either downgrade to Phase 1 exploration with explicit labels or ask for the missing formal artifact when the user wants decision-grade output.

## References

Load only what is needed:

- `THREE_PHASE_RESEARCH_PIPELINE.md`: primary phase model.
- `STRICT_AUDIT_ENFORCEMENT_STANDARD.md`: audit-only minimal-patch mode for lookahead, MTF, pivot/swing, execution, replay and version contamination defects.
- `RESEARCH_WORKFLOW.md`: formal Stage 0-13 details for Phase 2+.
- `DATA_SPLIT_AND_OOS_POLICY.md`: OOS, holdout and data-consumption rules.
- `EXIT_RISK_AND_LOGIC_REFINEMENT_STANDARD.md`: execution, SL/TP, sizing, logic changes and bar-by-bar replay.
- `MTF_LOOKAHEAD_AND_VERSION_ISOLATION_STANDARD.md`: MTF timing availability, bar-by-bar feature diffs, one-version-one-folder rules and path isolation.
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
- `templates/new_version_handoff_template.md` when opening a Phase 2+ child version.
- `templates/audit_report_template.md` for execution audits.
- `templates/strict_audit_enforcement_report_template.md` for audit-only/minimal-patch reviews.
- `templates/mtf_timing_audit_template.md` for multi-timeframe timing audits.
- `templates/version_isolation_manifest_template.yaml` for Phase 2+ version roots.
- `templates/cleanup_log_template.md` for Phase 2+ file hygiene.
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
- `scripts/mtf_lookahead_audit.py`
- `scripts/version_isolation_check.py`
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
- active `.py` copy status;
- context reset/new thread status;
- audit status;
- strict audit status if the task is audit/hardening/approval;
- MTF timing audit status, if applicable;
- version root/isolation status;
- data evidence type;
- attribution/change rationale;
- bar-by-bar replay status when near freeze;
- cleanup status;
- whether code/parameters may change;
- decision and next action.

Strict audit responses must include:

- `AUDIT_STATUS`: `PASS`, `FAIL`, or `CONDITIONAL_PASS`;
- issues by category: lookahead, repainting, MTF leakage, execution timing, survivorship,
  data/version contamination, cost model, runtime safety;
- exact file/function locations;
- minimal patches only, or `no_patch_applied`;
- `batch_vs_incremental`: `PASS`, `FAIL`, `NOT_RUN`, or `NOT_APPLICABLE`.

Phase 3:

- frozen candidate identity;
- runtime handoff status;
- dry-run/demo safety status;
- live authorization / account gate status;
- EXE/config hash status;
- runtime decision.

Never present weak or exploratory evidence as alpha. If evidence fails, say whether to reject, iterate, downgrade to exploration, or block formal promotion.
