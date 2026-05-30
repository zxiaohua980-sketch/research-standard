# Lookahead Bias Standard

Lookahead checks answer one question: was every feature, filter, session label, execution price, and management decision knowable at the declared decision time?

## Rolling and shift rules

- Rolling indicators used on bar `t` must not include bar `t` unless the signal is explicitly evaluated after bar close.
- If the signal is executed on the next bar, features may use completed bar `t`; the fill cannot be the same close.
- If the signal is evaluated intrabar, features must come from ordered tick/event data available before order submission.
- Any rolling feature used for entry should show whether it was shifted and what timestamp it represents.

## Current bar inclusion

Current high, low, close, range, candle color, and session final statistics are future data until the bar or session is complete. If such fields influence an entry, the entry must occur after they are known.

## Future high/low/close

Columns with names such as `future_high`, `future_low`, `next_close`, `max_forward`, `target_hit`, `label`, or `outcome` are labels or diagnostics. They must not be used as entry features or filters.

## ZigZag and swing confirmation

ZigZag, swing high/low, pivot, liquidity sweep, and structure break features often require delayed confirmation. Record:

- the raw price event time;
- the confirmation time;
- the earliest signal time;
- whether the strategy uses the raw event or the confirmed event.

Using a confirmed swing as if it was known at the swing bar is lookahead.

## Session statistics

Session high, low, range, volume, or sweep labels must be timestamped. A London session high is not known until London session has ended unless the rule uses only the running high up to current time.

## Label leakage

Event-study outcome columns must be physically separated from feature columns when possible. If not, reports must state which columns are labels and confirm they were excluded from strategy logic.

## Entry time validation

Audit every dataset with:

- `signal_time < entry_time` for event-driven entries;
- `signal_bar_index < entry_bar_index` for bar-close execution;
- no same-bar close fill when the signal uses that close;
- clear exception only for tick/event strategies with ordered timestamps and latency assumptions.
