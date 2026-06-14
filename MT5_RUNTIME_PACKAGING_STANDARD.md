# MT5 Runtime Packaging Standard

## Purpose

This standard governs Phase 3 MT5 dry-run/demo runtime packaging after a candidate has
passed the required research gates. It converts a frozen candidate into a portable,
auditable Windows EXE for dry-run or DEMO monitoring.

Runtime packaging validates execution plumbing and operational safety. It does not validate
strategy profitability, does not create OOS-Final evidence, and does not authorize REAL
account trading.

## Scope And Trigger

Apply this standard whenever a task mentions EXE packaging, MT5 automatic trading, demo
orders, order monitoring, runtime monitoring, PyInstaller, portable MT5 runtime, or Chinese
phrases such as:

- 打包成exe文件
- 打包 MT5 自动交易
- 模拟下单
- 监控订单
- 持仓管理
- 换电脑运行

Codex should also load the local `mt5-runtime-packager` skill for implementation details,
but this file is the research-governance rule.

## Entry Gate

Before packaging:

- the strategy must have a registry record;
- the candidate/version must be frozen or explicitly approved for Phase 3 runtime handoff;
- strategy logic, parameters, cost model, symbols, and timeframes must not be changed in place;
- bar-by-bar replay must have passed, including MTF timing diff when applicable;
- the runtime handoff must identify strategy id, version, commit/config hashes, enabled
  candidates, risk model, and data boundary;
- execution/runtime audit is required before any package can be called ready.

If these are missing, the package status is `runtime_blocked`, not `demo_ready`.

## Direct EXE Contract

The operator-facing deliverable must work by directly opening the EXE. BAT/CMD/PowerShell
wrappers are development artifacts. They may exist only outside the final operator folder and must
not be copied into the folder handed to the user.

On double-click, the EXE must:

- locate `config.ini` beside the EXE;
- print an immediate console header with EXE path, config path, instance name, strategy id,
  runtime id, PID, start time, MT5 account/server, magic/comment, log dir, data-cache dir,
  refresh interval, order-enabled state, and safety-gate state;
- refresh visible console status every cycle with market-data update, reconciliation counts,
  scan counts, order attempts, positions, pending orders, unknown/unresolved items, and next
  wake-up time;
- write all runtime outputs under the copied EXE folder, not the source repo, build folder,
  or developer machine path;
- write fatal startup exceptions to `logs\fatal_error_YYYYMMDD_HHMMSS.log` and keep the
  console readable long enough for an operator to see the failure.

The default portable **operator** folder contract is:

```text
package\
  StrategyRuntime.exe
  config.ini
  logs\
  data_cache\     # optional; only if the runtime config uses it
```

The operator folder rules are:

- exactly one primary `.exe` must be present at the top level and it must run by double-click;
- `config.ini` must sit beside the EXE;
- `logs\` must exist and be empty at delivery;
- `data_cache\` is allowed only when the runtime config uses it, and it must be empty at
  delivery;
- `.bat`, `.cmd`, `.ps1`, `.py`, `.spec`, source files, build scripts, historical logs,
  historical caches, local test configs, `build\`, `dist\`, and `__pycache__\` are forbidden in
  the final operator folder.

If a build creates many BAT files, that folder is not the operator deliverable. Create a separate
minimal `portable\<package_name>\` or `release\<package_name>\` folder and copy only the approved
operator artifacts into it.

After a real package is built for handoff, immediately run the final EXE from the operator folder
or from an exact copy of it. Inspect the generated `logs\` for fatal startup logs, non-empty error
logs, tracebacks, exceptions, or CRITICAL/ERROR/FATAL lines. A package that starts but writes error
logs is still `runtime_blocked`. Save smoke/log-check evidence outside the operator folder, then
reset delivery `logs\` and optional `data_cache\` back to empty before handoff.

Do not deliver source folders, PyInstaller `build`, `.spec`, historical logs, historical
caches, local test configs, or machine-specific files as the operator copy folder.

## Required Config Contract

`config.ini` is the operator control surface. Do not hardcode these values inside the EXE:

- identity: `strategy_id`, `runtime_id`, `instance_name`, `magic_number`, `comment_prefix`,
  `mt5_comment_max_length`;
- runtime: `mode`, `refresh_seconds`, `terminal_path`, `timezone`, `console_live_output`,
  `pending_monitor_mode=tick`, and `tick_poll_interval_ms`;
- runtime smoke: `run_mt5_smoke_on_build=false`, `expected_account_server`, `expected_login`,
  `print_account_magic_snapshot`, `write_account_magic_snapshot`,
  `require_trade_allowed_for_orders`, `require_zero_magic_positions_before_smoke`, and
  `require_zero_magic_orders_before_smoke`;
- market data: `data_source=mt5_api`, `bars_to_keep=3000`, `cache_refresh_bars`,
  `data_cache_dir=.\data_cache`, `exclude_current_bar=true`, `atomic_cache_write=true`;
- order limits: `order_enabled`, `risk_cash_per_order`, `max_volume_per_order`,
  `max_total_volume`, `max_positions_total`, `max_positions_per_symbol`,
  `max_new_orders_per_cycle`;
- market/open-price entry execution: `entry_execution_mode`,
  `market_entry_price_policy=broker_tick_side_no_manual_spread`,
  `market_entry_use_tick_side=true`, `spread_adjust_market_entry=false`, and
  `spread_risk_accounting`;
- pending-order management: `pending_expire_bars`, `pending_expire_minutes`,
  `cancel_stale_pending=true`, `signal_price_basis`, `pending_price_policy`,
  `sltp_price_policy`, side-specific bid/ask spread handling,
  `pending_too_close_policy`, `market_if_pending_triggered`, and
  `pending_reprice_to_min_distance=false`;
- cost-inclusive sizing: `position_sizing_mode=cost_inclusive_risk_cash`,
  `include_commission_in_risk=true`, `commission_per_lot_round_turn_usd=7.0`,
  `commission_free_symbols=XAUUSD,BTCUSD`, `include_spread_in_risk=true`,
  `spread_source=mt5_tick`, `spread_fallback_source`, `fixed_spread_points_default`,
  `include_slippage_in_risk=true`, `slippage_points_entry`, `slippage_points_exit`,
  `volume_rounding=floor_to_step`, and `max_risk_overshoot_pct=0`;
- pending-order price policy: `adjust_buy_pending_entry_for_spread=true`,
  `adjust_sell_pending_entry_for_spread=false`, `adjust_buy_sltp_for_spread=false`,
  `adjust_sell_sltp_for_spread=true`, and `reject_if_adjusted_sl_invalid`;
- duplicate signal guard: `signal_execution_ledger_path`, `signal_key_fields`,
  `consume_signal_before_order_send=true`, and `block_duplicate_signal_bar=true`;
- reconciliation: `reconcile_on_startup`, `reconcile_each_cycle`, `recovery_lookback_days`,
  `history_future_buffer_hours`, `order_confirm_timeout_seconds`,
  `order_confirm_poll_interval_seconds`, `unknown_freeze_new_orders`;
- logging: `log_dir=.\logs`, runtime/error/reconciliation/order/position log switches;
- safety: `kill_switch`, `allow_demo_trade`, `allow_live_trade`, `dry_run_enforce`.

The account type must be read from MT5 and printed at runtime. Do not infer DEMO/REAL status
from the EXE name, BAT name, folder name, or config label.

### Cost-Inclusive Position Sizing

Order-capable runtimes must calculate lots from the full cost-inclusive risk denominator:

```text
lots = risk_cash_per_order / total_risk_cash_per_lot

total_risk_cash_per_lot =
  entry_to_sl_price_loss_cash_per_lot
  + commission_cash_per_lot
  + spread_cost_cash_per_lot
  + slippage_cost_cash_per_lot
```

Default commission is USD 7 per lot per closed trade for non-exempt symbols. XAUUSD and
BTCUSD may be commission-free only when explicitly listed in `commission_free_symbols` or in
a symbol-specific override. The runtime must log the matched commission rule for each order.

Volume must round down to the broker lot step by default. If minimum volume, spread, slippage,
commission or adjusted stop distance would exceed configured risk, the order must be rejected
unless an explicit audited overshoot policy allows it.

### Market/Open-Price Entry Execution

Open-price or market-entry execution must not reuse pending-order spread adjustment.

When the runtime sends an immediate market order at the intended open/entry time, do not manually
add spread to the requested entry price. Use the broker executable side:

```text
BUY  market/open entry price = current tick.ask
SELL market/open entry price = current tick.bid
```

The following is forbidden for market/open `order_send` entries:

```text
BUY  entry = raw_open + spread_price
SELL entry = raw_open - spread_price
```

That adjustment is for conservative pending-order construction or historical bid-chart modelling,
not for the actual market order request.

Required config:

```ini
[orders]
entry_execution_mode = market
market_entry_price_policy = broker_tick_side_no_manual_spread
market_entry_use_tick_side = true
spread_adjust_market_entry = false
spread_risk_accounting = actual_fill_no_extra_spread
```

Risk accounting must avoid double counting spread:

- if entry-to-SL risk uses the actual executable/fill side such as BUY ask or SELL bid, use
  `spread_risk_accounting=actual_fill_no_extra_spread`;
- if entry-to-SL risk uses raw bid-chart open/SL only, use
  `spread_risk_accounting=raw_chart_add_spread_cost`.

The runtime must log raw signal open, current bid/ask, selected executable price, and
spread-risk-accounting mode for every attempted market/open entry.

### Pending Order Price Policy

Pending order formulas must be declared in config and logged with both raw and adjusted levels.
Do not hide spread handling in code.

Spread is an explicit non-negative price distance:

```text
Primary live/order source:
spread_price  = current tick.ask - current tick.bid
spread_points = spread_price / symbol.point

