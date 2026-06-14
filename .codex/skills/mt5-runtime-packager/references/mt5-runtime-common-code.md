# MT5 Runtime Common Code

Use this reference when building or repairing MT5 Python runtime monitors that need:

- MT5 API closed-bar downloads with the forming bar excluded.
- Enhanced ZigZag calculated in Python from OHLC, including the MA/MSKD-compatible `depth/deviation/backstep` pattern.
- DEMO-only market open/close helpers with magic/comment filtering, SL/TP confirmation, and broker-state reconciliation.
- Intent journals that preserve theoretical entry/SL/TP and join later MT5 order/deal evidence.

## Reusable Module

Copy `scripts/mt5_runtime_common.py` into the runtime source/staging folder when useful. Do not import it from the global skill path inside a packaged EXE.

The module includes:

- `fetch_closed_ohlc(mt5, symbol, timeframe, bars_count=3000, start_pos=1)`
- `calculate_enhanced_zigzag(high_arr, low_arr, depth, deviation, backstep, point_size)`
- `zigzag_points_from_ohlc(rows_old_to_new, point_size, depth=12, deviation=5, backstep=3, tick_size=...)`
- `DemoTradeGates`
- `market_entry_price_from_tick(...)`
- `bid_chart_to_mt5_order_prices(...)`
- `send_market_order_once(...)`
- `close_position_once(...)`
- `magic_positions(...)` and `magic_orders(...)`
- `mt5_account_state_snapshot(...)`
- `format_mt5_account_state_lines(...)`
- `mt5_account_state_blockers(...)`
- `write_mt5_account_state_snapshot(...)`
- `confirm_open_position(...)` and `confirm_position_closed(...)`
- `load_order_intent_latest(...)`
- `export_magic_history_rows(...)`

## Required Runtime Policy

Keep strategy parameters external:

```ini
bars_count = 3000
zigzag_depth = 12
zigzag_deviation = 5
zigzag_backstep = 3
```

Keep order gates safe by default:

```ini
allow_demo_trade = false
dry_run_enforce = true
order_enabled = false
allow_live_trade = false
magic_number = 0
comment_prefix =
mt5_comment_max_length = 16
```

The common module hard-rejects REAL accounts. Do not weaken that in a skill-derived runtime.

## Market/Open Entry Price Pattern

If a strategy enters at the next bar open and the runtime sends an immediate market order at that
time, do not manually add spread to the order request price. Use the broker executable side:

```python
entry_price, entry_price_audit = market_entry_price_from_tick(mt5, "EURUSD", "BUY")
# BUY uses tick.ask; SELL uses tick.bid.
# Do not do raw_open + spread for market/open order_send.
```

Recommended config:

```ini
[orders]
entry_execution_mode = market
market_entry_price_policy = broker_tick_side_no_manual_spread
market_entry_use_tick_side = true
spread_adjust_market_entry = false
spread_risk_accounting = actual_fill_no_extra_spread
```

Use `spread_risk_accounting=actual_fill_no_extra_spread` when the entry-to-SL risk denominator
uses the executable side returned by the broker tick. Use `raw_chart_add_spread_cost` only when
risk is calculated from raw bid-chart levels and spread is not already embedded in entry-to-SL
distance.

## Bid-Chart Pending Entry And SL/TP Pattern

For MT5 bid-chart raw levels:

```text
BUY_STOP / BUY_LIMIT   entry = raw_entry + spread
SELL_STOP / SELL_LIMIT entry = raw_entry

BUY  SL = raw_sl
BUY  TP = raw_tp

SELL SL = raw_sl + spread
SELL TP = raw_tp + spread
```

Use the helper:

```python
prices = bid_chart_to_mt5_order_prices(
    side="SELL",
    entry_execution_mode="pending",
    raw_entry=1.1000,
    raw_sl=1.1050,
    raw_tp=1.0900,
    spread_price=0.0002,
)
# SELL pending entry stays 1.1000.
# SELL SL becomes 1.1052 and SELL TP becomes 1.0902 because the closing side is Ask.
```

Do not use a symmetric add/subtract rule. Buy pending entries trigger on Ask; sell pending entries
trigger on Bid. BUY SL/TP closes on Bid; SELL SL/TP closes on Ask.

## MT5 Account/Magic State Pattern

Do not open MT5 just because a package is being built. Offline package audits should verify that
the code path exists, but should not call `mt5.initialize()`.

Use the account/magic snapshot only in an explicit runtime command, source/EXE smoke test, or
order-enabled startup after the caller has already initialized MT5:

```python
snapshot = mt5_account_state_snapshot(mt5, magic=gates.magic)
for line in format_mt5_account_state_lines(snapshot):
    print(line)
write_mt5_account_state_snapshot(Path("logs"), snapshot)

blockers = mt5_account_state_blockers(
    snapshot,
    expected_account_server=config.expected_account_server or None,
    expected_login=config.expected_login or None,
    require_trade_allowed=config.order_enabled,
    require_zero_magic_positions=config.require_zero_magic_positions_before_smoke,
    require_zero_magic_orders=config.require_zero_magic_orders_before_smoke,
)
if blockers:
    # enter safe mode; do not send orders
    print("MT5 state blockers:", blockers)
```

Expected short console output:

```text
当前账户：ICMarketsSC-Demo
trade_allowed=True
magic 24068 持仓：0
magic 24068 挂单：0
```

The server, login, magic number, and zero-state requirements must come from `config.ini` or the
explicit runtime command. Do not hardcode `ICMarketsSC-Demo` or `24068` into shared helpers.

## ZigZag Usage Pattern

```python
rows = fetch_closed_ohlc(mt5, "EURUSD", "M30", bars_count=3000, start_pos=1)
point, tick_size, _ = point_tick_info(mt5, "EURUSD")
zigzag_rows = zigzag_points_from_ohlc(
    rows,
    point_size=point,
    depth=12,
    deviation=5,
    backstep=3,
    tick_size=tick_size,
)
```

`fetch_closed_ohlc` returns rows sorted oldest to newest and assigns `Bar` so the latest closed bar is `Bar=1`. The ZigZag calculator internally reverses to MT5 series direction where index `0` is newest.

## Demo Order Usage Pattern

```python
gates = DemoTradeGates(
    magic=23082082,
    comment_prefix="MSKD82PKG",
    allow_demo_trade=True,
    dry_run_enforce=False,
    order_enabled=True,
    max_positions=1,
    max_comment=16,
)

summary = send_market_order_once(
    mt5,
    gates,
    symbol="EURUSD",
    side="BUY",
    requested_volume=0.01,
    sl=1.1600,
    tp=1.1700,
    signal_key="EURUSD|M30|candidate|2026-06-01T10:30:00|BUY",
    intent_journal=Path("logs/order_intents.jsonl"),
)
```

Before using `send_market_order_once`, the calling runtime must reserve or consume the signal key in a persistent signal execution ledger. This prevents reopening on the same completed signal bar if the first position closes inside the same candle.

## Close Usage Pattern

```python
for position in magic_positions(mt5, gates.magic, "EURUSD"):
    close_summary = close_position_once(
        mt5,
        gates,
        position,
        intent_journal=Path("logs/order_intents.jsonl"),
        close_scope="full_close",
    )
```

If close confirmation fails, enter manual review or quarantine. Do not assume the close succeeded.

## Packaging Notes

If copied into a runtime, include the module in the PyInstaller staging folder and add it with `--add-data` or direct source copy. After any edit:

1. Rebuild the EXE.
2. Run final `dist` EXE `--mode status`.
3. Run a one-cycle demo monitor with a temporary enabled config.
4. Run the package audit script.
5. Check final magic-number positions and orders are not unexpectedly left open.
