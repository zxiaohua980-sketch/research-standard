# MT5 Runtime Packager v1.1.5 Governance Change Audit

Date: 2026-06-14

## Scope

This governance/skill update clarifies two execution-code gaps in the MT5 runtime packaging rules:

1. the exact source and sign convention for spread;
2. the required state machine when a pending order is too close to current price or is already
   triggered before the broker accepts the pending order.

This is a packaging/runtime-code governance update only. It does not change any strategy signal
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

The user clarified that the prior rule was still not clear enough about:

- whether spread is added or subtracted;
- where spread comes from;
- what to do when a Buy Stop/Sell Stop cannot be placed because the current price is too close;
- what to do when price has already broken through the intended pending entry;
- why a once-per-minute loop is insufficient for an armed pending entry.

## Correct Spread Source And Sign Rule

For order-capable live/demo runtimes, the primary spread source is:

```text
spread_price  = symbol_info_tick(symbol).ask - symbol_info_tick(symbol).bid
spread_points = spread_price / symbol.point
```

The default bid-chart conversion has no subtract-spread case:

```text
BUY market/open entry  = current tick.ask       # no manual spread adjustment
SELL market/open entry = current tick.bid       # no manual spread adjustment

BUY_STOP / BUY_LIMIT   entry = raw_entry + spread_price
SELL_STOP / SELL_LIMIT entry = raw_entry

BUY  SL/TP = raw SL/TP
SELL SL/TP = raw SL/TP + spread_price
```

Fixed spread is allowed only when explicitly configured for deterministic dry-run/backtest
diagnostics or as an audited fallback. The runtime must log spread source, bid, ask, point,
spread points, spread price, tick timestamp, and how the spread was used.

## Pending Too-Close / Already-Triggered State Machine

Pending order management must be tick-level once an intent exists:

```ini
[runtime]
pending_monitor_mode = tick
tick_poll_interval_ms = 250

[orders]
pending_too_close_policy = wait_until_valid_or_market_if_triggered
market_if_pending_triggered = true
pending_reprice_to_min_distance = false
```

For default bid-chart MT5 rules:

```text
BUY_STOP  triggered if tick.ask >= adjusted_entry
SELL_STOP triggered if tick.bid <= adjusted_entry
BUY_LIMIT triggered if tick.ask <= adjusted_entry
SELL_LIMIT triggered if tick.bid >= adjusted_entry
```

If the trigger side has already reached the adjusted entry, the runtime must stop trying to place
the pending order and convert the same signal intent to a market order. If not triggered but too
close to current price under broker `trade_stops_level`/`trade_freeze_level`, the runtime must keep
the same intent in `armed_trigger_watch` and poll ticks until the original adjusted entry becomes
placeable, triggered, expired, or quarantined. It must not create duplicate signal keys or silently
move the entry unless an explicit audited repricing policy enables that.

## Code Helpers Added

`mt5_runtime_common.py` now includes:

- `spread_price_from_tick(...)`
- `min_pending_distance_from_symbol_info(...)`
- `pending_entry_state_from_tick(...)`

The helpers are import-safe and do not initialize MT5 or send orders.

## Audit Changes

The package audit now checks for:

- explicit spread source/sign config;
- mt5-tick spread code markers when `spread_source=mt5_tick`;
- side-specific pending/SL/TP spread policy;
- pending-too-close tick-level monitor config and code markers.

## Validation Required

- skill validation;
- Python compile for helper and audit scripts;
- config template parse;
- helper unit-style checks for spread source, market entry, pending price conversion, broker
  minimum-distance calculation, and pending state machine;
- `git diff --check`;
- local installed skill synchronized from the repo copy.

## Residual Risk

Exchange symbols can use Last-price trigger rules. A runtime handling exchange stocks/futures must
explicitly declare a different price basis and audit the broker symbol's trigger mode before
packaging.
