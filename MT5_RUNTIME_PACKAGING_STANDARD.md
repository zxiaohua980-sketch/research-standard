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

The operator-facing deliverable must work by directly opening the EXE. BAT files may exist
only as optional compatibility wrappers and must not be the only tested path.

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

The default portable folder contract is:

```text
package\
  StrategyRuntime.exe
  config.ini
  logs\
  data_cache\
```

Do not deliver source folders, PyInstaller `build`, `.spec`, historical logs, historical
caches, local test configs, or machine-specific files as the operator copy folder.

## Required Config Contract

`config.ini` is the operator control surface. Do not hardcode these values inside the EXE:

- identity: `strategy_id`, `runtime_id`, `instance_name`, `magic_number`, `comment_prefix`,
  `mt5_comment_max_length`;
- runtime: `mode`, `refresh_seconds`, `terminal_path`, `timezone`, `console_live_output`;
- market data: `data_source=mt5_api`, `bars_to_keep=3000`, `cache_refresh_bars`,
  `data_cache_dir=.\data_cache`, `exclude_current_bar=true`, `atomic_cache_write=true`;
- order limits: `order_enabled`, `risk_cash_per_order`, `max_volume_per_order`,
  `max_total_volume`, `max_positions_total`, `max_positions_per_symbol`,
  `max_new_orders_per_cycle`;
- pending-order management: `pending_expire_bars`, `pending_expire_minutes`,
  `cancel_stale_pending=true`, and spread-aware pending price handling;
- reconciliation: `reconcile_on_startup`, `reconcile_each_cycle`, `recovery_lookback_days`,
  `history_future_buffer_hours`, `order_confirm_timeout_seconds`,
  `order_confirm_poll_interval_seconds`, `unknown_freeze_new_orders`;
- logging: `log_dir=.\logs`, runtime/error/reconciliation/order/position log switches;
- safety: `kill_switch`, `allow_demo_trade`, `allow_live_trade`, `dry_run_enforce`.

The account type must be read from MT5 and printed at runtime. Do not infer DEMO/REAL status
from the EXE name, BAT name, folder name, or config label.

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

Required sequence:

1. run the source monitor with the final intended config;
2. verify config read, MT5 connection, visible identity header, logs/cache creation, 3000-bar
   cache seed/update, startup reconciliation, and at least one monitor cycle;
3. run package audit/preflight and fail on any contract FAIL;
4. build with PyInstaller only after source preflight passes;
5. run package audit again after build;
6. launch the packaged EXE directly from the portable folder;
7. copy the portable folder to a different temporary path and launch again;
8. record EXE hash, config hash, build command, preflight result, audit result, and smoke
   result.

`build_exe.bat` should call a local preflight script before PyInstaller and fail immediately
on missing config fields, path leaks, missing logs/cache contract, source-run failure, or
audit FAIL. In non-Git local strategy folders, this build-time preflight is the main hook
that supervises compliance.

## Verification Checklist

A package cannot be called `portable_package_ready` unless:

- source preflight passed;
- package audit has no FAIL;
- final EXE direct launch was tested;
- console shows dynamic cycle output;
- outputs are written under the portable folder;
- MT5 path discovery works without developer-machine absolute paths;
- logs and data cache are created;
- startup reconciliation runs before signal scanning;
- dry-run mode does not call `order_send`;
- DEMO order smoke, when explicitly authorized, confirms open/modify/close by broker state,
  not retcode alone;
- the deliverable copy folder contains only the EXE, `config.ini`, empty `logs`, empty
  `data_cache`, and explicitly requested docs/hash files.

## Evidence Labels

Use these labels:

- `runtime_blocked`: entry gate, preflight, audit, or safety check failed;
- `dry_run_ready`: direct EXE dry-run monitor passed, no order sending;
- `demo_ready`: authorized DEMO order path passed broker-state reconciliation;
- `portable_package_ready`: portable folder and copy-path smoke passed.

Demo/runtime logs remain `runtime_validation_not_oos_final`. They must not be reported as
OOS-Final or live performance.
