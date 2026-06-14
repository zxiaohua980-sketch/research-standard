# Strict Audit Enforcement Standard

## Purpose

This standard defines the mandatory audit-only mode for trading-system safety work. It
converts the hedge-fund-grade auditor prompt into a governance rule that fits the existing
three-phase research framework.

Use this standard whenever the task is to audit, verify, harden, minimally patch, or approve
a trading system, backtest engine, signal engine, replay engine, MT5 runtime, multi-timeframe
join, pivot/swing/structure detector, or execution model.

This is **not** an alpha-discovery or performance-improvement workflow. It is an enforcement
mode that prevents invalid results from being trusted.

---

## Relationship To Existing Governance

This standard does not replace:

- `THREE_PHASE_RESEARCH_PIPELINE.md`;
- `RESEARCH_WORKFLOW.md`;
- `DATA_SPLIT_AND_OOS_POLICY.md`;
- `EXIT_RISK_AND_LOGIC_REFINEMENT_STANDARD.md`;
- `MTF_LOOKAHEAD_AND_VERSION_ISOLATION_STANDARD.md`;
- `BROKER_COST_MODEL_STANDARD.md`;
- `MT5_RUNTIME_PACKAGING_STANDARD.md`.

Instead, it sits above them when the immediate task is audit or safety repair:

```text
User asks audit / bug fix / hardening / approval
  -> enter Strict Audit Enforcement Mode
  -> no performance optimization
  -> minimal patches only
  -> regenerate downstream evidence after any timing/leakage fix
```

Existing Phase 1 exploration may continue only after the audit result is labelled correctly.
Existing Phase 2/3 promotion, freeze, runtime handoff, OOS, forward-live, or demo-ready
claims are blocked until this audit mode has no blocking failures.

---

## 1. Allowed And Forbidden Actions

### Allowed

Codex may only:

- fix lookahead or leakage bugs;
- fix time alignment issues;
- add missing time metadata;
- add safety assertions and fail-fast checks;
- add read-only audit reports;
- add replay consistency checks;
- remove clearly unused dead parameters that are not part of decision logic;
- update documentation/templates to expose the audit result.

### Forbidden

Codex must not:

- change entry or exit logic;
- change indicators or formulas;
- modify strategy intent;
- optimize profit, PF, Sharpe, drawdown, win rate, RR, trade count, or parameter score;
- combine audit fixes with strategy improvements in one patch;
- hide or relabel invalid old results as decision-grade.

If a required safety fix changes signals or performance, that is permitted only as an audit
bug fix. The new metrics are not an optimization result; they are the corrected reality.

---

## 2. Global Time Model

Every trading system must satisfy:

```text
bar_open_time <= feature_available_at <= signal_time <= execution_time
```

For MT5 OHLC data:

```text
bar_close_time = next_bar_open_time
```

The current unfinished bar is not closed and must not be used for signal generation unless
the strategy explicitly operates on ordered tick/event data with decision and execution
timestamps.

Any violation makes the system invalid until fixed.

---

## 3. Lookahead Prohibition

Forbidden in decision logic:

- `i+1`, `i+k`, or any future index access;
- `shift(-1)` or equivalent future shift;
- forward-looking windows;
- centered rolling windows;
- future high, low, close, return, MFE, MAE, target, label or outcome columns;
- current unclosed bar for signal generation;
- same-bar signal and execution assumption for bar-close systems.

Required failure:

```python
raise RuntimeError("LOOKAHEAD_LEAK_DETECTED")
```

The failure name may be adapted to the project language/runtime, but the report must preserve
the exact category `LOOKAHEAD_LEAK_DETECTED`.

---

## 4. Pivot / Swing / Structure Integrity

All swing, pivot, fractal, ZigZag, divergence, market-structure, range-breakout, liquidity
sweep, or structural confirmation logic must satisfy:

```text
pivot_iloc <= pivot_detect_iloc <= confirm_iloc <= signal_iloc <= current_iloc
pivot_time <= pivot_detect_time <= confirm_time <= signal_time <= current_time
```

Each emitted signal must include, or be traceable to, these fields:

- `pivot_iloc`
- `pivot_time`
- `pivot_detect_iloc`
- `pivot_detect_time`
- `confirm_iloc`
- `confirm_time`
- `signal_iloc`
- `signal_time`

If a strategy does not use pivots/swings/structures, record `not_applicable`.

If any required field is missing or violates ordering, the audit status is FAIL and the
category is `LOOKAHEAD_LEAK_DETECTED`.

---

## 5. Multi-Timeframe Rules

Follow `MTF_LOOKAHEAD_AND_VERSION_ISOLATION_STANDARD.md`. In Strict Audit Enforcement Mode,
these are hard failures:

- higher-timeframe data used before its bar is fully closed;
- missing `feature_available_at`;
- `merge_asof(direction="forward")`;
- `merge_asof(direction="nearest")` without explicit availability assertion;
- `bfill` or `ffill` used for cross-timeframe decision features;
- open-time-labelled higher-timeframe rows forward-filled into lower-timeframe rows before
  the higher-timeframe close.

