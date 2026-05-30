# Microstructure and Liquidity Standard

Market microstructure research must separate narrative from measurable effect. A liquidity sweep story is not alpha until event timing, distribution, execution feasibility, and costs are tested.

## Session context

For London and New York session studies, declare:

- timezone;
- session boundary;
- DST handling;
- whether the session high/low is completed or running;
- whether the rule can act before the session completes.

## Liquidity sweep

For a sweep event, record:

- reference high/low source;
- sweep timestamp;
- sweep distance;
- close back inside/outside condition;
- confirmation delay;
- earliest tradable signal time.

## Failed breakout

Define breakout level, breakout confirmation, failure condition, and retest logic. Do not label a failed breakout using future reversal information unless the strategy waits for that confirmation.

## Inventory transition

If using inventory or session transition ideas, define observable proxies: range expansion, absorption, failed continuation, spread/volume proxy, or cross-symbol divergence. Do not infer dealer inventory without measurable evidence.

## Volatility expansion and decay

Measure pre-event volatility, post-event MFE/MAE, range expansion, and decay horizon. Expansion that arrives after entry but cannot be predicted is not an entry feature.

## Cross-symbol confirmation

For EURUSD, GBPUSD, USDJPY, XAUUSD, and related crosses, align timestamps and timezones. Cross-symbol confirmation must be available before the decision time and must not use later bars from another feed.

## Narrative control

Every microstructure claim must be translated into:

- timestamped event;
- executable rule candidate;
- counterfactual comparison;
- cost-adjusted distribution;
- failure criteria.
