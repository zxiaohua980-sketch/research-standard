---
name: python-mt5-ea-port
description: Convert Python MT5 trading systems into MT5 Expert Advisors with strict deterministic signal parity, closed-bar timing, full audit logs, Python-vs-MT5 validation, and hard pre-package gates. Use when migrating, porting, packaging, installing, or replicating Python strategy/runtime code into MT5 EA while preserving exact signal behavior, execution rules, risk logic, order lifecycle behavior, and validation evidence.
---

# Python MT5 to MT5 EA Port

Convert a Python MT5 trading strategy/runtime into a logically equivalent MT5 Expert Advisor.

Primary goal: **strict signal parity**.

This is not a redesign task.  
This is not a performance-optimization task.  
This is not a strategy-improvement task.

---

# Core Objective

Build an MT5 EA that:

1. Produces deterministic signals matching the Python baseline.
2. Uses only closed bars for signal calculation.
3. Preserves Python condition order and calculation order.
4. Preserves pivot / swing / structure state behavior.
5. Preserves entry / SL / TP / risk / cost / execution rules.
6. Produces complete logs for audit and Python comparison.
7. Separates strategy calculation from execution monitoring.

---

# Hard Rules

Do not break these rules:

- Do NOT simplify strategy logic.
- Do NOT optimize strategy logic unless the user explicitly asks in a separate new version.
- Do NOT change signal conditions.
- Do NOT reorder filters or condition sequence.
- Do NOT change parameter values.
- Do NOT replace custom Python logic with MT5 indicators unless replay proves exact equivalence.
- Do NOT use unfinished bars.
- Do NOT use `shift=0` for strategy features or signals.
- Do NOT use future bars.
- Do NOT introduce repainting.
- Do NOT modify the original Python strategy in place.
- Do NOT modify an existing frozen/forward/live EA in place.
- Every material change must create a new isolated version folder.
- Default runtime must be DRY_RUN / orders disabled.
- Do NOT call `OrderSend`, `PositionClose`, or `OrderDelete` unless the user explicitly authorizes execution.
- Do NOT launch MT5 terminal, run Strategy Tester, package runtime, or place demo/live orders unless explicitly requested.
- Do NOT package, install, or hand off an order-capable EA as usable for demo/live trading until the Python baseline replay, EA signal parity, and authorized order lifecycle tests have passed.
- If order lifecycle testing is not authorized, label the EA `dry_run_only_not_demo_ready_not_live_ready` or block; do not imply it can trade just because it compiles.
- All EA `input` / operator-facing custom variables must include clear Chinese comments explaining purpose, default behavior, and risk if applicable.

---

# Required First Steps

Before editing strategy code:

1. Read the project `AGENTS.md`.
2. Read the strategy registry entry if a strategy ID exists.
3. State:
   - strategy ID
   - current stage
   - current version
   - whether code changes are allowed
   - whether parameter changes are allowed
   - whether execution audit is required
   - whether the task can contaminate forward-live results
4. Create or use a new isolated version folder.
5. Record parent source path and hashes when possible.

---

# Version Isolation

Every EA migration or patch must use a separate version folder.

EA names and folders must preserve the source strategy version. Do not turn an EA build, compile fix, install-path fix, or execution-log fix into a new strategy version.

- Treat the strategy prefix as user-controlled. Do not hardcode or finalize a prefix such as `STR007_MA` unless the user has approved that exact prefix for the current EA work.
- Use the project three-phase directory contract: `C\` for Phase 1 candidates, `V\` for Phase 2 formal strategy versions, and `R\` for Phase 3 runtime/package/EA artifacts.
- Formal EA ports belong under `R\<strategy_version>\EA\R<major>\...`. Major EA artifact revisions create new subdirectories (`R1`, `R2`); minor EA fixes are subdirectories under the major revision (`R1.1`, `R1.2`).
- The EA file, installed MT5 folder, manifest, and report should include the approved strategy prefix, fixed strategy version, artifact type, and artifact revision: `<strategy_prefix>_V1.2_EA_R1`. Do not use an EA/runtime artifact name that looks like a new strategy `V`.

Required:

```text
<project_root>\<strategy_prefix>\
  R\
    <strategy_version>\
      EA\
        R1\
          src/
          audits/
          logs/ or tester evidence if applicable
          version_manifest.yaml