Fallback deterministic source:
spread_price = configured fixed_spread_points_default * symbol.point
```

Order-capable demo/live-equivalent runtimes should default to `spread_source=mt5_tick` and read
`symbol_info_tick(symbol).ask - symbol_info_tick(symbol).bid` at the order decision time. Fixed
spread points or symbol overrides are allowed only when explicitly selected in config for
deterministic dry-run/backtest diagnostics. Every order journal row must log spread source, bid,
ask, point, spread points, spread price, tick timestamp, and whether the value affected price
conversion, risk accounting, or both.

Default bid-chart to MT5 bid/ask policy:

```text
pending_price_policy = broker_bidask_from_bid_chart
sltp_price_policy    = broker_bidask_from_bid_chart
signal_price_basis   = bid_chart
spread_price_source  = mt5_tick

BUY_STOP / BUY_LIMIT   pending_entry = raw_entry + spread_price   # ADD spread_price
SELL_STOP / SELL_LIMIT pending_entry = raw_entry                  # ADD nothing, SUBTRACT nothing

BUY  position sl/tp = raw_sl / raw_tp                             # ADD nothing, SUBTRACT nothing
SELL position sl/tp = raw_sl + spread_price / raw_tp + spread_price # ADD spread_price
```

For default MT5 bid-chart levels, BUY pending entries trigger on Ask, SELL pending entries trigger
on Bid, BUY position SL/TP closes on Bid, and SELL position SL/TP closes on Ask. Do not use a
symmetric "entry plus/minus spread, SL plus/minus spread" shortcut. Under this default
`signal_price_basis=bid_chart` policy there is no "subtract spread" case. Any ask-chart,
mid-price, or already-executable price basis must declare a different `signal_price_basis` and an
audited conversion table.

Required config:

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
reject_if_adjusted_sl_invalid = true
min_pending_distance_points_buffer = 0
```

If a runtime uses a different price basis, it must document which MT5 side triggers each level and
audit formulas against `symbol_info_tick().bid/ask`. `conservative_full_spread` is a legacy/testing
policy only and must not be the default for order-capable MT5 packages.

After adjustment, the runtime must validate long SL below entry, short SL above entry,
broker stops level, minimum pending distance, tick size rounding, and lot-step risk impact.
Invalid adjusted levels are order blockers.

### Pending Too-Close And Tick-Level Trigger Handling

`refresh_seconds` may control closed-bar signal scans and operator status refreshes, but it must not
be the only loop that manages an armed pending entry. Once a pending intent exists, or a pending
order cannot be placed because it is too close to the current price, the runtime must use a
tick-level monitor:

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

Before placing a pending order, fetch `symbol_info_tick()` and `symbol_info()` and calculate:

```text
min_distance_points = max(symbol.trade_stops_level, symbol.trade_freeze_level) + buffer
min_distance_price  = min_distance_points * symbol.point
```

Trigger-side state machine:

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

If the entry has already been triggered before a pending order is accepted, the runtime must stop
trying to place that pending order and convert the same signal intent to a market order: BUY at
current `tick.ask`, SELL at current `tick.bid`. If the price is not yet triggered but is inside the
minimum-distance band, keep the same `intent_id` in `armed_trigger_watch`, poll ticks until the
original adjusted entry becomes placeable or triggered, and abandon only when the signal expires.
Do not silently move the entry to the broker minimum distance unless an explicit audited policy
enables repricing. On invalid-stops/invalid-price/price-changed/requote retcodes, immediately
refresh the tick and run the same state machine. Market conversion must recalculate lots from the
actual executable market entry, current spread, SL/TP and slippage policy, and should enforce a
`max_market_conversion_chase_points` guard to avoid unlimited breakout chasing.

