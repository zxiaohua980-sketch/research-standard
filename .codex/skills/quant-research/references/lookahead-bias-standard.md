# Lookahead Bias Standard

Lookahead checks answer one question: was every feature, filter, session label, execution price, and management decision knowable at the declared decision time?

Strict audit uses the global time model:

```text
bar_open_time <= feature_available_at <= signal_time <= execution_time
```

For MT5 OHLC, treat `bar_close_time` as the next bar's open time. A completed-bar signal may
execute only on the next executable quote/bar unless ordered tick/event data proves otherwise.

## Rolling and shift rules

- Rolling indicators used on bar `t` must not include bar `t` unless the signal is explicitly evaluated after bar close.
- If the signal is executed on the next bar, features may use completed bar `t`; the fill cannot be the same close.
- If the signal is evaluated intrabar, features must come from ordered tick/event data available before order submission.
- Any rolling feature used for entry should show whether it was shifted and what timestamp it represents.

## Current bar inclusion

Current high, low, close, range, candle color, and session final statistics are future data until the bar or session is complete. If such fields influence an entry, the entry must occur after they are known.

## Multi-timeframe features

Higher-timeframe bars must be timestamped by their actual close/available time, not by a
misleading open-time label. For every lower-timeframe decision row, assert:

```text
feature_available_at <= decision_time
```

If timestamp semantics are unknown, use only the prior fully completed higher-timeframe bar.
Do not forward-fill an H1/H4/D1 row labeled by open time into lower-timeframe rows before that
higher-timeframe bar has closed. `merge_asof` must join backward on `available_at`; forward,
nearest, backfill, centered rolling and negative shifts are blocking unless explicitly proven
safe by the MTF timing audit.

## Future high/low/close

Columns with names such as `future_high`, `future_low`, `next_close`, `max_forward`, `target_hit`, `label`, or `outcome` are labels or diagnostics. They must not be used as entry features or filters.

## ZigZag and swing confirmation

ZigZag, swing high/low, pivot, liquidity sweep, and structure break features often require delayed confirmation. Record:

- the raw price event time;
- the pivot detect time;
- the confirmation time;
- the earliest signal time;
- whether the strategy uses the raw event or the confirmed event.

Using a confirmed swing as if it was known at the swing bar is lookahead.

For pivot/structure signals, enforce:

```text
pivot_iloc <= pivot_detect_iloc <= confirm_iloc <= signal_iloc <= current_iloc
```

## Session statistics

Session high, low, range, volume, or sweep labels must be timestamped. A London session high is not known until London session has ended unless the rule uses only the running high up to current time.

## Label leakage

Event-study outcome columns must be physically separated from feature columns when possible. If not, reports must state which columns are labels and confirm they were excluded from strategy logic.

## Entry time validation

Audit every dataset with:

- `signal_time < entry_time` for event-driven entries;
- `signal_bar_index < entry_bar_index` for bar-close execution;
- no same-bar close fill when the signal uses that close;
- for MTF signals, no `source_htf_close_time` or `feature_available_at` later than the decision time;
- clear exception only for tick/event strategies with ordered timestamps and latency assumptions.