```

Do not overwrite:

- original Python files
- parent EA files
- frozen candidate files
- forward/live runtime files

---

# Required EA Architecture

Use a **single EA instance**.

- Attach to one chart only.
- Internally manage all symbols.
- Internally manage all timeframes.
- Do not require one chart per symbol.
- Do not depend on the chart timeframe for strategy logic.

---

# Event Model

## OnInit

Use for:

- config loading
- symbol/timeframe state initialization
- log initialization
- timer setup

## OnTimer

Use for:

- minute scheduling
- symbol/timeframe round-robin scanning
- closed-bar detection
- bar-layer strategy calculation
- reconciliation
- log flushing

## OnTick

Use for execution monitoring only:

- pending order monitoring
- spread/tick checks
- SL/TP modification checks
- position monitoring
- fill confirmation

`OnTick` must NOT compute:

- indicators
- pivots
- swings
- structures
- strategy signals

---

# Required Layers

Implement three logical layers.

---

## 1. StrategyEngine

Purpose:

- deterministic signal generation only

Input contract:

- StrategyEngine input is a frozen closed-bar OHLC snapshot.
- StrategyEngine must receive all data from the MT5 layer as immutable closed-bar arrays.
- StrategyEngine must NOT request, infer, or access any market data from MT5 runtime or tick stream.
- StrategyEngine must NOT call back into the EA layer to request data.
- StrategyEngine must NOT depend on runtime market state, spread, tick, order state, latency, account state, or broker execution state.

Restrictions:

- no trading API calls
- no tick access
- no order execution
- no `OrderSend`
- no `PositionClose`
- no `OrderDelete`
- no `SymbolInfoTick`
- no `CopyRates` inside StrategyEngine
- no MT5 runtime market-state access
- no EA-layer data callbacks
- no dependency on tick stream, spread, order state, latency, account state, or broker execution state

Allowed input:

- frozen closed-bar OHLC snapshot
- primitive arrays
- preloaded closed-bar OHLC data
- preloaded timestamp arrays
- precomputed or passed config values

The input snapshot must be complete before StrategyEngine execution starts.  
StrategyEngine must treat the snapshot as immutable.

Output:

- signal objects
- pivot metadata
- swing metadata
- structure metadata
- risk/cost metadata

StrategyEngine may use MQL5 structs/classes, but it must not fetch market data or execute trades itself.

---

## 2. MT5 Execution Layer

Purpose:

- data loading
- market monitoring
- order conversion
- order execution
- position management
- reconciliation

Responsibilities:

- call `CopyRates`
- call `SymbolInfoTick`
- manage MagicNumber filtering
- convert strategy signals into broker orders
- send pending orders only when authorized
- monitor fills
- manage exits/trailing/flat logic
- write execution logs

EA input rule:

Every MQL5 `input` variable exposed to the operator must have a Chinese comment.

Example:

```mql5
input bool InpEnableOrders = false; // 是否允许真实发送订单：默认 false，只记录日志不下单
input string InpRuntimeMode = "DRY_RUN"; // 运行模式：DRY_RUN=只记录不下单；LIVE=允许进入发单流程
```

---

## 3. Validation Layer

Purpose:

- compare Python baseline signals with EA-generated signals

Responsibilities:

- load Python baseline file
- compare signal-by-signal
- write match report
- write mismatch report
- write statistical report
- flag missing / extra / mismatched signals

Signal comparison contract:

- All signal comparisons MUST be anchored by `signal_time` timestamp, not array index.
- Array indices such as `pivot_iloc` and `confirm_iloc` are diagnostic metadata only.
- Array index drift across different backtest windows must NOT cause a mismatch by itself.
- Different backtest window lengths must not change signal alignment if `signal_time`, symbol, timeframe, direction, and prices match within tolerance.

---

# Data Access Rules

All strategy calculations must use closed bars only.

Use strictly:

```mql5
CopyRates(symbol, timeframe, 1, bars, rates);
```

Rules:

- `start_pos = 1`
- `shift = 0` forbidden for signals
- unfinished bar forbidden
- future bars forbidden
- repaint assumptions forbidden
- MT5 `rates[i].time` is bar open time
- signal time must match Python timing semantics
- if Python uses bar close time, compute it explicitly from open time + timeframe seconds

---

# Required State Model

Maintain state per `symbol × timeframe`.

Minimum state:

```text
SymbolTfState:
  symbol
  timeframe
  tf_seconds
  last_bar_time
  rates_cache
  atr_cache
  sma_cache
  pivot_state
  swing_state
  structure_state
  signal_cache
  last_signal_key
  last_signal_time
