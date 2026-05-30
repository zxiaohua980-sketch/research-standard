# Session and Timezone Standard

Session errors are a common source of hidden lookahead. Treat timezone and session labels as auditable data.

## Time fields

Record source timezone for every timestamp:

- UTC;
- broker server time;
- local machine time;
- exchange or market convention time if used.

Do not mix timezone-naive and timezone-aware timestamps without explicit conversion.

## Session boundaries

For Asia, London, New York, rollover, and custom sessions, define:

- start time;
- end time;
- timezone;
- whether boundaries are inclusive or exclusive;
- how cross-day sessions are assigned to dates.

## DST

London and New York DST changes must be handled explicitly. A fixed UTC hour may not match a local session across the whole year.

## Daily rollover

Broker daily candles may roll at New York close, UTC midnight, or server midnight. Daily features must state which convention was used.

## Weekend gaps

Weekend bars and Monday open gaps must be tagged. Do not treat weekend gap movement as tradable intrabar movement unless the broker provided executable quotes.

## Cross-day sessions

Sessions that cross midnight must preserve start-date and end-date logic. A signal late in NY session must not use the completed next-day session summary.

## Audit method

Check:

- timezone column presence;
- session label presence;
- suspicious timestamps at boundaries;
- session high/low fields computed after the signal;
- differences between broker time and UTC conversion.
