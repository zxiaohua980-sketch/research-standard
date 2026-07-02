# MTF Lookahead and Version Isolation Standard

## Purpose

This standard fixes two blocking risks in MT5/FX research:

1. multi-timeframe backtests may silently use higher-timeframe bars that were not complete at
   the lower-timeframe decision time;
2. a strategy version may accidentally read another version's backtest data, reports, cache or
   records because files are loosely named or stored in shared output folders.
3. a new version may accidentally continue editing the parent version's code or reuse the
   parent conversation context, causing version and reasoning contamination.

For Phase 2+ work, either risk makes the result non-decision-grade. A candidate cannot be
frozen, handed to runtime packaging, or used for OOS/forward claims until both gates pass.
For hard contamination findings (cross-version path or loose shared-output name), candidate
classification is blocked (`version_isolation_unverified`) rather than merely downgraded.

When the task is explicitly audit, hardening, lookahead repair, replay-difference
investigation, or candidate approval, also follow `STRICT_AUDIT_ENFORCEMENT_STANDARD.md`.
That mode allows only minimal safety patches and forbids performance optimization or
strategy-logic changes inside the audit patch.

---

## 0. Global Time Model

Every MTF, replay or execution audit must enforce:

```text
bar_open_time <= feature_available_at <= signal_time <= execution_time
```

For MT5 OHLC data:

```text
bar_close_time = next_bar_open_time
```

The current unfinished bar is not closed. A signal generated from a completed bar can execute
no earlier than the next executable quote/bar unless ordered tick/event data proves otherwise.

If a project uses `available_at` as the field name, treat it as `feature_available_at` and
preserve that value in signals/trades/audit rows.

---

## 1. Multi-Timeframe Timing Contract

Every dataset used by a multi-timeframe strategy must define timestamp semantics before any
result is trusted.

Required fields or equivalent metadata:

| Field | Meaning |
|-------|---------|
| `timeframe` | Source bar timeframe, for example `M15`, `M30`, `H1`, `H4`, `D1` |
| `bar_open_time` | Time when the source bar starts |
| `bar_close_time` | Time when the source bar is complete |
| `feature_available_at` / `available_at` | Earliest time the feature can be used by the decision engine |
| `source_file_hash` | Hash of the raw/source file or immutable snapshot |
| `timezone` | Broker/server timezone or normalized UTC policy |

If timestamp semantics are unknown, the safe default is:

```text
Use only the prior fully completed higher-timeframe bar.
```

Open-time-labeled higher-timeframe bars are especially dangerous. An H1 row labeled `10:00`
usually describes the full `10:00-11:00` bar. It is not available to an M15 signal at `10:15`,
`10:30` or `10:45`.

---

## 2. MTF Availability Rule

For every signal row and every derived feature:

```text
feature_available_at <= decision_time
```

For bar-close strategies:

- the current lower-timeframe decision bar may be used only after it is complete;
- the earliest market execution is the next executable quote/bar;
- a higher-timeframe feature may be used only after that higher-timeframe bar is complete;
- if a higher-timeframe close and lower-timeframe decision close share the same timestamp, the
  higher-timeframe feature may be used only when the data vendor's close-time labeling is proven;
- if labeling is unverified, shift the higher-timeframe feature by one full higher-timeframe bar.

Forbidden MTF joins and transforms:

- `merge_asof(..., direction="forward")`;
- `merge_asof(..., direction="nearest")` unless followed by an explicit `available_at <= decision_time` assertion;
- backfill (`bfill`) of higher-timeframe values into earlier lower-timeframe rows;
- forward-filling an open-time-labeled higher-timeframe row before its close;
- centered rolling windows;
- negative shifts such as `shift(-1)`;
- using current day/session high/low before that day/session is complete;
- using ZigZag, pivot, swing, fractal or divergence confirmation before the confirmation delay is complete.

Allowed pattern:

```text
1. compute source bar close/available time explicitly;
2. join lower-timeframe decision rows to higher-timeframe features with backward-asof on available_at;
3. store source_htf_bar_close_time and feature_available_at in signal/trade outputs;
4. assert feature_available_at <= decision_time for every row.
```

---

## 2A. Pivot / Swing / Structure Integrity

Any MTF strategy that uses ZigZag, pivot, swing, fractal, divergence, market structure,
range breakout or liquidity-sweep confirmation must prove the structure was detectable before
the signal:

```text
pivot_iloc <= pivot_detect_iloc <= confirm_iloc <= signal_iloc <= current_iloc
pivot_time <= pivot_detect_time <= confirm_time <= signal_time <= current_time
```

Signals must carry or be traceable to:

- `pivot_iloc`
- `pivot_time`
- `pivot_detect_iloc`
- `pivot_detect_time`
- `confirm_iloc`
- `confirm_time`
- `signal_iloc`
- `signal_time`

If these fields are missing, record the status as `structure_timing_unverified / not
decision-grade`. If ordering is violated, fail the audit as `LOOKAHEAD_LEAK_DETECTED`.

---

## 3. MTF Audit Requirements

Any Phase 2+ strategy using more than one timeframe must produce `mtf_timing_audit.md` or an
equivalent section inside `execution_audit.md`.

Required checks:

| Check | Blocking if failed |
|-------|--------------------|
| Timestamp semantics declared for each timeframe | yes |
| Higher-timeframe `available_at <= decision_time` assertion passes for every signal | yes |
| Boundary samples around HTF close times are manually reviewed | yes |
| Batch feature values match incremental/bar-by-bar feature values | yes |
| No forward/nearest/bfill/negative-shift pattern is unexplained | yes |
| Signal output stores source HTF close/available time | yes |
| Global time model `bar_open_time <= feature_available_at <= signal_time <= execution_time` passes | yes |
| Pivot/swing/structure timing metadata is present and ordered, if applicable | yes |
| Timezone/session conversion is documented | yes |

If the audit finds a lookahead defect, all downstream metrics generated from that engine are
invalid and must be regenerated after the fix.

---

## 4. Bar-by-Bar Replay Upgrade

For MTF strategies, bar-by-bar replay must recompute higher-timeframe features incrementally
from raw lower-timeframe or raw higher-timeframe bars. It must not preload a fully completed
future higher-timeframe feature table and then replay lower-timeframe rows against it.

The replay report must include:

- `mtf_feature_diff`: batch higher-timeframe features vs replay-time visible features;
- `signal_diff`: batch signals vs replay signals;
- `trade_diff`: batch trades vs replay trades;
- `equity_diff`: batch equity/PnL vs replay equity/PnL;
- a boundary sample table for at least several higher-timeframe rollovers.

If normal batch backtest and bar-by-bar replay differ materially, the default decision is:

```text
FAIL - candidate returns to Phase 2 iteration
```

Differences may be accepted only when every difference is traced to a declared conservative
execution/cost/gap policy and not to future information, state drift or cross-version data.

---

## 5. One Version, One Folder（强制）

Every Phase 2+ candidate version must have its own version root. Backtest outputs, reports,
audit files, caches and runtime handoff records from one version must not be used by another
version's backtest engine.

When opening a new Phase 2+ version:

1. create a new `versions/<new_version>/` subdirectory;
2. copy the parent version's active `.py` file into the new version as a new standalone file;
3. write `NEW_VERSION_HANDOFF.md` or equivalent context entry;
4. use a new Codex thread/conversation for the new version, or explicitly restart context from
   the handoff and mark `context_contamination_risk`;
5. re-audit the copied baseline before modifying the new version.

Before formal iteration starts on the new version, perform a **context purge**:

- move non-active context artifacts for previous versions (for example old `PROJECT_STATE.md`,
  old `NEW_VERSION_HANDOFF.md`, old `CLEANUP_LOG.md` references, loose `idea_note` / `history_context`)
  into `<new_version_root>/_trash_review/context/`;
- do not keep stale context files as active references for the new version;
- log purge artifacts + timestamps in `CLEANUP_LOG.md` and record `context_reset_status` as
  `new_thread`, `context_restarted_from_handoff`, or `context_contamination_risk`.

Required structure:

```text
strategy_root/
  versions/
    v0_1/
      version_manifest.yaml
      NEW_VERSION_HANDOFF.md
      CLEANUP_LOG.md
      src/
        strategy_v0_1.py
      config/
      data/
        input_manifest.yaml
      backtests/
        run_YYYYMMDDTHHMMSSZ_<run_id>/
      audits/
      reports/
      cache/
      logs/
      comparisons/
      _trash_review/
    v0_2/
      version_manifest.yaml
      ...
  shared_market_data/
    README.md
```

Allowed shared input:

- immutable raw market data snapshots under a declared shared data root;
- each shared snapshot must be read-only by convention and recorded with source, date range and hash.

Forbidden cross-version input (hard blocked in Phase 2+):

- reading `versions/v0_1/backtests/` while running `versions/v0_2`;
- editing the parent version's active `.py` when the intended work is a child version;
- reading another version's `reports/`, `cache/`, `logs/`, `trades.csv` or `signals.csv` as a backtest input;
- relying on loose names such as `latest.csv`, `final.csv`, `best.csv`, `new.csv`, `copy`, `副本`, or `saved_runs`;
- hard-coding an absolute path to an older version's output;
- writing Phase 2+ outputs outside the active version root.