```

Do not rebuild long-lived state from scratch unless required to preserve Python parity.

---

# Strategy Logic Preservation

Preserve all Python logic exactly.

---

## Pivot / Swing

Must preserve:

- n-left / n-right pivot confirmation
- ATR threshold logic
- retracement window
- confirm delay
- release index logic
- candidate lifecycle
- active candidate retention
- duplicate suppression
- deterministic ordering

Do not replace with:

- ZigZag
- iFractals
- built-in swing indicators
- simplified pivot logic

unless exact replay equivalence is proven.

---

## Structure

Must preserve:

- H0 / L0 / H1 / L1 ordering
- nearest swing selection
- structure chain construction
- deterministic tie-break rules
- Python sequence order

---

## MA Filter

Must preserve:

- fast pool
- slow pool
- fast/slow crossover detection
- golden cross count
- death cross count
- cumulative count
- `pass_count >= threshold`

---

## ATR / Risk

Must preserve:

- ATR formula
- Wilder smoothing seed behavior
- risk_atr calculation
- min/max risk bounds
- fixed RR logic
- SL / TP formula
- cost/risk inclusion rules

Do not replace hand-written Python ATR with `iATR` unless replay proves exact equality.

---

# Indicator Cache Rules

Default implementation MUST use full-window recomputation identical to the Python baseline.

Caching is DISABLED by default.

Incremental update is NOT allowed unless:

- the user explicitly requests it in a separate version
- full-window Python parity has already passed
- incremental-vs-full-window replay proves exact equality
- the optimization does not affect the correctness layer

Performance optimization must NOT affect signal generation correctness.

Caching is allowed only if parity is preserved.

Safe only after validation:

- cache loaded closed bars
- cache symbol/timeframe state
- skip unchanged bars
- use `iTime(symbol, tf, 1)` for new-bar checks
- delta `CopyRates` after initial seed

Dangerous:

- rolling ATR
- rolling SMA
- shortened warmup windows
- built-in MT5 indicators

Rule:

If rolling cache changes Python seed/window behavior, do not use it.  
Correctness has priority over performance.  
Full-window recomputation is the default correctness path.

---

# Signal Object Contract

Each generated EA signal must include enough data to compare with Python.

Required fields:

```text
signal_key
timestamp
symbol
timeframe
direction
entry
sl
tp
risk_atr
pass_count
pivot_iloc
pivot_time
pivot_price
confirm_iloc
confirm_time
signal_time
structure_chain
cost_class
spread_price_units
slippage_price_units
commission
reason_flags
```

Do not use `iloc` as the primary alignment key; windowed caches can shift indices.
Always anchor signal comparison by stable identifiers:

```text
signal_time
symbol
timeframe
direction
entry
sl
tp
pivot_time
pivot_price
confirm_time
```

`pivot_iloc` and `confirm_iloc` may be logged for diagnostics, but they must not be the unique basis for signal matching.

---

# Logging System

All EA logs must be written under:

```text
MQL5/Files/logs/
```

Use:

```mql5
FolderCreate("logs");
```

Write paths like:

```text
logs\signal_log.jsonl
logs\trade_execution_log.jsonl
logs\tick_trace.log
logs\mismatch_report.jsonl
```

Do not assume arbitrary filesystem paths are writable from an EA.

---

## 1. Signal Log

Path:

```text
logs\signal_log.jsonl
```

Fields:

```text
timestamp
symbol
timeframe
signal_key
pivot_iloc
pivot_time
pivot_price
confirm_iloc
confirm_time
direction
entry
sl
tp
source
stage
reason_flags
```

`source` must be:

```text
python | mt5
```

`stage` should normally be:

```text
bar_close
```

---

## 2. Trade Execution Log

Path:

```text
logs\trade_execution_log.jsonl
```

OPEN event fields:

```text
event
timestamp
symbol
volume
entry_price
sl
tp
ticket
signal_key
latency_ms
reason
retcode
comment
```

CLOSE event fields:

```text
event
timestamp
ticket
symbol
close_price
pnl
reason
retcode
```

---

## 3. Tick Trace Log

Path:

```text
logs\tick_trace.log
```

Format:

```text
timestamp | symbol | bid | ask | event
```

Only log execution events:

- pending activation
- SL modification
- TP modification
- close trigger
- fill confirmation
- rejection
- retry

Do not log every tick unless explicitly requested.

---

## 4. Mismatch Log

Path:

```text
logs\mismatch_report.jsonl
```

Fields:

```text
symbol
timeframe
signal_key
field
python_value
mt5_value
tolerance
mismatch_type
```

Mismatch types:

```text
missing_in_mt5
extra_in_mt5
field_mismatch
time_mismatch
price_mismatch
sequence_mismatch
```

---

# Validation Boundary

Every validation report must include:

```text
python_baseline_file
date_from
date_to
broker/server timezone
symbol list
timeframe list
price_tolerance
time_tolerance
expected_count
mt5_count
matched_count
missing_count
extra_count
mismatch_count
MATCH_STATUS
```

Do not report PASS without these boundaries.

---

# Primary Validation

## EURUSD M15 Hard Check

Required primary check:

```text
symbol = EURUSD
timeframe = M15
```

Requirement:

```text
100% signal match with Python baseline
```

Compare using `signal_time` as the primary anchor:

```text
signal_time
symbol
timeframe
direction
entry
sl
tp
pivot_time
pivot_price
confirm_time
signal_key
```

Diagnostic-only fields:

```text
pivot_iloc
confirm_iloc
```

If not 100% matched:

```text
MATCH_STATUS = FAIL
```

No unexplained mismatch is acceptable.

Index drift alone must not be treated as failure if timestamp-anchored signal identity matches within tolerance.

---

# Multi-Market Sampling Validation

Use reproducible sampling.

Rules:

- fixed seed required
- seed must be logged
- sample 3 to 5 symbols from FX28 + XAUUSD + BTCUSD
- sample timeframes from M15 / M30 / H1
- log sampled symbols
- log sampled timeframes

Important:

```text
Multi-market >=95% is diagnostic only.
Any unexplained mismatch must be investigated.
Accepted sampled scope requires zero unexplained mismatches.
```

Do not hide mismatches behind aggregate percentage.

All sampled validation must use timestamp-anchored comparison.  
Array index drift must not create false mismatches across different backtest windows.

---

# Execution Engine Rules

If Python sends pending orders, EA must support equivalent pending orders.

Required:

- BUY STOP
- SELL STOP
- spread-adjusted entry if Python does it
- spread-adjusted SL/TP if Python does it
- slippage/deviation model
- MagicNumber filtering
- comment tagging with timeframe
- pending expiry
- retry loop
- broker confirmation
- fill verification
- order/position reconciliation

Default must be dry-run/no-order-send.

Real broker actions require:

```text
InpRuntimeMode = LIVE
InpEnableOrders = true
explicit user authorization for this run
```

## Pre-Package EA Gate

Use this gate before producing a final `.ex5` handoff, MT5 install package, zipped EA folder, or any EA deliverable the user may interpret as ready for simulated/live trading.

Hard blockers:

1. Create a new isolated EA artifact revision under the strategy version first. Do not patch the parent Python strategy or an old EA in place.
2. Python baseline evidence must already exist:
   - isolated Python source copy and config hashes;
   - execution audit / no-lookahead audit;
   - bar-by-bar replay comparing signals, trades, equity, and MTF feature diffs if applicable.
3. EA StrategyEngine parity must pass before any order-capable handoff:
   - EURUSD M15 primary validation 100% matched;
   - sampled multi-market/timeframe validation has zero unexplained mismatches;
   - timestamp-anchored signal keys match, not just array indices.
4. Dry-run EA runtime test must pass before order testing:
   - EA loads config/inputs correctly;
   - no `shift=0` or unfinished-bar signals;
   - logs are written under the EA-safe folder;
   - one timer/bar cycle completes with no errors and no orders.
5. If the requested EA is order-capable (`模拟`, `实盘`, `能下单`, `LIVE`, or equivalent), require explicit authorization and test the execution lifecycle before final packaging/install handoff:
   - market/pending open path according to the Python contract;
   - broker/Strategy Tester confirmation of order accepted or position filled;
   - SL/TP attachment;
   - trailing/SLTP modification if implemented;
   - pending expiration/cancel if implemented;
   - position close or broker-side SL/TP close reconciliation;
   - restart/startup recovery by magic/comment/signal ledger;
   - duplicate signal blocking.
6. Compiling is allowed as a test step, but compile success is not acceptance. A compiled `.ex5` without parity and lifecycle evidence is `compile_only_not_trading_ready`.
7. If a packaged/installed EA reveals source or lifecycle bugs, mark it `wrong_deliverable_or_runtime_blocked`, fix the isolated source and validation first, then recompile/repackage.

---

# Risk and Volume Rules

Port Python volume logic exactly.

Must account for:

- tick size
- tick value
- contract size if Python uses it
- min volume
- max volume
- volume step
- configured cap
- commission inclusion
- spread inclusion
- slippage inclusion
- zero-volume rejection

Do not silently round up volume in a way that increases risk.

---

# Friday Flat / Manual Flat Rules

If Python has Friday flat or user asks for flat logic:

- keep BTC/crypto exemptions if required
- MagicNumber-filter positions and orders unless user explicitly asks for account-wide action
- separate automatic flat from manual flat
- manual flat must require explicit input, e.g.:

```mql5
input bool InpManualFridayFlatNow = false; // 手动周五全平开关：true=周五达到截止时间后，平掉/撤销非BTC的本EA持仓/挂单；执行后请改回false
```

- log every close/delete attempt
- do not treat manual flat as strategy performance evidence

---

# Performance Rules

Performance is measured, not primary.

Correctness > performance.

Log:

```text
tick latency
bar scan time
symbol scan time
CopyRates call count
cache hit count
```

Targets may be reported, but failure to hit a speed target must not justify logic changes.

---

# Build Evidence

Every EA delivery must report:

```text
EA source path
EX5 path
compile log path
compile status
error count
warning count
source_sha256
ex5_sha256
MT5 install path if installed
whether MT5 terminal was launched
whether Strategy Tester was run
whether any orders were sent
```

Compile target:

```text
0 errors
0 warnings preferred
```

---

# MT5 Install Rules

When installing into MT5:

- copy `.mq5`
- copy `.ex5`
- copy required `.mqh` modules
- use a versioned Experts subfolder
- verify installed hashes match version-root hashes
- do not launch MT5 unless user asks

Example install layout:

```text
MQL5/Experts/<strategy_prefix>/<strategy_version>/EA/R1/
  <strategy_prefix>_<strategy_version>_EA_R1.mq5
  <strategy_prefix>_<strategy_version>_EA_R1.ex5
  module1.mqh
  module2.mqh
