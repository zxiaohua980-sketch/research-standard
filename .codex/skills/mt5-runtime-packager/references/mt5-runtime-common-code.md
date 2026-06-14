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
- `send_market_order_once(...)`
- `close_position_once(...)`
- `magic_positions(...)` and `magic_orders(...)`
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

