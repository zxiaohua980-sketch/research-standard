# Data Contracts

Use these contracts before marking any research output as decision-grade. If required fields are missing, the report must say `not decision-grade` until the missing fields are supplied or justified.

## trade_detail required fields

Required identity and timing fields:

- `trade_id`
- `strategy_id`
- `strategy_version`
- `symbol`
- `timeframe`
- `signal_time`
- `entry_time`
- `exit_time`
- `side`
- `volume`

Required price and execution fields:

- `entry_price`
- `exit_price`
- `entry_bid` or `entry_ask`
- `exit_bid` or `exit_ask`
- `initial_sl`
- `initial_tp`
- `exit_reason`

Required risk and cost fields:

- `initial_risk`
- `pnl`
- `pnl_R`
- `spread`
- `commission`
- `slippage`
- `swap`

Required diagnostic fields:

- `MFE_R`
- `MAE_R`
- `bars_held`
- `session`
- `timezone`
- `data_split`

## signal/event required fields

- `event_id` or `signal_id`
- `symbol`
- `timeframe`
- `event_time`
- `signal_time`
- `signal_bar_index`
- `direction`
- `event_type`
- `session`
- `timezone`
- `features_available_at_signal_time`
- `data_split`

## event_study required fields

- `event_id`
- `symbol`
- `event_time`
- `direction`
- `year`
- `session`
- `timezone`
- `mfe_5`
- `mae_5`
- `final_return_5`
- `hit_rate_5`
- `mfe_10`
- `mae_10`
- `final_return_10`
- `hit_rate_10`
- `mfe_20`
- `mae_20`
- `final_return_20`
- `hit_rate_20`
- `mfe_40`
- `mae_40`
- `final_return_40`
- `hit_rate_40`

## summary required fields

- `strategy_id`
- `version`
- `git_commit`
- `config_hash`
- `data_hash`
- `data_range`
- `symbols`
- `timeframe`
- `timezone`
- `evidence_type`
- `audit_status`
- `generated_at`
- `decision_grade`

## audit_output required fields

- `script_name`
- `script_version`
- `generated_at_utc`
- `read_only`
- `input_files`
- `input_hashes`
- `row_counts`
- `checks`
- `overall_status`

Each check must contain `id`, `status`, `severity`, and `message`. Valid status values are `PASS`, `FAIL`, `WARN`, and `INFO`.
