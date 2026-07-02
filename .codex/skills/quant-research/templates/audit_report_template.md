# Read-Only Audit Report

## Metadata

- audit_id:
- script_versions:
- audited_artifacts:
- generated_at:
- git_commit:
- version_root:
- active_py_file:
- context_reset_status:
- read_only: true
- strict_audit_mode: yes/no
- strict_audit_report_ref:

## Input Integrity

- input files:
- input hashes:
- row counts:
- schema status:

## Output Integrity

- output files:
- output hashes:
- generated timestamps:
- overwrite risk:
- version isolation status:

## Checks

| Check ID | Description | Status | Severity | Evidence | Blocking |
|----------|-------------|--------|----------|----------|----------|
| | | PASS/FAIL/WARN | | | yes/no |

## Required Audit Areas

- global_time_model (`bar_open_time <= feature_available_at <= signal_time <= execution_time`):
- MT5_bar_close_equals_next_open:
- signal_time / entry_time:
- bar index ordering:
- current bar inclusion:
- MTF feature available_at:
- MTF boundary samples:
- pivot/swing/structure detect-confirm-signal order:
- bid/ask and costs:
- SL/TP direction:
- same-bar SL/TP collision:
- session/timezone:
- data split ledger:
- version folder isolation:
- active `.py` copied for new version:
- file hygiene / cleanup:
- survivorship/missing rows:
- output required fields:
- batch_vs_incremental_replay:
- context purge evidence:

## Strict Audit Enforcement

Use this section when the task is audit, lookahead repair, replay-difference investigation,
candidate approval, or safety hardening.

- AUDIT_STATUS: PASS | FAIL | CONDITIONAL_PASS
- minimal_patch_only: yes/no
- performance_or_strategy_logic_changed: must be no
- old_downstream_metrics_invalidated: yes/no
- blocking_categories:
  - LOOKAHEAD_LEAK_DETECTED:
  - MULTI_TIMEFRAME_LOOKAHEAD_DETECTED:
  - REPAINTING_OR_LOOKAHEAD_FAIL:

## Manual Sample Review

- sampled rows:
- sample method:
- findings:

## Blocking Items

- item:
- why blocking:
- required fix before decision-grade:

## Conclusion

- audit_status: PASS | FAIL | WARN_ONLY | CONDITIONAL_PASS
- metrics_decision_grade: yes | no
- allowed next action:
