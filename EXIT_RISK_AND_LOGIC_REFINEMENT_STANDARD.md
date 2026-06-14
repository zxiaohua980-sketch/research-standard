# Entry, Exit, Risk and Logic Refinement Standard

## Purpose

This standard governs entry execution, stop loss (SL), take profit (TP), time exits,
breakeven/trailing rules, position sizing, and any logic change derived from trade
attribution. It applies across Stage 2, Stage 5, Stage 6, Stage 7, Stage 11, Stage 12 and
Stage 13.

When the immediate task is audit, lookahead repair, replay-difference investigation,
execution hardening or candidate approval, also apply `STRICT_AUDIT_ENFORCEMENT_STANDARD.md`.
In that mode, only minimal safety patches are allowed; do not combine execution fixes with
profit optimization, parameter changes or strategy-logic changes.

An exit or risk rule is part of the strategy, not a harmless implementation detail. Changing
an SL, TP, trailing rule, breakeven trigger, timeout, sizing rule, execution price model, or
cost model creates a new strategy version or experiment branch.

---

## 1. Execution Model Must Be Declared First

Before a baseline backtest is considered auditable, the strategy must declare exactly when a
decision becomes known and at what price an order could be executed.

The global time model must be explicit:

```text
bar_open_time <= feature_available_at <= signal_time <= execution_time
```

For MT5 OHLC data, `bar_close_time` is the next bar's open time. A bar-close signal is not
known until that close time and cannot execute on the same close unless ordered tick/event
evidence proves it.

If the strategy uses multiple timeframes, resampling, or higher-timeframe filters, the
decision model must also declare the source bar close time and `available_at` time for each
higher-timeframe feature. See `MTF_LOOKAHEAD_AND_VERSION_ISOLATION_STANDARD.md`.

### Bar-close strategies

Default rule for OHLC/bar-based research:

1. The signal is evaluated after `bar t` is complete.
2. The earliest market entry is the first executable quote on `bar t+1`.
3. A long market entry uses ask and a long exit uses bid.
4. A short market entry uses bid and a short exit uses ask.
5. Spread, commission, slippage and any overnight financing must be applied consistently.

Using `bar t` close both to discover a signal and as its fill price is prohibited unless
tick/event data proves the order was submitted and fillable before that price passed.

### Intrabar/tick strategies

Same-bar entry is permitted only when the signal and execution engine operate on an ordered
tick/event stream and the audit stores the exact decision timestamp, order timestamp, quote,
fill and latency/slippage assumptions.

### SL/TP hit ordering

OHLC bars do not reveal which level was reached first if a bar touches both SL and TP.
Before running the test, choose one policy:

- use ordered lower-timeframe or tick data; or
- apply the conservative rule that SL is filled first.

The choice must be frozen in the configuration. Choosing the favorable outcome or changing
the rule after seeing results invalidates the run.

### Gaps and non-fillable prices

If price gaps through an SL or TP, fill at the first executable broker-consistent quote,
including slippage, rather than at an impossible requested level. Pending-order activation,
stop levels, minimum distance, lot step, partial fills and rejections must be modelled when
material to the instrument or broker.

---

## 2. Risk Rule Declaration

Before Stage 4 fixed-rule backtest, create a risk rule declaration in the strategy config or
report. It must contain:

| Rule | Required Definition |
|------|---------------------|
| Entry timing | signal timestamp, order type, fill-price convention |
| Initial SL | structural/ATR/fixed rule, distance, placement time, long/short direction |
| Initial TP | fixed R/structure/trailing/no fixed TP, placement time |
| Position sizing | risk amount, equity basis, lot rounding, max exposure |
| Dynamic exits | breakeven, trail, partial close or timeout trigger; otherwise `none` |
| Cost model | spread, commission, slippage, swap/financing |
| Collision/gap policy | same-bar SL/TP ordering and gap fill treatment |
| Portfolio constraints | max concurrent positions and correlated exposure limits |

### Risk unit

For each trade, define initial risk before entry:

```text
initial_risk_price = abs(entry_fill_price - initial_stop_price)
initial_risk_cash  = initial_risk_price * contract_value * position_size + entry_cost_buffer
pnl_R              = net_realized_pnl / initial_risk_cash
```

Never redefine `R` after a stop moves to breakeven or trails. Otherwise exit changes can
artificially improve attribution metrics.

---

## 3. Stage 2 Execution Audit for SL/TP

No result using SL/TP may proceed unless the audit explicitly records PASS/FAIL for:

1. The signal uses only information available before order submission.
2. Entry fills follow the declared bar/tick timing and bid/ask convention.
3. Initial SL and TP are computable at order time without future high/low values.
4. Direction is legal: long SL below fill and TP above fill; short SL above fill and TP below fill.
5. Same-bar SL/TP collisions use the predeclared conservative or ordered-data rule.
6. Gaps through exits, spread, commission, slippage and swap are included or explicitly justified.
7. Broker constraints are checked for MT5 execution: tick size/value, volume step, stops level,
   freeze level, margin, filling mode, hedging/netting behavior and rejected orders.
8. Position size is derived from pre-entry risk, with portfolio exposure limits applied.
9. End-of-sample open positions and forced liquidation treatment are reported separately.
10. Backtest and forward/live engines use equivalent decision, sizing and exit conventions.
11. Multi-timeframe features, if any, satisfy `feature_available_at <= decision_time` for
    every signal and store source higher-timeframe close/available times in the output.
12. Phase 2+ outputs and mutable inputs stay inside the active `versions/<version>/` folder,
    except immutable hash-declared market data snapshots.
13. If pivots/swings/structures are used, `pivot_detect_time <= confirm_time <= signal_time`
    is recorded and enforced.
14. Any batch-vs-incremental or ordinary-vs-bar-by-bar mismatch is classified before metrics
    are trusted; unexplained mismatch is `REPAINTING_OR_LOOKAHEAD_FAIL`.

Any failed item means the reported metrics are not decision-grade.

---

## 4. Phase 2 Bar-by-Bar Replay Gate

Before a candidate strategy can be frozen or handed to runtime packaging, it must pass a
bar-by-bar replay check. A vectorized or batch backtest is not enough to prove that the
strategy can run like a live monitor.

The replay engine must simulate:

1. signal confirmation only after the completed decision bar;
2. execution only on the next allowed executable quote or bar;
3. position state updates one bar/event at a time;
4. SL/TP, gap and same-bar collision ordering according to the frozen config;
5. breakeven, trailing, timeout and partial exits using only information available at that
   decision time;
6. one completed signal bar triggering at most one open;
7. state recovery assumptions after restart;
8. the same cost, bid/ask and sizing model used by the candidate config.

The replay report must include three diffs:

| Diff | Required comparison |
|------|---------------------|
| MTF feature diff | batch higher-timeframe features vs replay-time visible higher-timeframe features, when MTF is used |
| Signal diff | batch backtest signals vs replay signals |
| Trade diff | batch backtest trades vs replay trades |
| Equity diff | batch backtest equity/PnL vs replay equity/PnL |

Passing criteria:

- signal count and trade count match, or every difference is explained;
- MTF feature values are generated from information visible at that replay step;
- entry and exit times are reproducible under the declared timing model;
- PnL differences stay within the declared spread/slippage/gap model;
- no lookahead, incomplete higher-timeframe bar use, same-bar ideal fill, duplicate open,
  illegal SL/TP direction, cross-version input or state drift;
- output `bar_by_bar_replay_report.md` before freeze.

If this gate fails, the candidate returns to Phase 2 iteration. It cannot enter EXE dry-run or
demo packaging as a frozen candidate.

---

## 5. Stage 5 Attribution for Stops and Targets

The purpose of attribution is not to tune exits while looking at losses. It is to identify a
specific, pre-declared hypothesis that can be replayed on development validation and finally
evaluated once on locked final holdout.

### Required trade fields

Every trade dataset used to assess exits must include:

```text
strategy_version, config_hash, signal_time, order_time, entry_time,
entry_bid, entry_ask, entry_fill_price, side, volume,
initial_stop_price, initial_target_price, initial_risk_cash,
exit_time, exit_fill_price, exit_reason, net_pnl, pnl_R,
MFE_R, MAE_R, bars_to_MFE, bars_to_MAE, holding_bars,
spread_paid, commission_paid, slippage_paid, swap_paid,
ante_entry_features, management_events
```

`management_events` records only actions that the rule could have made in real time, for
example `breakeven_armed_at_1R` or `trail_updated_after_closed_bar`.

### Mandatory exit cohorts

Report at least these cohorts:

| Cohort | Question Answered |
|--------|-------------------|
| Direct SL losers with low MFE | Did the entry fail immediately? |
| SL losers after meaningful MFE | Did the trade give back profit before stopping? |
| TP winners with deep MAE | Is the initial SL too tight for eventual winners? |
| Winners that never reach planned TP | Is the TP unrealistic or is timeout relevant? |
| Timeout/signal exits | Is capital trapped without reaching either boundary? |
| Large winners removed | Is expectancy dependent on rare outliers? |

Analyze counts, expectancy in R, MAE/MFE distributions, holding time, costs and ante-entry
regime features for each cohort.

### What can justify a proposed change

Post-entry measures such as MFE or MAE may diagnose a problem, but they cannot by themselves
be a future filter. A proposed management rule must be executable using information available
at its decision time.

Examples:

- Acceptable candidate: "After a completed bar closes at +1R, move SL to entry on the next
  executable quote." This can be replayed without hindsight.
- Prohibited claim: "Close before losers reach their eventual MAE." Eventual MAE is unknown.
- Acceptable candidate: "A pre-entry ATR-normalized structural stop reduces direct SL losses
  without removing deep-MAE winners in development validation."

### Dataset discipline

Use data layers consistently:

1. `discovery_train`: discover cohorts and propose one bounded candidate rule.
2. `development_validation`: replay the candidate unchanged to decide whether it may enter
   Stage 6. Once viewed, this set is not final holdout.
3. `locked_final_holdout`: used once only after all entry, exit, sizing, cost and parameter
   choices are frozen.
4. `forward_live`: generated after the freeze timestamp and never backfilled.

---

## 6. Stage 6 Logic Refinement Gate

Any proposed change must have a change record before code is modified:

```markdown
# Logic Change Proposal
- strategy_id:
- parent_version:
- proposed_version_or_branch:
- change_family: entry_filter | initial_sl | initial_tp | dynamic_exit | sizing | execution
- attribution_report:
- observed_problem:
- causal_hypothesis:
- exact_new_rule:
- information_available_at_decision_time:
- datasets_already_viewed:
- reserved_locked_final_holdout:
- expected_benefit:
- failure_criteria:
- requires_execution_reaudit: yes
```

### Change procedure

1. Identify one problem from audited Stage 5 attribution.
2. Propose one bounded rule family; do not combine several rescue changes.
3. Create a new version or experiment branch before implementation.
4. In the new version root, copy the parent active `.py` into a new standalone active `.py`
   file and write a `NEW_VERSION_HANDOFF.md` or equivalent context entry.
5. Use a new thread/conversation for the child version, or restart from the handoff and mark
   `context_contamination_risk`.
6. Re-audit the copied baseline before implementing the candidate change.
7. Implement the candidate with tests for timing, direction, sizing and collision handling.
8. Repeat Stage 2 execution audit for the changed rule.
9. Evaluate unchanged on development validation and document rejected as well as accepted candidates.
10. Clean temporary/invalid outputs and update `CLEANUP_LOG.md`.
11. Run Stage 7 parameter robustness only for an accepted rule, without reopening discarded ideas.
12. Evaluate the fully fixed candidate once on locked final holdout.
13. If holdout fails, reject the version. Do not patch it using the same holdout.

### Adjustment classification

| Change | Minimum Restart Point |
|--------|------------------------|
| Fix an execution bug or look-ahead defect | Stage 2, then regenerate all downstream results |
| Add/remove an entry filter | Stage 5 evidence, then Stage 6 onward |
| Change initial SL or TP | Stage 5 exit attribution, then Stage 6 onward and Stage 2 re-audit |
| Add trailing/breakeven/timeout/partial exit | Stage 5 exit attribution, then Stage 6 onward and Stage 2 re-audit |
| Change sizing or exposure caps | Stage 5 risk attribution plus portfolio validation; new version |
| Change spread/slippage/swap/broker mechanics | Stage 2 re-audit and regenerate all claimed results |

---

## 7. Freeze, Forward-Live and Live Safety

At Stage 11, freeze all of the following with hashes and version identifiers:

- signal and entry rules;
- fill timing and bid/ask convention;
- initial SL, TP and all dynamic management rules;
- risk unit, position sizing, exposure caps and portfolio conflict rules;
- cost and broker-execution assumptions;
- collision/gap treatment and end-of-sample handling;
- operational live safeguards and alert thresholds.

During Stage 12 forward-live, none of these may be adjusted in place. A safety control may
pause new trading or close exposure in an emergency, but it must be recorded as an operational
intervention; it cannot silently become a strategy improvement or be mixed into the frozen
strategy's performance evaluation.

Before Stage 13 live deployment, document at minimum:

- maximum risk per trade, daily loss limit, total open-risk limit and correlated-risk limit;
- kill switch behavior, duplicate-order prevention, reconnection/reconciliation behavior;
- order rejection, partial fill and stale-price handling;
- credentials/secrets handling and immutable execution logs;
- alerting and human authorization required for restarting after a safety halt.

---

## Required Outputs

| Stage | Required Output for Exit/Risk Work |
|-------|------------------------------------|
| Stage 2 | `execution_audit.md` with the SL/TP audit checklist |
| Stage 2 MTF | `mtf_timing_audit.md` or equivalent section |
| Phase 2 version isolation | `version_manifest.yaml` and `version_isolation_check.json` |
| Stage 5 | `trade_attribution_report.md` with exit cohorts |
| Stage 6 | `logic_change_proposal.md` and `logic_refinement.md` |
| Stage 7 | full candidate/parameter output with dataset ledger |
| Phase 2 freeze gate | `bar_by_bar_replay_report.md` with signal/trade/equity diffs |
| Stage 11 | frozen risk/execution manifest in `version.json` or linked manifest |
| Stage 12 | append-only signal/trade/intervention logs and integrity check |
| Stage 13 | live risk and operations runbook |

The controlling rule is simple: an exit change is a strategy change, and a strategy change
must be attributable, auditable, versioned and tested on data that was not used to invent it.
