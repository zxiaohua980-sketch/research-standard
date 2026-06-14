---
name: mt5-runtime-packager
description: Package, audit, or document MT5 Python runtime monitors as minimal portable EXE operator folders with one runnable EXE, beside-EXE config.ini, empty logs, no BAT/CMD/PS1 wrappers in the final folder, offline/static build checks that do not open MT5, runtime-only account/magic snapshots, cost-inclusive sizing, MT5 bid/ask-correct market/open entries, explicit spread source/sign rules, Buy Stop/Sell Stop and SL/TP spread handling, pending-too-close tick monitoring with market conversion when triggered, same-bar duplicate-order ledgers, reconciliation logs, demo-only safety gates, magic/comment namespaces, and terminal/data-path discovery. Use for MT5 runtime packaging, config.ini risk/order design, PyInstaller builds, demo order plumbing, portable EXEs, runtime smoke tests, moving runtimes to another computer, or Chinese requests such as 打包成exe文件, 模拟下单, 仓位计算, 手续费点差滑点, 挂单价格, 防止重复下单.
---

# MT5 Runtime Packager

## Core Boundary

Use this as an operational packaging skill, not as a strategy-validation skill.

Before touching a trading runtime, obey the project `AGENTS.md` and registry. State the strategy stage, whether code/parameter changes are allowed, whether execution audit is required, and whether the work can contaminate forward-live results. Never create live-trading scripts, enable REAL-account trading, set `framework_start_time`, or treat demo/runtime logs as OOS-Final evidence.

## Workflow

1. Inspect the runtime package: executor script, direct EXE entry point, build BAT/spec, external `config.ini`, logs/cache handling, reconciliation files, dist/portable folder, and any legacy launch BATs.
2. State the project gate first: strategy stage, whether strategy code/parameters may change, whether execution audit is required, and whether this work can contaminate forward-live results.
3. Run or adapt `scripts/audit_mt5_runtime_package.py <runtime_dir>` for a first-pass audit.
4. Fix portability before packaging. Hardcoded MT5 terminal IDs, user-specific `MetaQuotes\Terminal\<hash>` paths, repo-root fallbacks, and machine-local data paths are blockers.
5. If the runtime needs MT5 API OHLC, Python ZigZag/fractal calculation, or demo order management helpers, read `references/mt5-runtime-common-code.md` and copy/adapt `scripts/mt5_runtime_common.py` into the runtime staging folder.
6. Do not open MT5 for every package build. First run an offline/static preflight that does not call `mt5.initialize()`: syntax/import safety, config fields, path portability, risk formula code paths, pending-order formula code paths, signal-ledger code paths, and portable-folder hygiene. Run MT5 source/EXE smoke only when the user explicitly asks to execute the runtime, when DEMO order testing is authorized, or when verifying the deliverable on the target machine.
7. Package with PyInstaller from a clean staging directory only after the offline/static preflight passes. Copy only required strategy/runtime modules and shared helpers.
8. Keep `config.ini` external beside the EXE. Never bury machine-specific settings, account identity, risk limits, refresh interval, magic number, comment prefix, or MT5 paths inside the binary.
9. The modern operator deliverable is opened by double-clicking the EXE. BAT files are optional legacy wrappers only and must not be the primary contract.
10. Verify cost-inclusive position sizing before any order-capable runtime is packaged: lots must equal configured risk cash divided by total per-lot risk, where total per-lot risk includes entry-to-SL price loss, commission, configured/fetched spread, and slippage estimate. XAUUSD and BTCUSD may be commission-free only when explicitly configured.
11. Verify entry price construction before any order-capable runtime is packaged. Market/open-price entries and pending-order entries are different contracts. A market/open-price entry must not reuse the pending-order `entry +/- spread` adjustment; pending orders must declare their own price basis, spread source, spread add/no-add rules, broker minimum-distance handling, and tick-level trigger watch for entry, SL and TP.
12. Verify account reconciliation, persistent signal execution ledger, and outage recovery behavior before any monitor is allowed to place demo orders.
13. After every source or config-default fix, rebuild and re-run the final EXE from the deliverable folder; do not rely on a pre-rebuild source test.
14. Build a clean portable **operator** deliverable folder for copying to another computer. The user-facing folder must be minimal: one immediately double-click runnable `.exe`, one beside-EXE `config.ini`, and an empty `logs\` directory. `data_cache\` is allowed only when the config/runtime needs it, and it must be empty at delivery. Do not put BAT/CMD/PowerShell wrappers in the operator folder.
15. Immediately after a real package is built for handoff, run the final EXE once from the operator folder or a copy of it. Inspect the generated logs for fatal/error/traceback/exception signals. A package with log errors is not deliverable.
16. After smoke passes, save smoke evidence outside the operator folder, then reset delivery `logs\` and optional `data_cache\` to empty so the final folder remains clean.
17. Record the EXE hash, config hash, build command, portable folder contents, static preflight result, post-package EXE smoke result, log-error check result, and final cleanup result.

## Direct EXE Operator Contract

When the user asks to "package as EXE", "打包成exe文件", "MT5自动交易", "模拟下单", "监控订单", or similar, treat the direct EXE contract as mandatory unless the user explicitly asks for a developer-only package.

The EXE launched by double-click must:

- locate and read `config.ini` beside the EXE;
- print a live console header immediately: EXE path, config path, instance name, strategy/runtime id, PID, start time, account/server, magic/comment, log dir, data-cache dir, refresh interval, order-enabled state, and safety-gate state;
- refresh visible console status every cycle, including market-data update, reconciliation counts, scan counts, order attempts, open positions, pending orders, unknown/unresolved items, and next wake-up time;
- use MT5 Python API data from the locally connected terminal, not machine-specific exported files, unless config explicitly selects a file source;
- store runtime outputs under the copied EXE folder, not the original repo or build folder;
- write fatal startup exceptions to `logs\fatal_error_YYYYMMDD_HHMMSS.log` and keep the console open long enough for the operator to read the error.

The required default operator folder contract is:

```text
package\
  StrategyRuntime.exe
  config.ini
  logs\
  data_cache\     # optional; only if the runtime config uses it
```

There must be exactly one primary `.exe` in the operator folder. It must be self-sufficient when
double-clicked. Optional BAT/CMD/PowerShell wrappers may exist only outside the operator folder
under a development/build area such as `dev_tools\` or `legacy_wrappers\`; they must not be copied
into the final folder handed to the user.

After a real package is created, run this EXE immediately from the operator folder or from a
temporary copy with the same beside-EXE `config.ini`. Inspect `logs\` before handoff. If any fatal
startup log, traceback, exception, non-empty error log, or CRITICAL/ERROR/FATAL log line appears,
the package is `runtime_blocked`. Store the smoke/log-check report outside the operator folder and
clean `logs\` back to empty before delivery.

## MT5 Path Portability Rules

Never hardcode:

```text
C:\Users\<user>\AppData\Roaming\MetaQuotes\Terminal\<terminal-id>\MQL5\Files
```

Use this priority order instead:

1. External config override: `terminal_path = ...` may point to a terminal executable, but should default blank.
2. `mt5.initialize(path=terminal_path)` only when config provides a path; otherwise call `mt5.initialize()` and use the default logged-in terminal.
3. After initialize, call `mt5.terminal_info()` and derive:

```python
terminal_root = Path(info.path)
terminal_data = Path(info.data_path)
mql5_files = terminal_data / "MQL5" / "Files"
```

4. If a legacy file-source workflow truly needs `MQL5\Files` before connection, scan `%APPDATA%\MetaQuotes\Terminal\*\MQL5\Files` and choose by required files or most recent matching source, then write the selected path to logs.
5. Prefer MT5 Python API OHLC and runtime-local temp files. Do not write generated temporary OHLC/ZigZag files into the user's MT5 `MQL5\Files`; write under `<exe_dir>\tmp`.
6. In PyInstaller onefile mode, use:

```python
BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", SCRIPT_DIR))
RUNTIME_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else SCRIPT_DIR
```

Use `BUNDLE_DIR` for bundled read-only modules and `RUNTIME_DIR` for external config/logs/tmp.

For frozen/packaged EXEs, do not fall back to project-root paths such as `D:\MT5\...`, repo `configs`, or repo `output` folders. Runtime data must resolve from the copied EXE folder, bundled `_MEIPASS` data, or explicit external config values only.

## Packaging Pattern

Use a maintained `build_exe.bat` or `.spec` that:

- Deletes old build/dist output.
- Creates a clean staging folder.
- Copies only required runtime modules.
- Adds strategy helper modules with `--add-data`.
- Adds native DLLs explicitly when using conda/extension packages, such as `ffi.dll`, OpenSSL DLLs, compression DLLs, and `sqlite3.dll`.
- Adds hidden imports for `numpy`, `pandas`, and `MetaTrader5`.
- Excludes unrelated heavy packages.
- Copies `config.ini` to `dist` and creates empty `dist\logs` and `dist\data_cache`.
- Records SHA256 for the EXE.
- Creates a separate clean portable operator deliverable such as `portable\<package_name>` containing exactly one runnable EXE, external `config.ini`, empty `logs`, and optional empty `data_cache` only if needed. The final user-facing folder must not contain `.bat`, `.cmd`, `.ps1`, `.py`, `.spec`, source files, build scripts, historical logs, historical caches, or local test configs.
- Fails immediately if old `build`, `dist`, or `portable` folders cannot be removed; do not continue after "Access is denied" or file-in-use cleanup failures.

Keep old BAT names only as development/legacy wrappers if users already have shortcuts; make them delegate to the EXE with the same external `config.ini`, and keep them outside the final operator folder. The final user-facing folder to copy to another computer is the minimal portable operator folder, not the source runtime folder.

## Required Config Contract

`config.ini` must be the operator control surface. At minimum it must externalize:

- identity: `strategy_id`, `runtime_id`, `instance_name`, `magic_number`, `comment_prefix`, `mt5_comment_max_length`;
- runtime: `mode`, `refresh_seconds`, `terminal_path`, `timezone`, `console_live_output`, `pending_monitor_mode=tick`, `tick_poll_interval_ms`;
- runtime smoke: `run_mt5_smoke_on_build=false`, `expected_account_server`, `expected_login`, `print_account_magic_snapshot`, `write_account_magic_snapshot`, `require_trade_allowed_for_orders`, `require_zero_magic_positions_before_smoke`, `require_zero_magic_orders_before_smoke`;
- market data: `data_source=mt5_api`, `bars_to_keep=3000`, `cache_refresh_bars`, `data_cache_dir=.\data_cache`, `exclude_current_bar=true`, `atomic_cache_write=true`;
- order limits: `order_enabled`, `risk_cash_per_order`, `max_volume_per_order`, `max_total_volume`, `max_positions_total`, `max_positions_per_symbol`, `max_new_orders_per_cycle`;
- cost-inclusive sizing: `position_sizing_mode=cost_inclusive_risk_cash`, `include_commission_in_risk=true`, `commission_per_lot_round_turn_usd=7.0`, `commission_free_symbols=XAUUSD,BTCUSD`, `include_spread_in_risk=true`, `spread_source=mt5_tick`, `spread_fallback_source`, `fixed_spread_points_default`, `include_slippage_in_risk=true`, `slippage_points_entry`, `slippage_points_exit`, `volume_rounding=floor_to_step`, `max_risk_overshoot_pct=0`;
- market/open-price entry execution: `entry_execution_mode`, `market_entry_price_policy=broker_tick_side_no_manual_spread`, `market_entry_use_tick_side=true`, `spread_adjust_market_entry=false`, and `spread_risk_accounting`;
- pending-order management: `pending_expire_bars`, `pending_expire_minutes`, `cancel_stale_pending=true`, `signal_price_basis`, `pending_price_policy`, `sltp_price_policy`, side-specific bid/ask spread handling for BUY pending entries, SELL pending entries, BUY SL/TP, and SELL SL/TP, plus `pending_too_close_policy`, `market_if_pending_triggered`, and `pending_reprice_to_min_distance=false`;
- duplicate-signal prevention: `signal_execution_ledger_path`, `signal_key_fields`, `consume_signal_before_order_send=true`, `block_duplicate_signal_bar=true`;
- reconciliation: `reconcile_on_startup`, `reconcile_each_cycle`, `recovery_lookback_days`, `history_future_buffer_hours`, `order_confirm_timeout_seconds`, `order_confirm_poll_interval_seconds`, `unknown_freeze_new_orders`;
- logging: `log_dir=.\logs`, `runtime_log_enabled`, `error_log_enabled`, `reconciliation_log_enabled`, `order_journal_enabled`, `position_snapshot_enabled`;
- safety: `kill_switch`, `allow_demo_trade`, `allow_live_trade`, `dry_run_enforce`.

The account type is read and printed from MT5 at runtime. Do not infer DEMO/REAL safety from the EXE filename or BAT name. Trading permission is the intersection of MT5 account state, config gates, and project policy.

## Cost-Inclusive Position Sizing Contract

Order-capable runtimes must size positions from the **total risk per lot**, not from the raw
entry-to-stop distance alone.

Required formula:

```text
lots = risk_cash_per_order / total_risk_cash_per_lot

total_risk_cash_per_lot =
  entry_to_sl_price_loss_cash_per_lot
  + commission_cash_per_lot
  + spread_cost_cash_per_lot
  + slippage_cost_cash_per_lot
```

The runtime must round volume down to broker `volume_step` by default. If the rounded volume
would exceed configured risk because of min volume, stop-level changes, spread, slippage or
commission, reject the order unless an explicit audited overshoot policy allows it.

Config must expose:

```ini
[risk]
position_sizing_mode = cost_inclusive_risk_cash
risk_cash_per_order = 100
include_commission_in_risk = true
commission_per_lot_round_turn_usd = 7.0
commission_free_symbols = XAUUSD,BTCUSD
include_spread_in_risk = true
spread_source = mt5_tick
spread_fallback_source = fixed_points
fixed_spread_points_default =
include_slippage_in_risk = true
slippage_points_entry = 0
slippage_points_exit = 0
volume_rounding = floor_to_step
max_risk_overshoot_pct = 0
```

Gold and Bitcoin are commission-free only if they match `commission_free_symbols` or a
symbol-specific override. Do not silently infer commission-free status from substring matches
without logging the matched rule.

Audit requirements:

- locate the sizing function, for example `mt5_executor.py`;
- prove `lots = risk_cash / total_risk_per_lot`;
- prove `total_risk_per_lot` includes entry-to-SL loss, commission, spread and slippage;
- prove XAUUSD/BTCUSD commission exemption is config-driven;
- log each order's raw risk components before sending.

## Market/Open-Price Entry Contract

Open-price or market-entry execution is **not** the same as pending-order price construction.

When the strategy says "enter at the next bar open" and the runtime sends an immediate market
order at that time, do not manually add spread to the order entry price. The runtime must use the
broker's executable side:

```text
BUY  market/open entry price = current tick.ask
SELL market/open entry price = current tick.bid
```

Do not do this for market/open entries:

```text
BUY  entry = raw_open + spread_price   # forbidden for market/open order_send
SELL entry = raw_open - spread_price   # forbidden for market/open order_send
```

That `entry +/- spread` adjustment belongs to conservative pending-order construction or to
historical bid-chart backtest modelling, not to the actual market-order request price.

Required config fields:

```ini
[orders]
entry_execution_mode = market
market_entry_price_policy = broker_tick_side_no_manual_spread
market_entry_use_tick_side = true
spread_adjust_market_entry = false
spread_risk_accounting = actual_fill_no_extra_spread
```

Risk accounting must avoid double counting spread:

- If `entry_to_sl_price_loss_cash_per_lot` is calculated from the actual executable/fill side
  such as BUY ask or SELL bid, use `spread_risk_accounting=actual_fill_no_extra_spread`.
- If risk is calculated from raw bid-chart levels only, use
  `spread_risk_accounting=raw_chart_add_spread_cost` and add spread as a separate cost component.
- In both cases, commission and slippage policies still remain config-driven and auditable.

Audit requirements:

- prove market/open orders use `symbol_info_tick().ask` for BUY and `symbol_info_tick().bid` for
  SELL, or an equivalent broker-reported fill price after send;
- prove no manual `raw_open +/- spread` entry shift is applied to market/open order requests;
- prove spread is not double counted in the risk denominator;
- log raw signal open, broker tick bid/ask, selected execution price, and spread-risk-accounting
  mode for each attempted order.

## Bid/Ask Spread Adjustment Contract

Default raw strategy levels are assumed to come from MT5 chart OHLC, which for FX/CFD symbols is
normally bid-chart data. Under `signal_price_basis=bid_chart`, convert raw strategy levels to MT5
execution/trigger sides like this:

`spread_price` is a non-negative price distance, not an arbitrary sign:

```text
Primary live/order source:
spread_price  = current tick.ask - current tick.bid
spread_points = spread_price / symbol.point

Fallback deterministic source:
spread_price = configured fixed_spread_points_default * symbol.point
```

The runtime must declare `spread_source=mt5_tick` for order-capable live/demo packages unless a
deterministic fixed spread is explicitly selected for dry-run/backtest diagnostics. If
`spread_source=mt5_tick`, read it from `symbol_info_tick(symbol).ask - symbol_info_tick(symbol).bid`
at the order decision time. If using fixed points or a symbol override, log the exact config key.
Always log: spread source, bid, ask, point, spread points, spread price, tick timestamp, and whether
the spread value was used for price conversion, risk accounting, or both.

```text
MARKET / OPEN-PRICE ENTRY
BUY  entry = current tick.ask   # no manual raw_open + spread
SELL entry = current tick.bid   # no manual raw_open - spread

PENDING ENTRY
BUY_STOP / BUY_LIMIT   entry = raw_entry + spread_price   # ADD spread_price
SELL_STOP / SELL_LIMIT entry = raw_entry                  # ADD nothing, SUBTRACT nothing

ATTACHED SL/TP AFTER POSITION OPENS
BUY  sl = raw_sl                    # ADD nothing, SUBTRACT nothing
BUY  tp = raw_tp                    # ADD nothing, SUBTRACT nothing
SELL sl = raw_sl + spread_price     # ADD spread_price
SELL tp = raw_tp + spread_price     # ADD spread_price
```

Do not use one symmetric "add/subtract spread everywhere" rule. The correct adjustment depends on
whether the order is a market/open entry, buy pending entry, sell pending entry, BUY position SL/TP,
or SELL position SL/TP. Under the default `signal_price_basis=bid_chart` policy above, there is no
"subtract spread" case. Any strategy that wants a different source basis such as ask-chart,
mid-price or already-executable prices must declare a different `signal_price_basis` and provide a
separate audited conversion table.

Required config fields:

```ini
[orders]
signal_price_basis = bid_chart
pending_price_policy = broker_bidask_from_bid_chart
sltp_price_policy = broker_bidask_from_bid_chart
spread_price_source = mt5_tick
adjust_buy_pending_entry_for_spread = true
adjust_sell_pending_entry_for_spread = false
adjust_buy_sltp_for_spread = false
adjust_sell_sltp_for_spread = true
```

If raw levels are not bid-chart levels, the config must say so with `signal_price_basis`, and the
runtime must document the equivalent conversion. `conservative_full_spread` is a legacy/testing
policy only and must not be used as the default for MT5 order-capable packages.

## Pending Order Price Contract

Pending order prices must be deterministic and config-driven. Do not hide spread adjustment
inside ad-hoc code.

First declare the signal price basis:

```ini
[orders]
signal_price_basis = bid_chart
pending_price_policy = broker_bidask_from_bid_chart
spread_price_source = mt5_tick
```

Supported policies:

### `broker_bidask_from_bid_chart`

Use this when raw signal levels are MT5 bid-chart levels:

```text
BUY_STOP / BUY_LIMIT   pending_entry = raw_entry + spread_price
SELL_STOP / SELL_LIMIT pending_entry = raw_entry

BUY  position sl/tp = raw_sl / raw_tp
SELL position sl/tp = raw_sl + spread_price / raw_tp + spread_price
```

This is the default exact MT5 bid/ask conversion for bid-chart strategy levels.

### `broker_bidask_exact`

Use this when raw levels are explicitly bid-chart levels and the runtime wants to model MT5
bid/ask trigger mechanics directly:

```text
BUY  entry executes on ask; buy pending entry may need raw_entry + spread_price.
BUY  SL/TP close on bid; raw bid-chart SL/TP usually stay at raw_sl/raw_tp.
SELL entry executes on bid; sell pending entry usually stays at raw_entry.
SELL SL/TP close on ask; raw bid-chart SL/TP may need + spread_price.
```

If this policy is selected, the runtime must log which MT5 side triggers each level and the
audit must verify it against `symbol_info_tick().bid/ask`, not just chart OHLC.

Required config fields:

```ini
[orders]
pending_price_policy = broker_bidask_from_bid_chart
sltp_price_policy = broker_bidask_from_bid_chart
signal_price_basis = bid_chart
spread_price_source = mt5_tick
adjust_buy_pending_entry_for_spread = true
adjust_sell_pending_entry_for_spread = false
adjust_buy_sltp_for_spread = false
adjust_sell_sltp_for_spread = true
reject_if_adjusted_sl_invalid = true
min_pending_distance_points_buffer = 0
```

Audit requirements:

- list formulas for market/open entry, BUY_STOP, SELL_STOP, BUY SL/TP and SELL SL/TP;
- prove adjusted long SL remains below entry and adjusted short SL remains above entry;
- prove broker stops-level/min-distance checks run after adjustment;
- prove order journal records both raw and adjusted levels;
- reject packaging if policy or price basis is missing for order-capable runtimes.

## Pending Too-Close And Tick-Level Trigger Contract

Pending orders cannot be managed only once per minute. The bar/closed-candle scan may still run on
`refresh_seconds`, but once a pending intent exists or a pending order cannot be placed because it
is too close to the current price, the runtime must switch that intent to tick-level monitoring.

Default runtime config:

```ini
[runtime]
refresh_seconds = 60
pending_monitor_mode = tick
tick_poll_interval_ms = 250

