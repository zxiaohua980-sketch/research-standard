# Strict Audit Enforcement Report

## A. AUDIT_STATUS

```text
PASS | FAIL | CONDITIONAL_PASS
```

- strategy_id:
- version:
- phase:
- generated_at:
- git_commit:
- config_hash:
- version_root:
- audit_scope:
- read_only:
- patch_applied: yes/no
- metrics_decision_grade: yes/no

## B. Issues List

| category | status | blocking | evidence | required_action |
|----------|--------|----------|----------|-----------------|
| lookahead | PASS/FAIL/WARN/NA | yes/no | | |
| repainting | PASS/FAIL/WARN/NA | yes/no | | |
| MTF leakage | PASS/FAIL/WARN/NA | yes/no | | |
| execution timing errors | PASS/FAIL/WARN/NA | yes/no | | |
| survivorship bias | PASS/FAIL/WARN/NA | yes/no | | |
| data/version contamination | PASS/FAIL/WARN/NA | yes/no | | |
| file hygiene / temporary output contamination | PASS/FAIL/WARN/NA | yes/no | | |
| cost model incompleteness | PASS/FAIL/WARN/NA | yes/no | | |
| runtime safety failure | PASS/FAIL/WARN/NA | yes/no | | |

## C. File + Function Locations

| file | function/section | inspected | issue_category | notes |
|------|------------------|-----------|----------------|-------|
| | | yes/no | | |

## D. Minimal Patches Only

| patch | file | function/section | defect_fixed | strategy_logic_changed | notes |
|-------|------|------------------|--------------|------------------------|-------|
| | | | | must be no | |

If no patch was applied:

```text
no_patch_applied
```

## E. Global Time Model

Required invariant:

```text
bar_open_time <= feature_available_at <= signal_time <= execution_time
```

| check | rows/signals checked | failures | status |
|-------|----------------------|----------|--------|
| bar_open_time <= feature_available_at | | | |
| feature_available_at <= signal_time | | | |
| signal_time <= execution_time | | | |
| MT5 bar_close_time = next_bar_open_time | | | |

## Pivot / Swing / Structure Integrity

Required invariant:

```text
pivot_iloc <= pivot_detect_iloc <= confirm_iloc <= signal_iloc <= current_iloc
```

| required_field | present | violations | status |
|----------------|---------|------------|--------|
| pivot_iloc | | | |
| pivot_time | | | |
| pivot_detect_iloc | | | |
| pivot_detect_time | | | |
| confirm_iloc | | | |
| confirm_time | | | |
| signal_iloc | | | |
| signal_time | | | |

## Replay Consistency Result

```text
batch_vs_incremental: PASS | FAIL | NOT_RUN | NOT_APPLICABLE
```

| mismatch_type | count | examples | blocking |
|---------------|-------|----------|----------|
| missing signals | | | |
| extra signals | | | |
| direction mismatch | | | |
| entry/SL/TP mismatch | | | |
| timestamp mismatch | | | |
| state drift | | | |

## Survivorship / Universe Control

- full_configured_universe:
- actually_available_symbols:
- missing_symbols:
- insufficient_history_symbols:
- timeframe_coverage_gaps:
- skipped_symbols_with_reasons:

## Data / Version Isolation

- active_version_root:
- active_py_file:
- parent_active_py_copied: yes/no/NA
- context_reset_status: new_thread/context_restarted_from_handoff/context_contamination_risk/NA
- mutable_inputs_under_version_root: yes/no
- outputs_under_version_root: yes/no
- immutable_shared_data_hashes:
- sibling_version_inputs_found: yes/no
- loose_latest_final_copy_saved_runs_found: yes/no

## File Hygiene / Cleanup

- cleanup_log_ref:
- obvious_temp_files_deleted: yes/no
- uncertain_files_moved_to_trash_review: yes/no/NA
- trash_review_dir:
- protected_evidence_preserved:
  - raw_data:
  - ledgers:
  - manifests:
  - audit_replay_attribution_reports:
  - frozen_forward_runtime_logs:

## Conclusion

- final_objective_status:
  - deterministic:
  - no_lookahead:
  - replay_validated:
  - time_consistent:
  - version_isolated:
  - production_safe:
- allowed_next_action:
- blocked_next_action:
