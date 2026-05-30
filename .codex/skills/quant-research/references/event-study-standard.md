# Event Study Standard

Event study comes before strategy evaluation whenever the user proposes a market behavior, pattern, liquidity event, session event, or microstructure story.

## Event definition

Define:

- event type;
- symbol;
- timeframe;
- event time;
- direction;
- confirmation rule;
- earliest signal time;
- exclusion rules;
- data split.

## Counterfactual control

Use a baseline such as random timestamps, non-event bars, opposite direction events, prior sessions, or matched volatility regimes. If no counterfactual exists, mark the result exploratory.

## Required horizons

For each event, report 5, 10, 20, and 40 bar outcomes:

- MFE;
- MAE;
- final return;
- hit rate;
- direction;
- symbol;
- year;
- session;
- distribution diagnostics.

## Distribution first

Do not rely only on averages. Report median, quartiles, tails, sample count, and outlier contribution. A mean positive result with unstable distribution is weak evidence.

## Segmentation

Segment by:

- symbol;
- direction;
- year;
- London/NY/Asia session;
- volatility regime;
- pre-event trend;
- spread/cost regime when available.

## Failure standard

Event study can formally fail. Failures include no directional shift, high MAE equal to MFE, cost-adjusted decay, unstable yearly behavior, or label leakage. A failed event study should stop strategy evaluation unless a new hypothesis is written.