## MT5 Portability

The runtime must use MT5 Python API data from the locally connected terminal unless a file
source is explicitly configured for diagnostics.

Rules:

- default `terminal_path` is blank;
- if `terminal_path` is blank, use `mt5.initialize()` and the logged-in local terminal;
- after initialize, derive terminal root and data path from `mt5.terminal_info()`;
- never hardcode `C:\Users\<user>\AppData\Roaming\MetaQuotes\Terminal\<hash>`;
- never fall back to `D:\MT5\...`, repo `configs`, repo `output`, or developer-machine
  folders from a packaged EXE;
- all runtime logs/caches must resolve from the copied EXE folder or explicit external config.

## Market Data Cache

Continuous monitors must keep a bounded local market-data cache:

- seed each symbol/timeframe with the latest configured closed-bar window, default 3000 bars;
- exclude the current unfinished bar;
- on later cycles, fetch only a recent tail, merge/deduplicate by closed-bar timestamp, and
  keep the latest 3000 closed bars;
- write cache files atomically under `data_cache\SYMBOL_TIMEFRAME_ohlc.csv`;
- if a cache is corrupt, unordered, duplicated, or gapped, reseed from MT5 and log the event;
- do not repeatedly download and rewrite the full 3000-bar window every cycle unless the user
  explicitly requests stateless diagnostics.

## Logs And Reconciliation

At minimum, a runtime that can send DEMO orders must create:

- `logs\runtime_YYYYMMDD.log`;
- `logs\errors_YYYYMMDD.log`;
- `logs\reconciliation_report.csv`;
- `logs\orders_journal.csv`;
- `logs\execution_lifecycle_log.csv`;
- `logs\positions_snapshot.csv`;
- `logs\pending_orders_snapshot.csv`;
- `logs\signal_execution_ledger.jsonl`;
- `logs\order_intents.jsonl` or atomic per-intent JSON files under `logs\intents\`.

Startup sequence:

1. connect/reconnect MT5;
2. reject REAL accounts unless a separate future live-deployment policy explicitly permits them;
3. load local intent journal and quarantine corrupt partial records;
4. query positions by magic;
5. query pending orders by magic;
6. query recent history using the configured recovery window;
7. reconcile unresolved intents to broker state, using ticket/order/deal id as primary key;
8. load signal execution ledger and treat consumed signal keys as already attempted;
9. write account/recovery snapshot;
10. only then scan new signals.

Broker state is authoritative. Local intent files are context, not the source of truth.

## Order Safety

Order-capable runtimes must enforce:

- REAL account hard rejection under the current research standard;
- `allow_live_trade=false`;
- DEMO order execution only when explicitly configured and authorized;
- `kill_switch=false`;
- MT5 `trade_allowed=True`;
- max position, max volume, and max new orders per cycle gates;
- unique `magic_number` and `comment_prefix` for every strategy/version/environment;
- cost-inclusive position sizing that includes entry-to-SL loss, commission, spread and slippage;
- config-declared pending-order price adjustment for entry/SL/TP;
- MT5 comment length handling, including broker-side truncation tolerance;
- signal execution ledger before or at order attempt, so one completed signal bar cannot open
  twice even if the first order closes in the same candle or the runtime restarts;
- order intent journal written atomically before `order_send`;
- no blind duplicate retry when state is unknown.

If an open/close/modify cannot be confirmed from broker state, the runtime must mark it
unknown, freeze new opens for the affected symbol/magic when configured, keep logging, and
require manual review or an explicit retry policy.

## Preflight And Build Hooks

Packaging must not use PyInstaller as the debugging loop.

Do not turn every package build into a live MT5 session. Split verification into two levels:

1. **Static/offline package audit**: may run on any computer and must not call
   `mt5.initialize()`, open MT5, or query the account. It verifies Python syntax, import safety,
   config fields, path portability, risk formula code paths, pending-order formula code paths,
   signal-ledger code paths, build scripts, and portable-folder hygiene.
2. **Runtime MT5 smoke**: connects to the already available/configured MT5 terminal only when the
   user asks to run the source/EXE, when DEMO order testing is explicitly authorized, or when the
   deliverable is being verified on the target machine. This step verifies config read, MT5
   connection, visible identity header, logs/cache creation, cache seed/update, startup
   reconciliation, one monitor cycle, and optional DEMO order behavior.

Required offline build sequence:

1. run static package audit/preflight and fail on any contract FAIL;
2. compile/import-check source modules without order side effects;
3. verify `config.ini` contains all required risk/order/reconciliation fields;
4. build with PyInstaller only after static preflight passes;
5. run package audit again after build;
6. inspect the portable operator folder for minimal shape: exactly one EXE, beside-EXE
   `config.ini`, empty `logs\`, optional empty `data_cache\`, no BAT/CMD/PS1 wrappers, no source
   files, no build artifacts, no historical logs/caches, and no path leaks;
7. record EXE hash, config hash, build command, preflight result, and audit result.

Required runtime smoke sequence, only when explicitly running the runtime:

1. run the source monitor or packaged EXE with the final intended config;
2. connect to MT5 from runtime code, not from the build script;
3. print/log the account and magic-number snapshot;
4. verify visible identity header, logs/cache creation, cache update, startup reconciliation, and
   at least one monitor cycle;
5. inspect generated logs for fatal/error/traceback/exception signals;
6. for DEMO order smoke, confirm open/modify/close by broker state and then restore safe defaults.

For package handoff, the packaged EXE smoke and log check are mandatory. They may be run from a
temporary copy of the operator folder to keep the final delivery folder clean. If logs contain
errors, do not ship the package.

`build_exe.bat` should call a local preflight script before PyInstaller and fail immediately
on missing config fields, path leaks, missing risk/order code paths, or audit FAIL. It should not
open MT5 unless it is an explicitly named runtime-smoke command. In non-Git local strategy
folders, this build-time preflight is the main hook that supervises compliance.

## MT5 Trading Code Implementation Contract

Trading helpers must be written as import-safe, side-effect-light code. Reusable helpers such as
`mt5_runtime_common.py` may define account-state and order helpers, but importing the module must
not initialize MT5, open the terminal, read a machine-specific path, or send any order.

Use this structure for account/magic checks:

```python
# Caller has already called mt5.initialize() as part of an explicit runtime command.
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

