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

## Replay Rules

- signal timing:
- entry timing:
- bid/ask convention:
- SL/TP collision policy:
- gap policy:
- cost model:
- MTF available_at rule:
- state persistence model:
- duplicate signal prevention:

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

## Exceptions

| item | expected | actual | explanation | accepted |
|------|----------|--------|-------------|----------|

## Required Pass Items

- [ ] no lookahead/data leakage
- [ ] no incomplete higher-timeframe bar leakage
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
