# MT5 Account Reconciliation and Recovery

Use this reference when a runtime can open, modify, or close positions.

## Core Principle

MT5 broker/account state is the source of truth. The local intent journal is only supporting context for recovery and audit.

`order_send()` and its retcode are not enough. The process can crash, the PC can lose power, the network can drop, or MT5 can return a confusing retcode while account state changes. A runtime must reconcile intended actions against positions, pending orders, and recent order/deal history.

## Minimum Intent Model

Persist an intent before every order action:

```json
{
  "intent_id": "20260531T183000123Z-BTCUSD-open-4f7a9c2d",
  "comment_id": "4f7a9c2d",
  "created_at": "2026-05-31T18:30:00",
  "action": "open|modify_sltp|close",
  "close_scope": "none|full|partial",
  "symbol": "BTCUSD",
  "side": "BUY",
  "volume": 0.01,
  "requested_volume": 0.01,
  "previous_volume": 0.01,
  "sl": 100000.0,
  "tp": 101000.0,
  "magic": 11007,
  "comment": "MA11D 4f7a9c2d",
  "status": "created|sent|confirmed|not_confirmed|unknown_manual_review",
  "resolution_note": null,
  "mt5_order": null,
  "mt5_deal": null,
  "position_ticket": null,
  "last_error": null
}
```

Recommended durable stores:

- SQLite with explicit transaction and commit.
- Per-intent JSON state file written atomically: write `*.tmp`, flush, fsync, then `os.replace(tmp, final)`.
- Append-only JSONL only for simple demo runtimes. Treat each line as an immutable event such as `created`, `sent`, `confirmed`, or `manually_resolved`; never update old lines in place. Each append must be flushed/fsynced and startup must ignore or quarantine one corrupt trailing line.

Direct `open(..., "w")` followed by normal write is not enough for recovery state. A crash can leave a half-written record that startup logic may misread.

Prefer SQLite once a runtime can both open and manage positions. JSONL is acceptable only when the implementation explicitly defines event replay and damaged-tail handling.

## Strategy Identity, Magic, And Comment Namespace

`magic_number` and MT5 `comment` are reconciliation keys. They must be configurable per strategy/runtime and must not be shared accidentally.

External config should include:

```ini
strategy_id = STR-007
runtime_id = MA_v1_1
environment_id = demo
magic_number = 11007
comment_prefix = MA11D
```

Rules:

- Use a different `magic_number` for every strategy/version/environment that may run on the same MT5 account.
- Use a short `comment_prefix` namespace for every runtime. Do not hardcode comments like `ma_monitor` across projects.
- Keep MT5 comments short. Many brokers truncate comments around 31 characters, so store the full `intent_id` locally and embed only a short `comment_id` in MT5.
- Use a comment format such as `{comment_prefix} {comment_id}`, for example `MA11D 4f7a9c2d`.
- On startup, treat `magic_number` match plus comment-prefix mismatch as manual review. Do not manage positions that may belong to another runtime.

## Intent ID Generation

Intent ids must be collision-resistant even when two orders are created in the same second.

Recommended:

```python
from datetime import datetime, timezone
from uuid import uuid4


def new_intent_ids(symbol: str, action: str) -> tuple[str, str]:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")[:-3]
    short = uuid4().hex[:8]
    return f"{ts}-{symbol}-{action}-{short}", short
```

Store the full `intent_id` locally. Put only `comment_id` plus a short configurable `comment_prefix` into MT5 `comment`.

## Atomic JSON Write Pattern

```python
import json
import os
from pathlib import Path


def atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=True, sort_keys=True)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
```

## Recovery History Window

`history_orders_get()` and `history_deals_get()` require a time range. Put the window in external config:

```ini
recovery_lookback_days = 7
```

Startup should query:

- the configured lookback window; and
- if unresolved local intents are older, the oldest unresolved intent time minus a safety margin.

Concrete calculation:

```python
from datetime import datetime, timedelta, timezone


def recovery_window_start(now, unresolved_intents, recovery_lookback_days: int):
    configured_start = now - timedelta(days=recovery_lookback_days)
    unresolved_times = [i.created_at for i in unresolved_intents if i.is_unresolved]
    if not unresolved_times:
        return configured_start
    oldest_unresolved = min(unresolved_times)
    return min(configured_start, oldest_unresolved - timedelta(hours=1))


now = datetime.now(timezone.utc)
start = recovery_window_start(now, unresolved_intents, recovery_lookback_days=7)
```

Do not use a hardcoded tiny window. It can miss the order/deal that resolves an interrupted send or close. Do not query unlimited history in a monitor loop.

## Startup Recovery Sequence

Before scanning for new signals:

1. Connect or reconnect to MT5.
2. If `mt5.initialize()` fails, log `mt5.last_error()`, enter safe mode, and do not send orders.
3. If `mt5.terminal_info()` returns `None`, treat MT5 as unavailable, log the condition, and do not send orders.
4. Reject REAL accounts and blocked trade state.
5. Load unresolved local intents. Quarantine corrupt intent records instead of guessing.
6. Query `positions_get()` for current open positions.
7. Query `orders_get()` for current pending orders.
8. Query `history_orders_get(start, end)` and `history_deals_get(start, end)` over the recovery window.
9. Build an MT5 broker-state snapshot filtered by strategy magic, symbol, and comment/intent id.
10. Reconcile local intents against that MT5 snapshot.
11. Scan for MT5 positions/orders with the strategy magic that have no known intent. Treat them as unknown, not as local truth.
12. Write a recovery report row before scanning any new signal.

Two failure modes must be separated:

- Process crash while MT5 stayed online: after restart, current positions/orders/history are queryable and should drive recovery.
- MT5 terminal unavailable or network disconnected: initialize/terminal checks fail or account state cannot be queried. The runtime must stop order actions, retry connection with backoff if designed to run continuously, and avoid opening/closing based on stale local state.

## Matching Priority

Primary keys:

- `position_ticket` for positions;
- order ticket for orders;
- deal ticket for deal history.

Validation fields:

- magic number;
- symbol;
- side/order type;
- comment or embedded `intent_id`;
- open/close time;
- volume;
- price/SL/TP.

If a ticket matches but magic/symbol/comment does not match, do not manage it automatically. Mark critical manual review. A matching ticket with conflicting identity data is more dangerous than no match.

If no ticket is available, an `intent_id` embedded in the MT5 comment is the next best identifier. Fallback matching by symbol/magic/time/volume is weak; if more than one match is possible, quarantine.

## Open Confirmation

An open intent is confirmed only when broker state proves it:

- a matching open position exists; or
- a matching deal/order history record proves the open occurred and the current position state is consistent.

If MT5 has an open position with the strategy magic but no local intent, classify it as `unknown_manual_review`. It may be a manual trade, a leftover from an older runtime, or a magic collision.

If the intent says an open was sent but MT5 has no position, pending order, or history proof, classify it as `sent_not_confirmed` or `unknown_manual_review`. Do not automatically send another open.

Use a bounded confirmation poll after sending:

```python
order_confirm_timeout_seconds = 3
order_confirm_poll_interval_seconds = 1
```

Poll account state until timeout. If the requested state is still not observable, persist `sent_not_confirmed` and enter reconciliation/quarantine policy instead of guessing.

## SL/TP Modify Confirmation

MT5 normalizes prices to symbol precision and tick size. Do not compare floats with exact equality.

Use a tolerance such as:

```python
def price_tolerance(symbol_info) -> float:
    tick_size = getattr(symbol_info, "trade_tick_size", 0.0) or 0.0
    point = getattr(symbol_info, "point", 0.0) or 0.0
    return max(point, tick_size) * 2


def price_matches(actual: float, target: float, symbol_info) -> bool:
    return abs(actual - target) <= price_tolerance(symbol_info)
```

Normalize target prices to the symbol's digits or tick size before sending. Confirm the observed position SL/TP is within tolerance.

## Close Confirmation

Record whether the close is full or partial:

```json
{
  "action": "close",
  "close_scope": "full",
  "position_ticket": 123456,
  "requested_volume": 0.01,
  "previous_volume": 0.01
}
```

Full close confirmation:

- the position ticket is gone or remaining volume is zero; and
- recent history shows a matching close deal/order when available.

Partial close confirmation:

- the remaining position volume is `previous_volume - requested_volume` within volume-step tolerance; or
- MT5 created a replacement/netted position whose remaining volume matches expectation; and
- recent history shows the partial close when available.

A generic "ticket disappeared" check is insufficient if partial close is supported.

## Unknown And Quarantine Policy

Unknown state must have a deterministic behavior.

Default quarantine behavior:

- freeze new opens for the affected symbol and magic number;
- keep status/dry-run scanning and logging if MT5 state can be queried safely;
- allow protective close/SL actions only if explicitly configured and operator-reviewed;
- write a high-visibility alert file or log row such as `logs/manual_review_required.json`;
- include account login, symbol, magic, intent id, ticket, action, and reason;
- keep the state quarantined until a later startup query resolves it or an operator clears it.

Quarantine release conditions:

- Automatic release: a later startup/recovery query finds matching broker order/deal/position evidence and updates the intent to a confirmed terminal status.
- Manual release: an operator explicitly changes the intent/DB status to `manually_resolved` and writes a non-empty `resolution_note`, operator id, and timestamp.
- Escalation only: if an intent exceeds `quarantine_max_days` such as 30 days, raise alert severity, but do not auto-release or auto-fail it.

Manual release must be auditable. Do not use silent file deletion as the normal resolution mechanism.

Do not auto-resolve unknown state just because time has passed. A timeout may escalate alert severity, but it should not silently mark success or failure unless an explicit written policy defines that behavior.

## Pending Orders

Even if the current strategy mostly uses market orders, scan pending orders on startup. A broker-side or future strategy variant may leave pending orders behind. Any pending order with the runtime magic number must be logged, reconciled, and either managed or quarantined before new opens.

## Signal Execution Ledger

Position count is not enough to prevent duplicate opens. A monitor can open a position from a completed signal bar, then the broker can close that position via SL/TP during the current candle. If the monitor only checks "no current position", it can reopen the same signal again.

Every signal-driven runtime that can send demo orders should persist a signal execution ledger before or at the open attempt. A practical JSONL key is:

```text
symbol
timeframe
candidate_id
last_closed_bar_time
last_closed_bar_value
matched_signal_bar
side
```

The ledger status should include at least:

```text
send_attempted
sent_confirmed_open
sent_not_confirmed
unknown_requires_manual_review
order_check_failed
```

Treat these statuses as consuming the signal key. Once consumed, the same completed signal bar must not open again, even if:

- the position was closed by SL/TP in the same candle;
- the runtime process restarts and in-memory `prev_signals` is empty;
- MT5 returns a misleading retcode but broker state later confirms the attempt.

This ledger is separate from the order intent journal. The intent journal answers "what order did we attempt and what happened to it?" The signal execution ledger answers "has this exact signal bar already been used for an open attempt?"

## Audit Signals

A package should WARN or FAIL audit if it can send orders but lacks:

- local intent journal;
- atomic intent write or transactional store;
- configured recovery history window;
- `orders_get()` pending-order scan;
- `history_orders_get()` or `history_deals_get()` reconciliation;
- startup reconciliation before signal scan;
- ticket-first reconciliation and identity validation;
- SL/TP tolerance check;
- full vs partial close semantics;
- MT5 disconnected/reconnect branch;
- unknown/manual-review handling;
- duplicate-open protection after restart;
- same-bar duplicate-open protection via a persistent signal execution ledger.

## Operator Report Fields

Append one row on every startup after reconciliation and before scanning new signals:

```text
logs/startup_report.csv
```

Use append mode, not overwrite, so operational history can be reviewed later. Also write/update a high-visibility manual review file when quarantine exists:

```text
logs/manual_review_required.json
```

Startup report fields:

```text
startup_time
account_login
server
trade_mode
strategy_id
runtime_id
magic
comment_prefix
open_positions_count
pending_orders_count
history_lookback_days
unresolved_intents_count
reconciled_intents_count
unknown_intents_count
quarantined_symbol_magic
manual_review_file
action_gate
decision
```