[orders]
pending_too_close_policy = wait_until_valid_or_market_if_triggered
market_if_pending_triggered = true
pending_reprice_to_min_distance = false
pending_retry_on_invalid_price = true
max_market_conversion_chase_points =
```

`refresh_seconds` is for signal scans and status cycles. It is not allowed to be the only mechanism
that decides whether an armed pending entry has been reached.

Before placing a pending order, fetch `symbol_info_tick()` and `symbol_info()` and validate broker
minimum distance:

```text
min_distance_points = max(symbol.trade_stops_level, symbol.trade_freeze_level) + buffer
min_distance_price  = min_distance_points * symbol.point
```

Then apply the trigger-side logic:

```text
BUY_STOP  already triggered if tick.ask >= adjusted_entry
SELL_STOP already triggered if tick.bid <= adjusted_entry
BUY_LIMIT already triggered if tick.ask <= adjusted_entry
SELL_LIMIT already triggered if tick.bid >= adjusted_entry

BUY_STOP  is placeable only if adjusted_entry > tick.ask + min_distance_price
SELL_STOP is placeable only if adjusted_entry < tick.bid - min_distance_price
BUY_LIMIT is placeable only if adjusted_entry < tick.ask - min_distance_price
SELL_LIMIT is placeable only if adjusted_entry > tick.bid + min_distance_price
```

If the entry is already triggered before the pending order is accepted, do **not** keep trying to
place the pending order. Convert the same signal intent to a market order:

```text
BUY_STOP triggered  -> send market BUY at current tick.ask
SELL_STOP triggered -> send market SELL at current tick.bid
BUY_LIMIT triggered -> send market BUY at current tick.ask
SELL_LIMIT triggered -> send market SELL at current tick.bid
```

If the order is not triggered but is inside the broker minimum-distance band, do not blindly retry
every minute and do not silently move the entry level. Keep the same intent in
`armed_trigger_watch` and poll ticks until one of these happens:

1. trigger side reaches the adjusted entry -> convert to market if `market_if_pending_triggered=true`;
2. price moves away enough that the original adjusted entry becomes placeable -> place the pending
   order at the original adjusted entry;
3. signal expires -> abandon the intent and record `expired_without_place`;
4. broker/order state becomes unknown -> quarantine/manual review; do not duplicate.

If `order_send()` for a pending order returns invalid stops, invalid price, price changed or requote,
immediately fetch a fresh tick and run the same state machine. Repeated failures must update the
same `intent_id`; they must not create duplicate signal keys or duplicate order intents. Market
conversion must recalculate lots from the actual executable market entry, current spread, SL/TP and
slippage policy before sending. A `max_market_conversion_chase_points` guard should block unlimited
chasing after a violent breakout.

## Runtime Safety Gates

Default runtime config must match the deliverable intent.

Read-only scanner defaults:

```ini
mode = dry_run
allow_demo_trade = false
allow_live_trade = false
dry_run_enforce = true
kill_switch = false
risk_cash_per_order = 100
position_sizing_mode = cost_inclusive_risk_cash
include_commission_in_risk = true
commission_per_lot_round_turn_usd = 7.0
commission_free_symbols = XAUUSD,BTCUSD
include_spread_in_risk = true
spread_source = mt5_tick
spread_fallback_source = fixed_points
include_slippage_in_risk = true
slippage_points_entry = 0
slippage_points_exit = 0
volume_rounding = floor_to_step
entry_execution_mode = market
market_entry_price_policy = broker_tick_side_no_manual_spread
market_entry_use_tick_side = true
spread_adjust_market_entry = false
spread_risk_accounting = actual_fill_no_extra_spread
pending_price_policy = broker_bidask_from_bid_chart
sltp_price_policy = broker_bidask_from_bid_chart
signal_price_basis = bid_chart
adjust_buy_pending_entry_for_spread = true
adjust_sell_pending_entry_for_spread = false
adjust_buy_sltp_for_spread = false
adjust_sell_sltp_for_spread = true
signal_execution_ledger_path = .\logs\signal_execution_ledger.jsonl
consume_signal_before_order_send = true
block_duplicate_signal_bar = true
max_positions_total = 1
max_positions_per_symbol = 1
max_new_orders_per_cycle = 1
refresh_seconds = 60
pending_monitor_mode = tick
tick_poll_interval_ms = 250
pending_too_close_policy = wait_until_valid_or_market_if_triggered
market_if_pending_triggered = true
pending_reprice_to_min_distance = false
log_dir = .\logs
terminal_path =
magic_number =
comment_prefix =
mt5_comment_max_length = 16
strategy_tag =
environment_id = demo
```

If the user explicitly authorizes a DEMO-order deliverable, default config may instead be:

```ini
mode = demo_trade
allow_demo_trade = true
allow_live_trade = false
dry_run_enforce = false
kill_switch = false
order_enabled = true
risk_cash_per_order = 100
position_sizing_mode = cost_inclusive_risk_cash
include_commission_in_risk = true
commission_per_lot_round_turn_usd = 7.0
commission_free_symbols = XAUUSD,BTCUSD
include_spread_in_risk = true
spread_source = mt5_tick
spread_fallback_source = fixed_points
include_slippage_in_risk = true
slippage_points_entry = 0
slippage_points_exit = 0
volume_rounding = floor_to_step
entry_execution_mode = market
market_entry_price_policy = broker_tick_side_no_manual_spread
market_entry_use_tick_side = true
spread_adjust_market_entry = false
spread_risk_accounting = actual_fill_no_extra_spread
pending_price_policy = broker_bidask_from_bid_chart
sltp_price_policy = broker_bidask_from_bid_chart
signal_price_basis = bid_chart
adjust_buy_pending_entry_for_spread = true
adjust_sell_pending_entry_for_spread = false
adjust_buy_sltp_for_spread = false
adjust_sell_sltp_for_spread = true
signal_execution_ledger_path = .\logs\signal_execution_ledger.jsonl
consume_signal_before_order_send = true
block_duplicate_signal_bar = true
max_positions_total = 1
max_positions_per_symbol = 1
max_new_orders_per_cycle = 1
refresh_seconds = 60
pending_monitor_mode = tick
tick_poll_interval_ms = 250
pending_too_close_policy = wait_until_valid_or_market_if_triggered
market_if_pending_triggered = true
pending_reprice_to_min_distance = false
log_dir = .\logs
data_cache_dir = .\data_cache
terminal_path =
environment_id = demo
```

For this profile, direct EXE startup should show a clear `DEMO_ORDER_ENABLED` state when the account and config allow it. Any optional BAT wrapper must preserve the same behavior as launching the EXE directly. REAL accounts are still hard rejected unless the project policy explicitly permits a separate live-release path; this skill must not create that path by default.

Order methods must require:

- connected account;
- non-REAL account, with REAL hard rejected;
- `trade_allowed=True`;
- effective CLI mode `demo_trade`;
- `allow_demo_trade=true`;
- `dry_run_enforce` not blocking;
- `kill_switch=false`;
- max-position and max-volume gates for opens;
- candidate-level `order_enabled=true`.

## Runtime Output and Disk Control

Continuous monitors must not produce unbounded per-cycle bulk files by default.

Require by default:

- print dynamic console status every monitor cycle; a quiet console is a packaging defect for operator-facing EXEs;
- append rolling runtime events to `logs\runtime_YYYYMMDD.log`;
- append fatal and recoverable errors to `logs\errors_YYYYMMDD.log`;
- append reconciliation decisions to `logs\reconciliation_report.csv`;
- append order lifecycle rows to `logs\orders_journal.csv` and `logs\execution_lifecycle_log.csv`;
- write latest broker-state snapshots to `logs\positions_snapshot.csv` and `logs\pending_orders_snapshot.csv`;
- keep persistent safety ledgers append-only: `logs\signal_execution_ledger.jsonl`, `logs\order_intents.jsonl`, or atomic per-intent files under `logs\intents\`;
- maintain stable market-data cache files under a relative `data_cache_dir`;
- seed cache files with the required closed-bar window, then fetch only a configured recent tail such as `cache_refresh_bars`, merge/deduplicate by closed-bar timestamp, and keep the bounded window such as latest 3000 closed bars;
- write cache files atomically as `data_cache\SYMBOL_TIMEFRAME_ohlc.csv`, excluding the current unfinished bar;
- if a cache is corrupt or has gaps, reseed it from MT5, log the event, and continue only when the rebuilt cache passes timestamp ordering and duplicate checks;
- recalculate ZigZag from the bounded OHLC cache into one stable ZigZag cache file per symbol/timeframe/parameter set; do not append ZigZag blindly because recent extrema can change;
- write MT5 history and lifecycle as latest snapshot CSVs by default, not repeated full JSONL appends every cycle;
- delete per-scan OHLC/ZigZag temp folders after each scan unless a troubleshooting config explicitly keeps them;
- default `write_timestamped_scan_files=false`, `write_full_trade_history=false`, `write_fail_reasons=false`, `keep_scan_tmp_files=false`;
- document every config switch that can increase disk usage and turn it off again for continuous monitoring.

Do not make demo order execution depend on re-reading a freshly rewritten `realtime_latest_signals.csv`. Use the current scan result in memory, and treat files as audit outputs.

Do not repeatedly download the entire 3000-bar window and write/delete per-cycle OHLC/ZigZag files in continuous monitor mode. Use bounded cache files unless the user explicitly requests stateless scans for diagnostics.

`magic_number` and `comment_prefix` must be external config values and must be unique for each strategy/version/environment. Do not reuse the same magic/comment namespace across different runtimes, or position reconciliation can manage the wrong trades.

Broker-side MT5 comments may be truncated more aggressively than MT5's nominal limit; keep `mt5_comment_max_length` external, default conservatively, and validate identity by allowing the broker comment to be a prefix of the intended comment. Preserve a short intent id in the comment.

When broker retcodes are unreliable, send once and reconcile against account state: new position observed for open, SL/TP observed for modify, position gone for close.

## Account Reconciliation and Outage Recovery

Treat order submission as an intent plus broker-state reconciliation, not as a single `order_send` call.

Every runtime that can send demo orders should include:

- an order intent journal written before `order_send`, with intent id, symbol, side, volume, SL, TP, magic, comment, created time, close scope, requested volume, previous volume, and status;
- an intent id generated with `uuid4()` or millisecond timestamp plus random suffix; MT5 comments should embed only a short id because broker comments can be length-limited;
- atomic intent persistence: SQLite transaction, or write temp file + flush/fsync + `os.replace()`; direct partial-prone open/write is not enough for recovery state;
- append-only intent updates should merge by `intent_id` and preserve original non-empty fields such as comment, theoretical entry, SL, TP, risk, and signal key; later status rows must not erase the original order intent context;
- post-send reconciliation using `positions_get`, `orders_get`, `history_orders_get`, and/or `history_deals_get`, with MT5 broker/account state treated as authoritative and the local intent journal treated only as context;
- explicit statuses such as `sent_confirmed_open`, `sent_not_confirmed`, `close_confirmed`, `close_not_confirmed`, `unknown_requires_manual_review`;
- startup reconciliation before new signal handling;
- immediate scan of current open positions by magic number;
- scan of pending orders by magic number;
- recent order/deal history scan over a configured `recovery_lookback_days` window, expanded to include the oldest unresolved intent plus a safety margin; add a configurable future buffer such as `history_future_buffer_hours` when broker history timestamps can be ahead of local UTC;
- reconciliation matching by broker ticket/order/deal id as the primary key; symbol, magic, comment, time, side, and volume are validation fields, not the primary key;
- SL/TP confirmation using symbol tick/point tolerance, not exact float equality;
- close confirmation that distinguishes full close from partial close and validates remaining volume when partial close is supported;
- a persistent signal execution ledger keyed by symbol, timeframe, candidate id, completed signal bar time/value, matched signal bar, and side, so one signal bar can trigger at most one open even if the first position closes in the same candle or the runtime restarts;
- reconnect handling that distinguishes process crash recovery from MT5 unavailable/network-disconnected recovery using `mt5.initialize()`, `mt5.last_error()`, and `mt5.terminal_info()`;
- no blind duplicate retry when state is unknown;
- a defined manual-review/quarantine mode when an intent cannot be reconciled: freeze new opens for the affected symbol/magic, keep logging/scanning if safe, write an operator alert, and avoid automatic time-based resolution unless an explicit policy says otherwise.

On monitor startup, do this before scanning for new signals:

1. Connect or reconnect to MT5; if initialize/terminal_info fails, enter safe mode and do not send orders.
2. Reject REAL accounts.
3. Load local intent journal if present; ignore or quarantine corrupt partial records.
4. Query `positions_get()` and filter by magic number.
5. Query `orders_get()` and filter pending orders by magic number.
6. Query recent `history_orders_get()` and `history_deals_get()` for the configured recovery window.
7. Reconcile each unresolved intent to broker state, using ticket/order/deal id first and validating magic/symbol/comment after the match.
8. Load the signal execution ledger and treat previously attempted signal keys as consumed.
9. Log the account snapshot and recovery decision.
10. Only then scan new signals.

If an open command was sent but no position/order/deal can be confirmed, mark it unknown and do not send another open automatically. If a close command was sent but the position still exists, either retry once under an explicit retry policy or quarantine/manual-review; never assume the close succeeded. If the terminal/network is unavailable, stop order actions and keep the safest local state.

For signal-driven monitors, do not rely only on "current open position count" to prevent duplicate opens. If a position is opened and then closed by SL/TP within the same candle, the same completed signal bar must remain consumed in a persistent ledger such as `signal_execution_ledger.jsonl`. Write the ledger before or at order attempt time and fsync it when practical.

## MT5 Trading Code Implementation Contract

Reusable trading helpers such as `mt5_runtime_common.py` must be import-safe and side-effect-light.
Importing the helper must not call `mt5.initialize()`, open MT5, read machine-specific terminal
paths, send orders, modify orders, or close positions.

Do not require a live MT5 session for every package build. Use two levels:

1. **Offline/static package audit**: verifies code/config/build contracts without touching MT5.
2. **Runtime MT5 smoke**: connects to MT5 only when the user intentionally runs the source/EXE,
   authorizes DEMO order testing, or asks to verify the deliverable on the target computer.

Concrete account/magic status code should be centralized in the runtime helper:

```python
# Caller has already initialized MT5 as part of an explicit runtime command.
snapshot = mt5_account_state_snapshot(mt5, magic=config.magic_number)
for line in format_mt5_account_state_lines(snapshot):
    print(line)