### 5A. Physical Isolation Naming Contract

To prevent version confusion, file-level writes/readbacks in Phase 2+ must include version/root in path:

- `backtests/`, `reports/`, `audits/`, `cache/`, `logs/` under `versions/<version>/`;
- `run_YYYYMMDDTHHMMSSZ_<run_id>/` for backtest run folders;
- no bare filenames for reusable evidence (including `latest`, `final`, `best`, `new`, `copy`, `副本`, `saved_runs`).

Any code/path that uses loose names is treated as mixed-version evidence and must be moved to
`_trash_review/` before the version is promoted.

## 5B. Context Purge Contract (Phase 2+)

Context reset is part of phase integrity. Only one active context may drive a version:

- current `NEW_VERSION_HANDOFF.md` and current `PROJECT_STATE.md` (if present) are permitted as
  the active context entry;
- previous versions' context files and notes must be quarantined under
  `version_root/_trash_review/<timestamp>/context/`;
- unresolved `context_contamination_risk` blocks freeze/runtime handoff until a new context entry
  and cleanup evidence are recorded.

Version comparison is allowed only as a reporting task. The comparison tool may read frozen
summary manifests from parent versions, but it must not feed parent-version trades, signals,
cache or reports into the current version's backtest calculation.

---

## 6. Version Manifest

Each Phase 2+ version root must contain `version_manifest.yaml`.

Minimum fields:

```yaml
strategy_id:
version:
parent_version:
version_root:
created_at:
git_commit:
config_hash:
code_hash:
active_config:
allowed_input_roots:
  - current_version_data
  - immutable_shared_market_data
forbidden_input_roots:
  - other_version_backtests
  - other_version_reports
  - other_version_cache
  - loose_saved_runs
output_root:
active_py_file:
parent_active_py_file_hash:
new_version_handoff:
context_reset_status:
data_snapshot_hashes:
batch_backtest_ref:
bar_by_bar_replay_ref:
mtf_timing_audit_ref:
version_isolation_check_ref:
evidence_label:
cleanup_log_ref:
```

If this manifest is missing for Phase 2+ work, the result is blocked from formal promotion.

`context_reset_status` must be one of:

```text
new_thread
context_restarted_from_handoff
context_contamination_risk
```

`context_contamination_risk` is allowed for emergency continuation, but blocks freeze/runtime
handoff until the version is re-audited from the handoff in a clean context.

---

## 7. Path Guard Requirements

Every formal backtest or replay runner should accept an explicit `--version-root` argument or
equivalent config field. Before reading or writing files, it must resolve absolute paths and
enforce:

```text
all outputs are under version_root
all mutable inputs are under version_root
shared inputs are immutable and hash-declared
no path resolves under a sibling versions/<other_version> folder
```

If a script cannot prove these path rules, its result must be labeled:

```text
version_isolation_unverified
not decision-grade
```

Legacy projects do not need to be deleted. Keep old files as read-only historical evidence,
then create a clean `versions/<new_version>/` folder for the next formal candidate.

---

## 7A. Cleanup Guard

Phase 2+ runners and reports must not leave loose temporary outputs that can be mistaken for
formal evidence. Before committing or comparing a version:

- delete obvious temporary files (`__pycache__`, `.pyc`, `.tmp`, partial failed outputs, debug dumps);
- move uncertain files to `version_root/_trash_review/<timestamp>/`;
- record cleanup in `CLEANUP_LOG.md` or a report cleanup section;
- never delete raw market data snapshots, ledgers, manifests, audit/replay/attribution reports,
  frozen artifacts, forward-live logs, or runtime order/reconciliation evidence without explicit
  user approval and an archival note.

---

## 8. Required Outputs

| Phase/Stage | Required output |
|-------------|-----------------|
| Phase 1 MTF quick test | fatal timing note; label `exploratory_not_decision_grade` |
| Stage 2 / Phase 2 MTF candidate | `mtf_timing_audit.md` |
| Phase 2 every candidate version | `version_manifest.yaml` |
| Phase 2 formal backtest/replay | `version_isolation_check.json` |
| Phase 2 freeze gate | `bar_by_bar_replay_report.md` with `mtf_feature_diff` when MTF is used |
| Phase 3 runtime handoff | frozen version root and hashes copied into runtime handoff |

The controlling rule is simple:

```text
If the engine could have seen the future, or the version could have read another version's
files, the result is not trusted.
```
