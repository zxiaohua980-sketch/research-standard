# Quick Test Report

- idea_id:
- strategy_id:
- phase: phase_1_exploration
- evidence_grade: exploratory_not_decision_grade
- generated_at:
- code_ref:
- config_ref:
- data_range:
- data_evidence_type: development_exploration

## Core Metrics

| metric | value |
|--------|-------|
| trades | |
| win_rate | |
| avg_win_R | |
| avg_loss_R | |
| EV_R | |
| PF | |
| max_drawdown_R | |
| max_consecutive_losses | |
| top_5pct_removed_EV_R | |
| cost_sensitivity | |

## RR Test Matrix

| target_R | trades | hit_rate | breakeven_win_rate | EV_R | PF | max_dd_R | top_5pct_removed_EV_R |
|----------|--------|----------|--------------------|------|----|----------|------------------------|
| 0.5 | | | | | | | |
| 1.0 | | | | | | | |
| 1.5 | | | | | | | |
| 2.0 | | | | | | | |
| 3.0 | | | | | | | |
| 4.0 | | | | | | | |
| 6.0 | | | | | | | |

## Attribution Notes

- profitable structures:
- losing structures:
- profitable sessions:
- losing sessions:
- volatility regimes:
- trend regimes:
- entry failure modes:
- exit failure modes:
- concentration risk:

## Decision

```text
keep_exploring | reject | promote_to_candidate
```

Rationale:
