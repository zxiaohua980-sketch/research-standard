# Survivorship Bias Standard

Survivorship bias appears whenever losing opportunities, failed executions, inactive symbols, missing periods, or incomplete trades are silently removed.

## Missing or skipped trades

Check whether the backtest removed:

- trades that hit SL before a valid entry was recorded;
- duplicate signals that would have created conflicts;
- rejected orders;
- trades with missing exit prices;
- trades with large negative slippage;
- trades crossing rollover or weekend boundaries.

Removed rows must be reported with counts and reasons.

## Open positions

End-of-sample open positions must be reported separately. Forced liquidation, mark-to-market, or exclusion must be declared before metrics are calculated.

## Failed orders

If an order is rejected because of stops level, freeze level, volume step, margin, off quotes, or invalid price, it is part of execution evidence. Do not exclude failed orders when evaluating live feasibility.

## Duplicate signals

Duplicate signals may be real strategy conflicts. Track whether duplicates were ignored, merged, netted, hedged, or treated as separate entries.

## Symbol and universe gaps

For EURUSD, GBPUSD, USDJPY, XAUUSD, and other instruments, record:

- symbol suffixes and broker feed changes;
- missing history periods;
- tick size/value changes;
- contract specification changes;
- spread regime changes;
- inactive or delisted symbols if the study expands beyond major FX.

## Sample truncation

Do not choose start/end dates because they make performance look better. If a sample starts after a known bad period or ends before a drawdown, state that explicitly.

## Abnormal data

Abnormal spikes, zero spreads, duplicated bars, weekend bars, and missing sessions must be counted. Cleaning rules must be written before seeing performance impact.