write_mt5_account_state_snapshot(Path(config.log_dir), snapshot)
blockers = mt5_account_state_blockers(
    snapshot,
    expected_account_server=config.expected_account_server or None,
    expected_login=config.expected_login or None,
    require_trade_allowed=config.order_enabled,
    require_zero_magic_positions=config.require_zero_magic_positions_before_smoke,
    require_zero_magic_orders=config.require_zero_magic_orders_before_smoke,
)
if blockers:
    enter_safe_mode(blockers)
```

The human-readable runtime smoke block is:

```text
当前账户：ICMarketsSC-Demo
trade_allowed=True
magic 24068 持仓：0
magic 24068 挂单：0
```

But `ICMarketsSC-Demo`, login, magic number and zero-position requirements must come from
`config.ini` or the explicit runtime command, never hardcoded in shared helpers. Static packaging
should verify that this code path exists. Runtime smoke/order-enabled startup should execute it
only when MT5 is intentionally being run.

## Verification Checklist

Run verification in this order:

1. Offline/static preflight: syntax/import safety, config parsing, path portability, cost-inclusive sizing path, pending-order price policy path, signal-ledger path, and package hygiene. This step must not open MT5.
2. Package audit: run or adapt `scripts/audit_mt5_runtime_package.py <runtime_dir>` and fail on any safety, portability, config, direct-EXE, logging, reconciliation, or cache-contract FAIL.
3. Build: run the maintained PyInstaller build script only after offline/static preflight and audit pass. Treat cleanup errors, file-in-use, or access denied as blockers.
4. Final EXE smoke: for package handoff, launch the single packaged EXE directly from the portable operator folder or an exact copy with its beside-EXE `config.ini`. It must show the live header immediately and write outputs under that folder.
5. Immediate log check: after the EXE smoke, inspect `logs\` with `scripts/check_runtime_logs_for_errors.py <operator_or_logs_dir>` or an equivalent scanner. Any fatal/error/traceback/exception finding blocks delivery.
6. Portability smoke: when runtime execution is requested/required, copy the portable folder to a different temporary path and launch the EXE there. Outputs must be written under the copied folder, not the original repo/runtime/build directory.
7. Runtime monitor smoke: when runtime execution is requested/required, run at least one full monitor cycle. Confirm dynamic console updates, account/magic snapshot, `monitor_cycle pass` or equivalent, reconciliation counts, scan counts, cache update status, and no unexpected `order_send` when config disables orders.
8. Order smoke: only after the user explicitly authorizes DEMO testing, run a demo-only open/modify/close or `close_all_magic`, then restore the safe default config. Verify retcode plus broker-state observation, lifecycle rows, history export, and final magic-number positions/orders check.
9. Risk/config audit: verify cost-inclusive sizing, commission-free symbol overrides, spread/slippage risk components, pending-order price formulas, raw-vs-adjusted order journal fields, and same-signal-bar duplicate blocking.
10. Final hygiene: save smoke/log-check evidence outside the operator folder, then clean delivery `logs\` and optional `data_cache\` back to empty. The operator folder should contain one `.exe`, `config.ini`, empty `logs\`, and optional empty `data_cache\` only if needed. No BAT/CMD/PowerShell wrappers, source files, PyInstaller specs, build folders, historical logs, historical caches, local test configs, or loose helper scripts may be present. Text files and EXE strings should not contain machine-specific paths such as `D:\MT5`, `C:\Users\<name>`, `%APPDATA%\MetaQuotes\Terminal`, or terminal hash IDs.

Expected runtime behavior:

- Direct EXE launch is sufficient; optional BAT wrappers cannot be the only tested path.
- Final operator delivery is minimal: EXE + config.ini + empty logs folder. BAT/CMD/PS1 wrappers are development artifacts, not user-facing delivery artifacts.
- After a real package is built, the final EXE is run immediately and logs are checked. Error logs block handoff even when the build succeeded.
- Offline packaging does not by itself open MT5; live account/magic checks belong to intentional runtime smoke or order-enabled startup.
- A strategy monitor with no latest signal reports `attempted=0` rather than forcing a trade.
- Startup reconciles existing positions, pending orders, recent order/deal history, and unresolved local intents before scanning new signals.
- Position size uses cost-inclusive risk denominator: entry-to-SL loss plus commission, spread, and slippage.
- Pending orders use the configured price policy and journal both raw and adjusted entry/SL/TP.
- Duplicate opens for the same completed signal bar are blocked by a persistent signal execution ledger, even if the first order closes in the same candle or the runtime restarts.
- Dry-run/runtime rows are labelled not forward-live and not for performance claims.
- Cached market-data verification runs two cycles: first seed/update, second incremental tail merge with stable file counts and no full-window rewrite unless diagnostics explicitly request it.

## Enforcement Hooks

Skills are instructions, not a hard runtime hook. They improve Codex behavior, but they cannot technically force every future agent action.

Use build-time hooks for enforcement:

- add or adapt a local preflight script such as `scripts/preflight_mt5_runtime_contract.py`;
- make `build_exe.bat` call the preflight before PyInstaller and fail immediately on contract failures;
- make the build script call the package audit after PyInstaller and fail on any FAIL;
- require a small evidence file such as `build_preflight_report.json` for offline checks, and only when runtime smoke is explicitly run, `logs\source_preflight_last.json` recording config path, source-run result, cache/log creation, MT5 account state, and one-cycle scan status;
- after final EXE smoke, run `scripts/check_runtime_logs_for_errors.py` or an equivalent scanner and save the smoke/log-check evidence outside the operator folder;
- for Git/CI repositories, run the same preflight/audit in pre-commit or CI; for non-Git local strategy folders, the build script is the most reliable hook.

When this skill triggers, Codex should prefer adding or using these hooks instead of relying on memory. If no hook exists, report that gap before packaging.

## References

- For implementation snippets and a fuller checklist, read `references/portable-runtime-pattern.md`.
- For account-state recovery requirements, read `references/account-reconciliation.md`.
- For a config template covering cost-inclusive sizing, pending-order spread policy and duplicate-signal ledger, use `templates/config_cost_inclusive_pending_orders.ini`.
- For reusable Python helpers covering MT5 API OHLC download, Enhanced ZigZag calculation, DEMO market open/close, magic-number filtering, intent journals, and history exports, read `references/mt5-runtime-common-code.md` and copy/adapt `scripts/mt5_runtime_common.py`.
- For package audits, run `scripts/audit_mt5_runtime_package.py <runtime_dir>`.
- For post-smoke log checks, run `scripts/check_runtime_logs_for_errors.py <operator_or_logs_dir>`.
