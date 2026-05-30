# Failure Case Examples

Use these examples to prevent weak evidence from being repackaged as alpha.

## No directional event drift

A liquidity sweep event study shows MFE and final return distributions centered near zero across 5, 10, 20, and 40 bars. The correct delivery is `REJECT` or `WEAK`, not a strategy backtest.

## Gross positive but net negative

Gross expectancy is positive before spread and slippage, but net expectancy becomes negative under realistic costs. The correct conclusion is that the market behavior is not executable under the stated cost model.

## One year contributes all profit

Full-sample net profit is positive, but one year contributes nearly all gains while other years are flat or negative. The report should mark regime dependence and avoid claiming stable alpha.

## MFE and MAE both too large

Events show high MFE, but MAE is equally large and often occurs first. The effect may be directional in hindsight but not tradable with acceptable risk unless a new hypothesis explains timing.

## OOS failure

IS and OOS-Dev look acceptable, but locked_final_holdout fails after the candidate is fixed. The current version fails. Do not patch and reuse the same final holdout.

## Audit failure

Backtest metrics look strong, but `signal_time` equals `entry_time` while using same-bar close and high/low fields. The correct output is `AUDIT_FAIL`; performance metrics are not decision-grade.