Required failure category:

```text
MULTI_TIMEFRAME_LOOKAHEAD_DETECTED
```

---

## 6. Execution Model Rule

For bar-close systems:

```text
signal -> confirmation after bar close -> next-bar / next-quote execution
```

Rules:

- signals are generated only after the decision bar is closed;
- execution happens at the next available executable bar/quote;
- no same-bar execution is allowed unless ordered tick/event evidence proves it;
- TP/SL must not use future bars;
- trailing, breakeven, timeout and partial exits must use only completed bars or ordered
  real-time events available before the management action.

Violations are blocking execution-timing failures.

---

## 7. Replay Consistency

Every formal candidate or audit target must be testable as:

```text
batch_run(full_data)
incremental_run(prefix_data)
```

For every decision step, batch and incremental outputs must match on:

- signal existence;
- direction;
- entry timing;
- SL/TP;
- management events;
- execution timing;
- signal metadata and timestamps.

Mismatch categories:

- missing signals;
- extra signals;
- different direction;
- different entry/SL/TP;
- timestamp mismatch;
- state drift;
- cross-version/cache contamination.

Any unexplained mismatch is:

```text
REPAINTING_OR_LOOKAHEAD_FAIL
```

Material differences may be accepted only when caused by a documented conservative
execution/cost/gap policy, not by future information or hidden state.

---

## 8. Survivorship Bias Control

Any multi-symbol universe scan, portfolio backtest, batch test, or symbol-selection result
must explicitly report:

- full configured symbol universe;
- actually available symbols;
- missing symbols;
- symbols with insufficient history;
- timeframe coverage gaps;
- symbols skipped and the exact reason.

Silent skipping is forbidden. If unavailable symbols are omitted without reporting, the
evidence label must be:

```text
survivorship_unverified
not decision-grade
```

---

## 9. Data / Version Isolation

Follow `MTF_LOOKAHEAD_AND_VERSION_ISOLATION_STANDARD.md`. In Strict Audit Enforcement Mode,
these are hard failures:

- mixing old strategy versions;
- using external cache or loose `latest`, `final`, `copy`, `副本`, or `saved_runs`;
- cross-run contamination of signals;
- reusing historical outputs as live inputs;
- reading sibling-version backtest/report/cache/log files as calculation input;
- writing formal outputs outside the active version root.

All data must be bound to the active runtime/candidate version.

---

## 10. Dead Code Policy

Codex may identify:

- unused parameters;
- diagnostic-only metrics;
- unused caches;
- unreachable report-only branches.

Codex must not remove anything used in:

- signal generation;
- entry/exit decision logic;
- risk management;
- position sizing;
- execution timing;
- MTF joining;
- replay state.

Dead-code removal must be documented as non-decision-related. If unsure, leave it in place
and mark for manual review.

---

## 11. Hard Assertion Layer

Before emitting any formal signal, the engine should enforce equivalent assertions:

```python
assert bar_open_time <= feature_available_at <= signal_time <= execution_time
assert pivot_iloc <= confirm_iloc <= signal_iloc <= current_iloc
assert signal_time >= confirm_time
```

For strategies without pivots/swings, the pivot assertion may be replaced with the relevant
decision-time metadata assertion.

If violated, raise:

```python
RuntimeError("LOOKAHEAD_LEAK_DETECTED")
```

or the closest runtime-equivalent hard failure.

---

## 12. Minimal Patch Protocol

When a defect is found:

1. Locate file, function and line/logic area.
2. Classify the defect category.
3. Patch the smallest possible safety defect.
4. Do not change strategy intent, parameters or optimization objective.
5. Add or update assertions/tests/replay checks.
6. Mark all prior downstream metrics from the defective engine invalid.
7. Regenerate only the evidence needed to prove the defect is fixed.

Do not perform broad refactors unless the current code structure makes the safety invariant
impossible to enforce.

---

## 13. Strict Output Contract

Every strict audit response/report must include:

### A. AUDIT_STATUS

```text
PASS | FAIL | CONDITIONAL_PASS
```

`CONDITIONAL_PASS` means non-blocking warnings remain and are explicitly listed; no formal
promotion may occur if any blocking category remains.

### B. Issues List

Report each category:

- lookahead;
- repainting;
- MTF leakage;
- execution timing errors;
- survivorship bias;
- data/version contamination;
- cost model incompleteness, if applicable;
- runtime safety failure, if applicable.

### C. File + Function Locations

List exact files, functions, scripts or report sections inspected.

### D. Minimal Patches Only

List only audit/safety patches. If no patch was made, say `no_patch_applied`.

### E. Replay Consistency Result

State:

```text
batch_vs_incremental: PASS | FAIL | NOT_RUN | NOT_APPLICABLE
```

and explain any mismatch.

---

## Final Objective

The audited system must be:

```text
DETERMINISTIC
NO-LOOKAHEAD
REPLAY-VALIDATED
TIME-CONSISTENT
VERSION-ISOLATED
PRODUCTION-SAFE
```

If it is not all of these, it is not decision-grade.
