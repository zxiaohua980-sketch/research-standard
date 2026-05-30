# Machine-Readable Data Ledger Standard

Data ledger is the first line of defense against research set contamination. A dataset is not clean because its filename says `OOS`; it is clean only if the ledger proves it has not been used for discovery, selection, parameter tuning, or post-failure patching.

## Required principle

Before any event study, backtest, attribution, optimization, OOS report, walk-forward review, freeze, or forward-live evaluation, load the ledger and answer:

- Which dataset ids will be read?
- What research stage is reading them?
- What usage type is requested?
- Has each dataset already been consumed?
- Will this action consume a new data layer?
- Is the claimed evidence type still valid after this use?

If no machine-readable ledger exists, mark the run `legacy_or_untracked` and do not call the result decision-grade.

## Required dataset fields

Each dataset entry must include:

- `dataset_id`
- `symbols`
- `timeframe`
- `date_range`
- `timezone`
- `source_path`
- `data_hash`
- `usage_type`
- `research_stage`
- `evidence_role`
- `consumed`
- `use_count`
- `first_used_at`
- `last_used_at`
- `used_by`
- `notes`

## Evidence roles

Valid `evidence_role` values:

- `discovery_train`
- `development_validation`
- `locked_final_holdout`
- `wf_oos`
- `forward_live`
- `diagnostic_only`
- `legacy_unverified`

## Usage types

Valid `usage_type` values:

- `hypothesis_generation`
- `event_study`
- `baseline_backtest`
- `execution_audit`
- `trade_attribution`
- `logic_selection`
- `parameter_search`
- `dev_validation`
- `locked_final_evaluation`
- `walk_forward_diagnostic`
- `forward_live_collection`
- `reporting_only`

## Consumption rules

- `discovery_train` may be consumed repeatedly, but never proves final validity.
- `development_validation` may screen candidates; after screening, it is consumed development data.
- `locked_final_holdout` may be opened once for a fully fixed candidate. Any second opening is blocking.
- `wf_oos` is historical diagnostic evidence, not final holdout or forward-live.
- `forward_live` must start after `framework_start_time` and must never include backfilled history.

## Gate behavior

If the requested action conflicts with the ledger:

- block formal research;
- output a failure or guard report;
- do not run strategy logic unless the user explicitly marks the run as temporary exploratory work;
- never silently rename consumed data as OOS-Final.
