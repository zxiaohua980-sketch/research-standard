# Broker Cost Model Standard / 默认交易费用模型

## Purpose

This file records the user's default MT5 research/runtime cost model so it does not need to
be restated in every strategy conversation.

Use this model whenever a task needs a default broker-cost assumption, unless an audited
strategy/version config explicitly overrides it. Any override must be written in that
version's config/report and compared against this default.

## Cost Components

For research metrics, costs must be stored as positive deductions:

```text
net_r = gross_r - spread_r - slippage_r - commission_r
cost_r = spread_r + slippage_r + commission_r
```

Do not mix signs silently. Report whether each cost field is positive cost or signed PnL.

## Default Commission Rule

| Symbol class | Commission |
|---|---:|
| XAUUSD, BTCUSD | 0 USD / lot / closed trade |
| All other symbols | 7 USD / lot / closed trade |

Commission conversion should use MT5 symbol specs when possible:

```text
usd_per_price_unit_per_lot = trade_tick_value / trade_tick_size
commission_price_units = commission_usd_per_lot / usd_per_price_unit_per_lot
commission_r = commission_price_units / initial_risk_price
```

If `trade_tick_value` or `trade_tick_size` is missing, formal cost-sensitive results are
blocked until the missing symbol value is registered or verified.

## Default Round-Turn Spread Assumptions

The following spread values are **round-turn / both-way** price-unit assumptions.

| Symbol class | Round-turn spread in price units |
|---|---:|
| EURUSD | 0.00002 |
| USDJPY / direct JPY pair | 0.002 |
| Other USD direct FX pairs | 0.00004 |
| JPY crosses, e.g. AUDJPY/EURJPY/GBPJPY/CADJPY/NZDJPY/CHFJPY | 0.004 |
| Other non-JPY crosses, e.g. EURCHF/EURNZD/EURGBP/GBPNZD | 0.00004 |
| XAUUSD, BTCUSD | must be explicitly configured; use larger symbol-specific values and no commission |

Interpretation notes:

- "Other USD direct FX pairs" includes symbols such as `GBPUSD`, `AUDUSD`, `NZDUSD`,
  `USDCAD`, `USDCHF`, except `EURUSD` and `USDJPY` which have explicit rows above.
- Crosses are non-USD FX pairs. JPY crosses use the wider 0.004 assumption.
- XAUUSD and BTCUSD do not use the FX table. They require explicit spread/slippage values in
  the project cost profile because the user requires wider symbol-specific costs.

## Slippage Rule

The default model is:

```text
spread + slippage + commission
```

Slippage is a separate cost component and must not be hidden inside spread unless the report
explicitly states that the quoted spread assumption already includes slippage.

For formal decision-grade research, every version must declare `slippage_price_units` per
symbol or symbol class. If slippage is not declared, mark the result
`cost_model_incomplete / not decision-grade`.

## Runtime vs Research Usage

Runtime order placement should use live bid/ask prices and current spread for actual order
price/SL/TP adjustment. The default research spread table is for historical-cost simulation,
stress tests, and pre-runtime comparability.

For MT5 pending-order runtimes:

- long market/buy-stop entry pays ask-side spread;
- short sell-stop entry and short exits must be ask/bid aware;
- record live `spread_price`, `spread_points`, commission rule, slippage assumption, and
  actual broker commission/swap/fee when available.

## Required Fee Check

Every cost-sensitive backtest or runtime reconciliation report should include or be able to
produce a fee check with at least:

```text
symbol, trades, gross_r, net_r,
commission_r, spread_r, slippage_r, cost_r,
gross_minus_cost, net_diff,
commission_rule_ok, spread_rule_ok, slippage_rule_ok,
spread_price_units, slippage_price_units,
commission_usd_per_lot, cost_source
```

Minimum checks:

1. XAUUSD/BTCUSD commission must be zero or effectively zero.
2. Non-XAU/BTC symbols must apply 7 USD/lot commission unless an audited override exists.
3. Spread must match the class table above or a registered symbol-specific override.
4. Slippage must be declared and deducted separately, or the result is cost-incomplete.
5. `net_r ≈ gross_r - spread_r - slippage_r - commission_r` within the declared tolerance.
6. Unregistered/fallback live-spread-only symbols must be labelled and cannot be used for
   formal cost-sensitive ranking.

