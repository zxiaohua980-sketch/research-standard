# MT5 Runtime Packager v1.1.4 Governance Change Audit

Date: 2026-06-14

## Scope

This governance/skill update corrects MT5 bid/ask spread adjustment rules for market/open entries,
Buy Stop/Sell Stop pending entries, Stop Loss and Take Profit. It does not change any strategy
logic, parameters, backtest result, forward-live evidence, or registry strategy state.

Affected files:

- `D:\MT5\RESEARCH_STANDARD\MT5_RUNTIME_PACKAGING_STANDARD.md`
- `D:\MT5\RESEARCH_STANDARD\.codex\skills\mt5-runtime-packager\SKILL.md`
- `D:\MT5\RESEARCH_STANDARD\.codex\skills\mt5-runtime-packager\templates\config_cost_inclusive_pending_orders.ini`
- `D:\MT5\RESEARCH_STANDARD\.codex\skills\mt5-runtime-packager\scripts\mt5_runtime_common.py`
- `D:\MT5\RESEARCH_STANDARD\.codex\skills\mt5-runtime-packager\scripts\audit_mt5_runtime_package.py`
- `D:\MT5\RESEARCH_STANDARD\.codex\skills\mt5-runtime-packager\references\mt5-runtime-common-code.md`
- `D:\MT5\RESEARCH_STANDARD\.codex\skills\mt5-runtime-packager\agents\openai.yaml`

## User Correction Captured

The user asked to re-check spread add/subtract rules for:

- long entries;
- short entries;
- Buy Stop;
- Sell Stop;
- Stop Loss;
- Take Profit.

The user also corrected that if execution is at open/market price, the runtime must not manually
add spread to the order request. It should directly execute on the broker price.

## Correct Default Model

For MT5 bid-chart raw levels:

```text
MARKET / OPEN ENTRY
BUY  entry = current tick.ask
SELL entry = current tick.bid

PENDING ENTRY
BUY_STOP / BUY_LIMIT   entry = raw_entry + spread
SELL_STOP / SELL_LIMIT entry = raw_entry

ATTACHED SL/TP
BUY  SL = raw_sl
BUY  TP = raw_tp
SELL SL = raw_sl + spread
SELL TP = raw_tp + spread
```

The previous symmetric conservative policy is no longer the default. It is kept only as a
legacy/testing concept and should not be used for order-capable MT5 packages unless explicitly
documented and audited as intentionally non-exact.

## Config Changes

Added/required side-specific fields:

```ini
[orders]
signal_price_basis = bid_chart
pending_price_policy = broker_bidask_from_bid_chart
sltp_price_policy = broker_bidask_from_bid_chart
adjust_buy_pending_entry_for_spread = true
adjust_sell_pending_entry_for_spread = false
adjust_buy_sltp_for_spread = false
adjust_sell_sltp_for_spread = true
```

Market/open entry fields remain:

```ini
entry_execution_mode = market
market_entry_price_policy = broker_tick_side_no_manual_spread
market_entry_use_tick_side = true
spread_adjust_market_entry = false
spread_risk_accounting = actual_fill_no_extra_spread
```

## Code Helpers Added

`mt5_runtime_common.py` now includes:

- `market_entry_price_from_tick(...)`
- `bid_chart_to_mt5_order_prices(...)`

These helpers do not initialize MT5 and do not send orders.

## Audit Changes

The package audit now requires:

- market/open entries use broker tick side and avoid manual `raw_open +/- spread`;
- pending/SL/TP spread config is side-specific;
- `conservative_full_spread` is not accepted as the default MT5 order policy for order-capable
  packages.

## Validation

Required validation:

- skill validation;
- Python compile for helper and audit scripts;
- config template parse;
- helper unit-style checks for BUY/SELL market entry and bid-chart pending/SL/TP conversion;
- `git diff --check`;
- local installed skill synchronized from the repo copy.

## Residual Risk

These are default FX/CFD bid-chart rules. Exchange symbols can have Last-price trigger rules, so a
runtime handling exchange stocks/futures must explicitly declare a different `signal_price_basis`
and audit the broker symbol's trigger mode before packaging.