The short console block should be produced by the runtime smoke/order path, not by the offline
build:

```text
当前账户：ICMarketsSC-Demo
trade_allowed=True
magic 24068 持仓：0
magic 24068 挂单：0
```

`ICMarketsSC-Demo`, login, magic number, and zero-position requirements must come from config or
the runtime command, not hardcoded in shared helper code. The reusable helper should expose:

- `mt5_account_state_snapshot(mt5, magic, symbol=None, include_details=True)`;
- `format_mt5_account_state_lines(snapshot)`;
- `mt5_account_state_blockers(snapshot, ...)`;
- `write_mt5_account_state_snapshot(log_dir, snapshot)`.

The snapshot/blocker functions are required before order-enabled runtime logic, but they are not a
reason to open MT5 for every packaging build. Static audit should verify these functions or their
equivalent exist; runtime smoke should execute them only when the user intentionally runs the
runtime against MT5.

## Verification Checklist

A package cannot be called `portable_package_ready` unless:

- static package preflight passed;
- package audit has no FAIL;
- the final operator folder contains exactly one runnable EXE, beside-EXE `config.ini`, empty
  `logs\`, and optional empty `data_cache\` only if needed;
- the final operator folder contains no `.bat`, `.cmd`, `.ps1`, `.py`, `.spec`, source/build
  artifacts, historical logs, historical caches, or local test configs;
- final EXE direct launch was tested when a runtime smoke was requested or required for handoff;
- generated logs from the immediate final EXE smoke were inspected and contained no fatal/error,
  traceback, exception, or non-empty error-log evidence;
- console shows dynamic cycle output during runtime smoke;
- outputs are written under the portable folder;
- MT5 path discovery works without developer-machine absolute paths;
- logs and data cache are created;
- startup reconciliation runs before signal scanning;
- dry-run mode does not call `order_send`;
- DEMO order smoke, when explicitly authorized, confirms open/modify/close by broker state,
  not retcode alone;
- the deliverable copy folder is the minimal operator package, not `build`, `dist`, source root,
  or a folder full of helper BAT files.
- smoke/log-check evidence is stored outside the final operator folder, and delivery `logs\` and
  optional `data_cache\` are empty at handoff.

## Evidence Labels

Use these labels:

- `runtime_blocked`: entry gate, preflight, audit, or safety check failed;
- `dry_run_ready`: direct EXE dry-run monitor passed, no order sending;
- `demo_ready`: authorized DEMO order path passed broker-state reconciliation;
- `portable_package_ready`: portable folder and copy-path smoke passed.

Demo/runtime logs remain `runtime_validation_not_oos_final`. They must not be reported as
OOS-Final or live performance.
