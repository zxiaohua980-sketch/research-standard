# STR-003 Governance Onboarding Pilot

Generated: 2026-05-30T15:30:00+08:00

This is a sidecar governance onboarding for `STR-003 / D:\MT5\openclaw\bb_strategy`. It does not modify strategy code, parameters, backtest outputs, or forward-live data.

## Scope

- Strategy: STR-003
- Root path: `D:\MT5\openclaw\bb_strategy`
- Registry stage: `stage_12_forward_live`
- Registry status: `forward_live_active`
- Frozen tag: `v0.1-frozen`
- Framework start time: `2026-05-27 00:00:00 UTC`

## Created Governance Files

- `research_data_ledger.yaml`
- `research_stage_state.yaml`
- `frozen_candidates.yaml`
- `archived_hypotheses.yaml`

## Key Findings

1. The strategy is already in Stage 12 forward-live, so no code, parameter, filter, SL/TP, sizing, or cost-model changes are allowed in place.
2. Current checked-out branch is `master`, while registry says forward-live should use `forward-v0.1`.
3. Current worktree has untracked files and reports, so formal validation must not be run from this dirty state.
4. Git tag `v0.1-frozen` points to frozen commit `e594c33`, but `version.json` reports `676986e`; this reproducibility mismatch should be resolved before formal claims.
5. The locked final holdout has already been consumed for v0.1. It must not be reused for parameter search or logic selection.

## Guard Results

### Allowed Path: `forward_live_collection`

| Guard | Result | Output |
|-------|--------|--------|
| Data Ledger Guard | PASS | `guard_results/data_ledger_forward_live.json` |
| Stage Gate Check | PASS / ALLOW | `guard_results/stage_gate_forward_live.json` |
| Frozen Registry Check | PASS | `guard_results/frozen_registry_forward_live.json` |

### Blocked Probes

| Probe | Guard | Result | Reason |
|-------|-------|--------|--------|
| `modify_parameters` | Stage Gate Check | FAIL / BLOCK | Action is blocked at `forward_live` stage. |
| `parameter_search` | Data Ledger Guard | FAIL | locked_final_holdout cannot be used for selection. |
| `modify_parameters` | Frozen Registry Check | FAIL | Action appears in frozen candidate `blocked_actions`. |

## Decision

The governance onboarding pilot is successful as a sidecar process. It demonstrates that v1.2 can allow forward-live collection while blocking parameter modification and holdout reuse.

This is not a strategy validation and not a performance review. No backtest, optimization, walk-forward, or forward-live analysis was run.

## Next Integration Step

If this pilot is accepted, move or copy the four governance YAML files into an agreed canonical location, preferably after selecting the correct branch and deciding whether governance files live inside each strategy root or a central `D:\MT5\research_registry\governance\STR-003\` directory.
