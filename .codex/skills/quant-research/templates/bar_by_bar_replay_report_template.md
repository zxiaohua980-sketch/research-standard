# Bar-by-Bar Replay Report

- strategy_id:
- version:
- phase: phase_2_candidate_iteration
- generated_at:
- batch_backtest_ref:
- replay_engine_ref:
- config_hash:
- data_range:
- evidence_grade: candidate_engine_validation

## Replay Rules

- signal timing:
- entry timing:
- bid/ask convention:
- SL/TP collision policy:
- gap policy:
- cost model:
- state persistence model:
- duplicate signal prevention:

## Diff Summary

| check | batch | replay | diff | status |
|-------|-------|--------|------|--------|
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
- [ ] no same-bar ideal fill
- [ ] no illegal SL/TP direction
- [ ] same-bar SL/TP collision follows frozen policy
- [ ] no duplicate open for the same completed signal bar
- [ ] state does not drift across bars
- [ ] batch vs replay trade differences are explained
- [ ] PnL differences are within declared cost/slippage/gap model

## Decision

```text
PASS | FAIL | PASS_WITH_EXPLAINED_DIFFERENCES
```
