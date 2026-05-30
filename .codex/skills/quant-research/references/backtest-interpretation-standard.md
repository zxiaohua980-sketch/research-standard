# Backtest Interpretation Standard

Backtest metrics are not conclusions until execution, data, and output integrity audits pass.

## Win rate

Win rate alone is not alpha. Interpret it with average win, average loss, cost model, holding time, and tail dependence. A high win rate with rare large losses may be fragile.

## Profit factor

Profit factor must be shown gross and net of costs. PF is unstable with small samples and may be dominated by one or two large winners.

## Average R

Average R is meaningful only if initial risk is defined before entry and never redefined after breakeven or trailing changes. Report median R and distribution tails.

## MFE and MAE

MFE/MAE explain path quality. Large MFE with poor final return may indicate late exits. Large MAE for winners may indicate stops are too tight or entries are early. MFE/MAE are post-entry diagnostics, not direct filters unless transformed into realtime rules.

## Monthly stability

Monthly returns should include zero-trade months. Do not remove quiet months or bad months. Report worst month and longest flat period.

## Yearly consistency

If one year contributes most net profit, the strategy is regime-dependent or sample-fragile. A positive full sample with one dominant year is not robust evidence.

## Cost sensitivity

Run or request sensitivity to spread, commission, slippage, and swap when material. A strategy that fails under modest cost increases is not decision-grade.

## Small samples

For fewer than 30 trades, report only exploratory evidence. For 30-50 trades, report weak evidence unless supported by independent forward-live or strong event-level distributions. Never add filters based on tiny cohorts.

## Required interpretation labels

Use one of:

- `DECISION_GRADE`
- `EXPLORATORY_ONLY`
- `WEAK`
- `REJECT`
- `AUDIT_FAIL`
- `NOT_DECISION_GRADE`
