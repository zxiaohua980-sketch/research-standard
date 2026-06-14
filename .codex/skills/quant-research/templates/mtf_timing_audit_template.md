# MTF Timing Audit

- strategy_id:
- version:
- phase: phase_2_candidate_iteration
- generated_at:
- git_commit:
- config_hash:
- audit_status: PASS | FAIL | WARN_ONLY
- evidence_grade: candidate_timing_validation
- strict_audit_mode: yes/no

## Timeframes

| timeframe | source | label_semantics | bar_open_field | bar_close_field | available_at_rule | timezone |
|-----------|--------|-----------------|----------------|-----------------|-------------------|----------|
| | | open_time/close_time/unknown | | | | |

## Availability Assertions

| assertion | rows_checked | failures | status |
|-----------|--------------|----------|--------|
| bar_open_time <= feature_available_at <= signal_time <= execution_time | | | PASS/FAIL |
| MT5 bar_close_time = next_bar_open_time | | | PASS/FAIL |
| feature_available_at <= decision_time | | | PASS/FAIL |
| htf_bar_close_time <= decision_time | | | PASS/FAIL |
| no incomplete HTF bar used | | | PASS/FAIL |

## Pivot / Swing / Structure Integrity

Required when ZigZag, pivot, swing, fractal, divergence, market structure, range breakout or
liquidity-sweep confirmation is used.

```text
pivot_iloc <= pivot_detect_iloc <= confirm_iloc <= signal_iloc <= current_iloc
```

| field/check | present | violations | status |
|-------------|---------|------------|--------|
| pivot_iloc / pivot_time | | | PASS/FAIL/NA |
| pivot_detect_iloc / pivot_detect_time | | | PASS/FAIL/NA |
| confirm_iloc / confirm_time | | | PASS/FAIL/NA |
| signal_iloc / signal_time | | | PASS/FAIL/NA |
| ordering assertion | | | PASS/FAIL/NA |

## Boundary Samples

Review rows around higher-timeframe rollovers.

| decision_time | ltf_bar | htf_feature_time | htf_available_at | expected_visible_htf_bar | actual_used_htf_bar | status |
|---------------|---------|------------------|------------------|--------------------------|---------------------|--------|
| | | | | | | |

## Static Pattern Review

| pattern | count | explanation | blocking |
|---------|-------|-------------|----------|
| shift(-n) | | | yes/no |
| merge_asof forward/nearest | | | yes/no |
| bfill/backfill | | | yes/no |
| centered rolling | | | yes/no |
| open-time HTF forward fill | | | yes/no |
| ZigZag/pivot/swing/fractal confirmation | | | yes/no |

## Batch vs Incremental Feature Diff

| feature | batch_rows | replay_rows | mismatch_rows | max_abs_diff | status |
|---------|------------|-------------|---------------|--------------|--------|
| | | | | | |

## Decision

```text
PASS | FAIL | PASS_WITH_EXPLAINED_WARNINGS
```

## Blocking Fixes

- item:
- required_fix:
- downstream_results_to_regenerate:
