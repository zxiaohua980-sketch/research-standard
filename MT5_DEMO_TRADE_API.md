# MT5 Demo Trade API

This helper is for reusable DEMO execution only. It does not decide signals,
SL/TP, position size, filters, trailing rules, or strategy validity.

Canonical shared file:

```text
D:\MT5\RESEARCH_STANDARD\mt5_demo_trade_api.py
```

Strategy packages may include a copied distribution version next to their runtime
files, but the shared source should be maintained in `D:\MT5\RESEARCH_STANDARD`.

## Safety Boundary

- Importing the module does not connect to MT5 and does not trade.
- All order methods require `allow_demo_order=True`.
- REAL accounts are rejected immediately.
- The account must report `trade_mode=0` and `trade_allowed=True`.
- Every `order_send` is checked against actual account state. This matters because
  BTCUSD demo testing observed retcode `10031` even when the broker state changed.
- This API is not forward-live evidence and must not set `framework_start_time`.

## Minimal Pattern

```python
from mt5_demo_trade_api import MT5DemoTradeClient


client = MT5DemoTradeClient(
    magic=92001,
    allow_demo_order=True,
    max_positions=1,
    deviation=3000,
)

client.connect()
try:
    symbol = "BTCUSD"
    tick = client.tick(symbol)

    # The strategy must provide its own audited SL/TP rule.
    sl = tick.ask - 100.0
    tp = tick.ask + 200.0

    opened = client.open_market(
        symbol=symbol,
        side="BUY",
        volume="auto_min",
        sl=sl,
        tp=tp,
        comment="my_strategy_demo",
    )

    client.poll_position(
        ticket=opened.position_ticket,
        hold_seconds=300,
        interval_seconds=60,
    )

    client.close_position(ticket=opened.position_ticket, symbol=symbol)
finally:
    client.disconnect()
```

## Common Calls

```python
client.connect()
client.tick("BTCUSD")
client.normalize_volume("BTCUSD", "auto_min")
client.open_market(symbol="BTCUSD", side="BUY", volume="auto_min", sl=sl, tp=tp)
client.modify_sltp(ticket=ticket, symbol="BTCUSD", sl=new_sl, tp=old_tp)
client.poll_position(ticket=ticket, hold_seconds=300, interval_seconds=60)
client.close_position(ticket=ticket, symbol="BTCUSD")
client.close_all_magic(symbol="BTCUSD")
client.disconnect()
```

## Integration Rule

Other strategies should call this only after they already have a signal, side,
volume, SL, and TP from their own approved strategy logic. Do not put signal
generation or strategy-specific trailing rules into this helper.