```

---

# Packaging Rules

Only package when the user explicitly asks.

If packaging is requested:

- enforce the Pre-Package EA Gate first;
- follow the MT5 runtime packaging standard / packager skill
- preserve dry-run/demo/live safety gates
- run final smoke/log checks after packaging
- if claiming demo/live readiness, run final packaged/installed EA order lifecycle smoke, not just compile or dry-run
- record EX5/package hashes, config/input hashes, Python parity evidence, order lifecycle evidence when applicable
- do not include wrapper scripts unless the packaging standard allows them

---

# Required Output Format

For each migration or patch, report:

```text
Strategy ID:
Parent version:
New version:
Stage:
Code changes allowed:
Parameter changes allowed:
Execution audit required:
Forward-live contamination risk:

Changed files:
Unchanged parent files:
EA source:
EX5:
Compile:
Validation:
Logs:
Hashes:
MT5 install path:
MT5 launched:
Orders sent:
Known limitations:
```

---

# Final Acceptance Criteria

A migrated EA is valid only if:

- EURUSD M15 primary validation is 100% matched.
- Sampled multi-market validation has zero unexplained mismatches.
- No lookahead exists.
- No unfinished bar is used for signals.
- Logs are complete and reproducible.
- Tick/bar/timer responsibilities are separated.
- Build evidence and hashes are recorded.
- Default runtime remains dry-run/orders-disabled.
- If advertised as demo/live/order-capable, order lifecycle evidence exists for open/place, broker confirmation, SL/TP, trailing/modify if implemented, close/cancel/history reconciliation, startup recovery, and duplicate-signal blocking.
- If order lifecycle evidence does not exist, final status must be `dry_run_only_not_demo_ready_not_live_ready` or `compile_only_not_trading_ready`, never `demo_ready` or `live_ready`.

---

# Global Determinism Rule

All MT5 outputs must be deterministic given identical closed-bar input snapshot.

No runtime state may influence signal generation, including:

- tick data
- current spread
- order state
- fill state
- latency
- account state
- broker execution state
- terminal runtime state

Runtime state may affect execution logs and broker actions only.  
It must never affect StrategyEngine signal output.
