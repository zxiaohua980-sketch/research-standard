# New Version Handoff

- strategy_id:
- parent_version:
- new_version:
- created_at:
- version_root:
- parent_active_py:
- parent_active_py_hash:
- new_active_py:
- git_base_commit:
- intended_change_family:
- intended_change_summary:
- evidence_label: candidate_not_final

## Context Reset

```text
context_reset_status: new_thread | context_restarted_from_handoff | context_contamination_risk
context_purge_status: PASS | BLOCK
context_purge_dir:
```

- new_thread_id_or_note:
- prior_thread_summary_ref:
- archived_old_context_refs:
- context_files_to_read_first:
  - version_manifest.yaml
  - config/
  - execution_audit.md
  - mtf_timing_audit.md
  - attribution_report.md

## Baseline Copy Checklist

- [ ] new `versions/<new_version>/` subdirectory created
- [ ] parent active `.py` copied into new version as standalone active `.py`
- [ ] parent active `.py` not modified
- [ ] config copied or explicitly regenerated
- [ ] allowed input roots declared
- [ ] forbidden sibling-version outputs declared
- [ ] copied baseline re-audit planned before logic changes

## Initial Audit Requirements

- execution_audit:
- mtf_timing_audit, if applicable:
- version_isolation_check:
- strict_audit_required:

## Cleanup Rules

- cleanup_log:
- trash_review_dir:
- files that must not be deleted:

## Next Action

```text
copy_baseline_audit | implement_single_change | run_attribution | reject_version | other
```
