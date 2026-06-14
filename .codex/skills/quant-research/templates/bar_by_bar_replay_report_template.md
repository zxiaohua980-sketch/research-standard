# Bar-by-Bar Replay Report

- strategy_id:
- version:
- phase: phase_2_candidate_iteration
- generated_at:
- batch_backtest_ref:
- replay_engine_ref:
- config_hash:
- version_root:
- version_isolation_check:
- mtf_timing_audit:
- data_range:
- evidence_grade: candidate_engine_validation
- strict_audit_mode:

## Replay Rules

- signal timing:
- entry timing:
- global time model (`bar_open_time <= feature_available_at <= signal_time <= execution_time`):
- bid/ask convention:
- SL/TP collision policy:
- gap policy:
- cost model:
- MTF available_at rule:
- state persistence model:
- duplicate signal prevention:
- pivot/swing/structure timing fields, if applicable:

## Diff Summary

| check | batch | replay | diff | status |
|-------|-------|--------|------|--------|
| mtf_feature_count | | | | |
| mtf_feature_mismatch_rows | | | | |
| signal_count | | | | |
| trade_count | | | | |
| net_pnl_R | | | | |
| max_drawdown_R | | | | |
| final_equity | | | | |

## Batch vs Incremental Decision Trace

```text
batch_vs_incremental: PASS | FAIL | NOT_RUN | NOT_APPLICABLE
```

| decision_time | batch_signal | incremental_signal | mismatch_type | blocking | explanation |
|---------------|--------------|--------------------|---------------|----------|-------------|
| | | | missing/extra/direction/entry_sl_tp/timestamp/state_drift | yes/no | |

Unexplained mismatch category:

```text
REPAINTING_OR_LOOKAHEAD_FAIL
```

## Exceptions

| item | expected | actual | explanation | accepted |
|------|----------|--------|-------------|----------|

## Required Pass Items

- [ ] no lookahead/data leakage
- [ ] no incomplete higher-timeframe bar leakage
- [ ] global time model assertion passes
- [ ] pivot/swing/structure detect-confirm-signal order is valid, if applicable
- [ ] MTF `feature_available_at <= decision_time` assertion passes, if applicable
- [ ] no same-bar ideal fill
- [ ] no illegal SL/TP direction
- [ ] same-bar SL/TP collision follows frozen policy
- [ ] no duplicate open for the same completed signal bar
- [ ] state does not drift across bars
- [ ] batch vs replay trade differences are explained
- [ ] batch vs replay MTF feature differences are explained, if applicable
- [ ] PnL differences are within declared cost/slippage/gap model
- [ ] no cross-version backtest/report/cache/log input is used

## Decision

```text
PASS | FAIL | PASS_WITH_EXPLAINED_DIFFERENCES
```
