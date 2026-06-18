#!/usr/bin/env python
"""Reusable MT5 runtime helpers for portable Python/EXE monitors.

Copy this module into a runtime package when useful. Do not import it from the
global skill directory inside a packaged EXE. Order helpers are safe-gated by
default: REAL accounts are rejected unless explicit live_trade config gates are present.
"""
from __future__ import annotations

import json
import math
import os
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


TRADE_MODE_DEMO = 0
TRADE_MODE_CONTEST = 1
TRADE_MODE_REAL = 2


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    """Append one durable JSONL record and fsync it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {"ts_utc": utc_now(), **payload}
    with path.open("a", encoding="utf-8", newline="\n") as fobj:
        fobj.write(json.dumps(row, ensure_ascii=False, sort_keys=True, default=str) + "\n")
        fobj.flush()
        os.fsync(fobj.fileno())


def timeframe_const(mt5: Any, timeframe: str) -> int:
    key = timeframe.strip().upper()
    mapping = {
        "M1": mt5.TIMEFRAME_M1,
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "M30": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1,
        "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1,
    }
    if key not in mapping:
        raise ValueError(f"unsupported timeframe: {timeframe}")
    return mapping[key]


def price_digits(tick_size: float) -> int:
    if tick_size <= 0:
        return 5
    text = f"{tick_size:.10f}".rstrip("0")
    return len(text.split(".")[1]) if "." in text else 0


def round_price(price: float, tick_size: float) -> float:
    if tick_size <= 0:
        return float(price)
    return round(round(float(price) / tick_size) * tick_size, price_digits(tick_size))


def nearest_to_tick(price: float, tick_size: float) -> float:
    return round_price(price, tick_size)


def floor_to_tick(price: float, tick_size: float) -> float:
    if tick_size <= 0:
        return float(price)
    return round(math.floor(float(price) / tick_size) * tick_size, price_digits(tick_size))


def ceil_to_tick(price: float, tick_size: float) -> float:
    if tick_size <= 0:
        return float(price)
    return round(math.ceil(float(price) / tick_size) * tick_size, price_digits(tick_size))


def point_tick_info(mt5: Any, symbol: str) -> tuple[float, float, dict[str, Any]]:
    info = mt5.symbol_info(symbol)
    if info is None:
        raise RuntimeError(f"symbol_info unavailable for {symbol}")
    point = float(getattr(info, "point", 0.0) or 0.0)
    tick_size = float(getattr(info, "trade_tick_size", point) or point)
    if tick_size <= 0:
        tick_size = point if point > 0 else 0.00001
    meta = {
        "digits": getattr(info, "digits", ""),
        "point": point,
        "tick_size": tick_size,
        "trade_contract_size": getattr(info, "trade_contract_size", ""),
        "currency_base": getattr(info, "currency_base", ""),
        "currency_profit": getattr(info, "currency_profit", ""),
    }
    return point, tick_size, meta


def calculate_enhanced_zigzag(
    high_arr: list[float],
    low_arr: list[float],
    depth: int,
    deviation: int,
    backstep: int,
    point_size: float,
) -> tuple[list[float], list[float]]:
    """Python port of MA/v1.1_runtime Enhanced ZigZag.

    `high_arr` and `low_arr` use MT5 series direction: index 0 is the newest bar.
    Common MSKD setting is depth=12, deviation=5, backstep=3, but keep these in
    external config for any formal runtime.
    """
    n = len(high_arr)
    high_buf = [0.0] * n
    low_buf = [0.0] * n

    for shift in range(depth, n - depth):
        high_window = high_arr[shift:shift + depth]
        extreme_idx = shift + max(range(len(high_window)), key=high_window.__getitem__)
        extreme_val = high_arr[extreme_idx]
        if extreme_val == high_arr[shift]:
            extreme_counter = 0
            for j in range(shift + 1, min(shift + depth, n)):
                if high_arr[j] >= extreme_val - deviation * point_size:
                    extreme_counter += 1
            if extreme_counter == 0:
                is_valid = True
                for k in range(1, min(backstep, shift) + 1):
                    if high_buf[shift - k] != 0.0:
                        if high_arr[shift] <= high_buf[shift - k]:
                            is_valid = False
                        else:
                            high_buf[shift - k] = 0.0
                if is_valid:
                    high_buf[shift] = high_arr[shift]

        low_window = low_arr[shift:shift + depth]
        extreme_idx = shift + min(range(len(low_window)), key=low_window.__getitem__)
        extreme_val = low_arr[extreme_idx]
        if extreme_val == low_arr[shift]:
            extreme_counter = 0
            for j in range(shift + 1, min(shift + depth, n)):
                if low_arr[j] <= extreme_val + deviation * point_size:
                    extreme_counter += 1
            if extreme_counter == 0:
                is_valid = True
                for k in range(1, min(backstep, shift) + 1):
                    if low_buf[shift - k] != 0.0:
                        if low_arr[shift] >= low_buf[shift - k]:
                            is_valid = False
                        else:
                            low_buf[shift - k] = 0.0
                if is_valid:
                    low_buf[shift] = low_arr[shift]

    return high_buf, low_buf


def fetch_closed_ohlc(
    mt5: Any,
    symbol: str,
    timeframe: str,
    bars_count: int = 3000,
    min_bars: int = 200,
    start_pos: int = 1,
) -> list[dict[str, Any]]:
    """Fetch closed MT5 bars only. start_pos=1 excludes the forming bar."""
    rates = mt5.copy_rates_from_pos(symbol, timeframe_const(mt5, timeframe), start_pos, bars_count)
    if rates is None or len(rates) < min_bars:
        raise RuntimeError(f"copy_rates_from_pos returned {0 if rates is None else len(rates)} bars")
    rows: list[dict[str, Any]] = []
    for rate in rates:
        dt = datetime.fromtimestamp(int(rate["time"]), timezone.utc).replace(tzinfo=None)
        has_tick_volume = hasattr(rate, "dtype") and "tick_volume" in rate.dtype.names
        rows.append(
            {
                "datetime": dt,
                "Date": dt.strftime("%Y-%m-%d"),
                "Time": dt.strftime("%H:%M:%S"),
                "Open": float(rate["open"]),
                "High": float(rate["high"]),
                "Low": float(rate["low"]),
                "Close": float(rate["close"]),
                "Volume": float(rate["tick_volume"]) if has_tick_volume else 0.0,
            }
        )
    rows.sort(key=lambda row: row["datetime"])
    rows = rows[-bars_count:]
    for idx, row in enumerate(rows):
        row["Bar"] = len(rows) - idx
    return rows


def zigzag_points_from_ohlc(
    rows_old_to_new: list[dict[str, Any]],
    point_size: float,
    depth: int = 12,
    deviation: int = 5,
    backstep: int = 3,
    tick_size: float = 0.00001,
) -> list[dict[str, Any]]:
    """Return confirmed ZigZag points from OHLC rows sorted oldest -> newest."""
    rows_rev = list(reversed(rows_old_to_new))
    high_buf, low_buf = calculate_enhanced_zigzag(
        [float(row["High"]) for row in rows_rev],
        [float(row["Low"]) for row in rows_rev],
        depth,
        deviation,
        backstep,
        point_size,
    )
    digits = price_digits(tick_size)
    out: list[dict[str, Any]] = []
    for i in range(len(rows_rev) - 1, -1, -1):
        row = rows_rev[i]
        if high_buf[i] != 0.0:
            out.append(
                {
                    "Date": str(row["Date"]).replace("-", "/"),
                    "Time": row["Time"],
                    "Bar": row.get("Bar", ""),
                    "Price": round(float(high_buf[i]), digits),
                    "Type": "HIGH",
                }
            )
        elif low_buf[i] != 0.0:
            out.append(
                {
                    "Date": str(row["Date"]).replace("-", "/"),
                    "Time": row["Time"],
                    "Bar": row.get("Bar", ""),
                    "Price": round(float(low_buf[i]), digits),
                    "Type": "LOW",
                }
            )
    return out


def normalize_volume(symbol_info: Any, requested: float) -> float:
    volume_min = float(getattr(symbol_info, "volume_min", 0.01) or 0.01)
    volume_max = float(getattr(symbol_info, "volume_max", requested) or requested)
    volume_step = float(getattr(symbol_info, "volume_step", volume_min) or volume_min)
    volume = max(volume_min, min(volume_max, requested))
    steps = round((volume - volume_min) / volume_step)
    return round(volume_min + steps * volume_step, 8)


def magic_positions(mt5: Any, magic: int, symbol: str | None = None) -> list[Any]:
    positions = mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get()
    return [p for p in (positions or []) if int(getattr(p, "magic", 0)) == int(magic)]


def magic_orders(mt5: Any, magic: int, symbol: str | None = None) -> list[Any]:
    orders = mt5.orders_get(symbol=symbol) if symbol else mt5.orders_get()
    return [o for o in (orders or []) if int(getattr(o, "magic", 0)) == int(magic)]


def market_entry_price_from_tick(mt5: Any, symbol: str, side: str) -> tuple[float, dict[str, Any]]:
    """Return the broker executable price for an immediate market/open entry.

    This helper does not initialize MT5 and does not send an order. It only reads
    the current tick and selects the executable side:

    - BUY uses ask;
    - SELL uses bid.

    Do not manually add/subtract spread to this result. If risk is calculated
    from this executable side, use spread_risk_accounting=actual_fill_no_extra_spread
    to avoid double counting spread in the risk denominator.
    """
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        raise RuntimeError(f"symbol_info_tick unavailable for {symbol}")
    bid = float(getattr(tick, "bid", 0.0) or 0.0)
    ask = float(getattr(tick, "ask", 0.0) or 0.0)
    normalized_side = side.strip().upper()
    if normalized_side == "BUY":
        price = ask
    elif normalized_side == "SELL":
        price = bid
    else:
        raise ValueError(f"unsupported side: {side}")
    if price <= 0:
        raise RuntimeError(f"invalid executable price for {symbol} {side}: bid={bid}, ask={ask}")
    return price, {
        "symbol": symbol,
        "side": normalized_side,
        "bid": bid,
        "ask": ask,
        "selected_entry_price": price,
        "market_entry_price_policy": "broker_tick_side_no_manual_spread",
    }


def spread_price_from_tick(mt5: Any, symbol: str) -> tuple[float, dict[str, Any]]:
    """Return current broker spread as ``tick.ask - tick.bid``.

    This helper is import-safe: it does not initialize MT5 and does not send an
    order. Call it only inside an intentional runtime/smoke/order path after the
    caller has initialized MT5.
    """
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        raise RuntimeError(f"symbol_info_tick unavailable for {symbol}")
    info = mt5.symbol_info(symbol)
    bid = float(getattr(tick, "bid", 0.0) or 0.0)
    ask = float(getattr(tick, "ask", 0.0) or 0.0)
    if bid <= 0 or ask <= 0 or ask < bid:
        raise RuntimeError(f"invalid bid/ask for spread on {symbol}: bid={bid}, ask={ask}")

    point = float(getattr(info, "point", 0.0) or 0.0) if info is not None else 0.0
    time_msc = getattr(tick, "time_msc", None)
    spread_price = ask - bid
    spread_points = spread_price / point if point > 0 else None
    return spread_price, {
        "symbol": symbol,
        "spread_source": "mt5_tick",
        "spread_formula": "symbol_info_tick.ask - symbol_info_tick.bid",
        "bid": bid,
        "ask": ask,
        "point": point,
        "spread_price": spread_price,
        "spread_points": spread_points,
        "tick_time": getattr(tick, "time", None),
        "tick_time_msc": time_msc,
    }


def bid_chart_to_mt5_order_prices(
    *,
    side: str,
    spread_price: float,
    raw_entry: float | None = None,
    raw_sl: float | None = None,
    raw_tp: float | None = None,
    entry_execution_mode: str = "pending",
) -> dict[str, Any]:
    """Convert raw bid-chart strategy levels to MT5 bid/ask order prices.

    For FX/CFD symbols, MT5 chart OHLC is normally Bid-based. Under that default:

    - BUY market/open entry uses broker Ask and should not call this to add spread.
    - SELL market/open entry uses broker Bid and should not call this to subtract spread.
    - BUY pending entries (Buy Stop/Buy Limit) trigger on Ask, so add spread.
    - SELL pending entries (Sell Stop/Sell Limit) trigger on Bid, so do not adjust entry.
    - BUY position SL/TP close on Bid, so do not adjust SL/TP.
    - SELL position SL/TP close on Ask, so add spread to SL/TP.

    ``spread_price`` must be non-negative. For live/demo order-capable runtimes,
    prefer ``spread_price_from_tick(mt5, symbol)`` so the source is
    ``symbol_info_tick().ask - symbol_info_tick().bid`` at decision time. Fixed
    spread points are acceptable only when config explicitly selects them.

    The function returns both adjusted prices and an audit dictionary. It performs no MT5 I/O.
    """
    normalized_side = side.strip().upper()
    if normalized_side not in {"BUY", "SELL"}:
        raise ValueError(f"unsupported side: {side}")
    spread = float(spread_price or 0.0)
    if spread < 0:
        raise ValueError(f"spread_price must be non-negative: {spread_price}")

    adjusted_entry: float | None = None
    adjusted_sl: float | None = None
    adjusted_tp: float | None = None
    mode = entry_execution_mode.strip().lower()

    if raw_entry is not None:
        if mode == "pending":
            adjusted_entry = float(raw_entry) + spread if normalized_side == "BUY" else float(raw_entry)
        elif mode in {"market", "open", "open_price"}:
            adjusted_entry = None
        else:
            raise ValueError(f"unsupported entry_execution_mode: {entry_execution_mode}")

    if raw_sl is not None:
        adjusted_sl = float(raw_sl) if normalized_side == "BUY" else float(raw_sl) + spread
    if raw_tp is not None:
        adjusted_tp = float(raw_tp) if normalized_side == "BUY" else float(raw_tp) + spread

    return {
        "side": normalized_side,
        "signal_price_basis": "bid_chart",
        "pending_price_policy": "broker_bidask_from_bid_chart",
        "sltp_price_policy": "broker_bidask_from_bid_chart",
        "entry_execution_mode": mode,
        "spread_price": spread,
        "raw_entry": raw_entry,
        "raw_sl": raw_sl,
        "raw_tp": raw_tp,
        "adjusted_entry": adjusted_entry,
        "adjusted_sl": adjusted_sl,
        "adjusted_tp": adjusted_tp,
        "rules": {
            "buy_pending_entry": "raw_entry + spread_price",
            "sell_pending_entry": "raw_entry",
            "buy_sltp": "raw_sl/raw_tp",
            "sell_sltp": "raw_sl/raw_tp + spread_price",
        },
    }


def broker_trigger_side_order_prices(
    *,
    side: str,
    raw_entry: float | None = None,
    raw_sl: float | None = None,
    raw_tp: float | None = None,
    entry_execution_mode: str = "pending",
) -> dict[str, Any]:
    """Return order prices when raw levels are already MT5 trigger-side prices.

    This is the recommended live/demo EXE policy when the strategy/runtime
    computes prices directly from a fresh broker tick:

    - BUY pending entry raw_entry is the desired Ask trigger price.
    - SELL pending entry raw_entry is the desired Bid trigger price.
    - BUY SL/TP raw levels are desired Bid exit trigger prices.
    - SELL SL/TP raw levels are desired Ask exit trigger prices.

    No spread is added or subtracted here. Spread conversion belongs only to
    explicit basis conversions such as Bid-bar levels -> broker trigger side.
    """
    normalized_side = side.strip().upper()
    if normalized_side not in {"BUY", "SELL"}:
        raise ValueError(f"unsupported side: {side}")
    mode = entry_execution_mode.strip().lower()
    if mode not in {"pending", "market", "open", "open_price"}:
        raise ValueError(f"unsupported entry_execution_mode: {entry_execution_mode}")

    adjusted_entry: float | None = None
    if raw_entry is not None and mode == "pending":
        adjusted_entry = float(raw_entry)

    return {
        "side": normalized_side,
        "signal_price_basis": "broker_trigger_side",
        "pending_price_policy": "broker_trigger_side",
        "sltp_price_policy": "broker_exit_trigger_side",
        "entry_execution_mode": mode,
        "spread_price": 0.0,
        "raw_entry": raw_entry,
        "raw_sl": raw_sl,
        "raw_tp": raw_tp,
        "adjusted_entry": adjusted_entry,
        "adjusted_sl": None if raw_sl is None else float(raw_sl),
        "adjusted_tp": None if raw_tp is None else float(raw_tp),
        "rules": {
            "buy_pending_entry": "raw_entry is desired Ask trigger price",
            "sell_pending_entry": "raw_entry is desired Bid trigger price",
            "buy_sltp": "raw_sl/raw_tp are desired Bid exit triggers",
            "sell_sltp": "raw_sl/raw_tp are desired Ask exit triggers",
            "spread_conversion": "none; levels already use broker trigger side",
        },
    }


def symbol_chart_mode_snapshot(mt5: Any, symbol: str) -> dict[str, Any]:
    """Return MT5 chart-mode metadata for one symbol.

    Useful when a runtime wants to prove that a Bid-bar conversion policy is
    valid on the current live symbol before applying spread adjustments derived
    from Bid-side bar levels.
    """
    info = mt5.symbol_info(symbol)
    if info is None:
        raise RuntimeError(f"symbol_info unavailable for {symbol}")
    chart_mode = getattr(info, "chart_mode", None)
    bid_const = getattr(mt5, "SYMBOL_CHART_MODE_BID", None)
    last_const = getattr(mt5, "SYMBOL_CHART_MODE_LAST", None)
    return {
        "symbol": symbol,
        "chart_mode": chart_mode,
        "symbol_chart_mode_bid": bid_const,
        "symbol_chart_mode_last": last_const,
        "is_bid_chart_mode": chart_mode == bid_const if bid_const is not None else None,
    }


def min_pending_distance_from_symbol_info(
    symbol_info: Any,
    *,
    buffer_points: float = 0.0,
) -> tuple[float, dict[str, Any]]:
    """Return conservative broker minimum distance for pending order placement.

    MT5 symbols expose ``trade_stops_level`` for minimum stop/pending distance
    and ``trade_freeze_level`` for the near-market zone where order changes may
    be blocked. For runtime safety we use the larger value plus a configurable
    buffer. This helper performs no MT5 I/O.
    """
    point = float(getattr(symbol_info, "point", 0.0) or 0.0)
    stops_level = float(getattr(symbol_info, "trade_stops_level", 0.0) or 0.0)
    freeze_level = float(getattr(symbol_info, "trade_freeze_level", 0.0) or 0.0)
    buffer = float(buffer_points or 0.0)
    min_distance_points = max(stops_level, freeze_level) + buffer
    min_distance_price = min_distance_points * point
    return min_distance_price, {
        "point": point,
        "trade_stops_level": stops_level,
        "trade_freeze_level": freeze_level,
        "buffer_points": buffer,
        "min_distance_points": min_distance_points,
        "min_distance_price": min_distance_price,
    }


def pending_entry_state_from_tick(
    *,
    order_type: str,
    adjusted_entry: float,
    tick_bid: float,
    tick_ask: float,
    min_distance_price: float = 0.0,
) -> dict[str, Any]:
    """Classify whether a pending entry should be placed, watched, or market-converted.

    The returned ``action`` is one of:

    - ``place_pending``: original adjusted entry is far enough from current price;
    - ``convert_to_market``: trigger side has already reached the adjusted entry;
    - ``armed_trigger_watch``: entry is not triggered but is too close to place.

    Use this after a pending ``order_send`` invalid-price/invalid-stops/requote
    response as well as before the initial pending send. Reuse the same
    signal/intent id; do not create duplicate order intents.
    """
    kind = order_type.strip().upper()
    aliases = {
        "BUY": "BUY_STOP",
        "SELL": "SELL_STOP",
        "BUYSTOP": "BUY_STOP",
        "SELLSTOP": "SELL_STOP",
        "BUYLIMIT": "BUY_LIMIT",
        "SELLLIMIT": "SELL_LIMIT",
    }
    kind = aliases.get(kind, kind)
    if kind not in {"BUY_STOP", "SELL_STOP", "BUY_LIMIT", "SELL_LIMIT"}:
        raise ValueError(f"unsupported pending order_type: {order_type}")
    entry = float(adjusted_entry)
    bid = float(tick_bid)
    ask = float(tick_ask)
    min_dist = max(0.0, float(min_distance_price or 0.0))
    if entry <= 0 or bid <= 0 or ask <= 0 or ask < bid:
        raise ValueError(f"invalid pending state prices: entry={entry}, bid={bid}, ask={ask}")

    if kind == "BUY_STOP":
        trigger_side = "ask"
        trigger_price = ask
        already_triggered = ask >= entry
        distance_price = entry - ask
        placeable = entry > ask + min_dist
        market_side = "BUY"
    elif kind == "SELL_STOP":
        trigger_side = "bid"
        trigger_price = bid
        already_triggered = bid <= entry
        distance_price = bid - entry
        placeable = entry < bid - min_dist
        market_side = "SELL"
    elif kind == "BUY_LIMIT":
        trigger_side = "ask"
        trigger_price = ask
        already_triggered = ask <= entry
        distance_price = ask - entry
        placeable = entry < ask - min_dist
        market_side = "BUY"
    else:  # SELL_LIMIT
        trigger_side = "bid"
        trigger_price = bid
        already_triggered = bid >= entry
        distance_price = entry - bid
        placeable = entry > bid + min_dist
        market_side = "SELL"

    if already_triggered:
        action = "convert_to_market"
        reason = "trigger_side_already_reached_adjusted_entry"
    elif placeable:
        action = "place_pending"
        reason = "broker_min_distance_satisfied"
    else:
        action = "armed_trigger_watch"
        reason = "inside_broker_min_distance_wait_tick_or_market_if_triggered"

    return {
        "order_type": kind,
        "market_side": market_side,
        "adjusted_entry": entry,
        "bid": bid,
        "ask": ask,
        "trigger_side": trigger_side,
        "trigger_price": trigger_price,
        "already_triggered": already_triggered,
        "distance_price": distance_price,
        "min_distance_price": min_dist,
        "placeable": placeable,
        "action": action,
        "reason": reason,
        "pending_too_close_policy": "wait_until_valid_or_market_if_triggered",
    }


def trade_mode_label(trade_mode: int | None) -> str:
    """Return a stable label for MT5 account trade_mode values."""
    if trade_mode == TRADE_MODE_DEMO:
        return "DEMO"
    if trade_mode == TRADE_MODE_CONTEST:
        return "CONTEST"
    if trade_mode == TRADE_MODE_REAL:
        return "REAL"
    return f"UNKNOWN({trade_mode})"


def _mt5_fields(item: Any, fields: tuple[str, ...]) -> dict[str, Any]:
    """Extract serializable public fields from MT5 namedtuple-like objects."""
    return {field: getattr(item, field, None) for field in fields}


def mt5_account_state_snapshot(
    mt5: Any,
    magic: int,
    symbol: str | None = None,
    include_details: bool = True,
) -> dict[str, Any]:
    """Collect an account/magic snapshot after the caller has initialized MT5.

    This helper is deliberately side-effect light:

    - it does not call ``mt5.initialize()``;
    - it does not open the terminal;
    - it does not send, modify, or close orders.

    Use it inside source-run preflight, final EXE smoke, or immediately before
    order-enabled runtime logic. Build/package scripts should only statically
    verify that this code path exists unless the user explicitly requested a
    live MT5 smoke test.
    """
    errors: list[str] = []
    account = None
    terminal = None
    positions: list[Any] = []
    orders: list[Any] = []

    try:
        account = mt5.account_info()
    except Exception as exc:  # pragma: no cover - depends on external MT5 state
        errors.append(f"account_info failed: {exc}")

    try:
        terminal = mt5.terminal_info()
    except Exception as exc:  # pragma: no cover - depends on external MT5 state
        errors.append(f"terminal_info failed: {exc}")

    try:
        positions = magic_positions(mt5, magic, symbol)
    except Exception as exc:  # pragma: no cover - depends on external MT5 state
        errors.append(f"positions_get failed: {exc}")

    try:
        orders = magic_orders(mt5, magic, symbol)
    except Exception as exc:  # pragma: no cover - depends on external MT5 state
        errors.append(f"orders_get failed: {exc}")

    trade_mode_raw = getattr(account, "trade_mode", None) if account is not None else None
    trade_mode = int(trade_mode_raw) if trade_mode_raw is not None else None
    account_trade_allowed = bool(getattr(account, "trade_allowed", False)) if account is not None else False
    terminal_trade_allowed = (
        bool(getattr(terminal, "trade_allowed", False)) if terminal is not None else False
    )
    effective_trade_allowed = account_trade_allowed and terminal_trade_allowed

    snapshot: dict[str, Any] = {
        "checked_at_utc": utc_now(),
        "magic": int(magic),
        "symbol_filter": symbol,
        "account_login": getattr(account, "login", None) if account is not None else None,
        "account_server": getattr(account, "server", None) if account is not None else None,
        "account_name": getattr(account, "name", None) if account is not None else None,
        "trade_mode": trade_mode,
        "trade_mode_label": trade_mode_label(trade_mode),
        "account_trade_allowed": account_trade_allowed,
        "terminal_trade_allowed": terminal_trade_allowed,
        "trade_allowed": effective_trade_allowed,
        "terminal_connected": terminal is not None,
        "magic_positions_count": len(positions),
        "magic_orders_count": len(orders),
        "errors": errors,
    }

    last_error = None
    try:
        last_error = mt5.last_error()
    except Exception:  # pragma: no cover - depends on external MT5 module
        last_error = None
    if last_error:
        snapshot["last_error"] = last_error

    if include_details:
        position_fields = (
            "ticket",
            "time",
            "time_msc",
            "symbol",
            "type",
            "volume",
            "price_open",
            "sl",
            "tp",
            "magic",
            "comment",
        )
        order_fields = (
            "ticket",
            "time_setup",
            "time_setup_msc",
            "symbol",
            "type",
            "volume_initial",
            "volume_current",
            "price_open",
            "sl",
            "tp",
            "magic",
            "comment",
        )
        snapshot["positions"] = [_mt5_fields(item, position_fields) for item in positions]
        snapshot["orders"] = [_mt5_fields(item, order_fields) for item in orders]

    return snapshot


def format_mt5_account_state_lines(snapshot: dict[str, Any]) -> list[str]:
    """Format the short human-readable status block used in runtime logs."""
    account = snapshot.get("account_server") or "UNKNOWN"
    magic = snapshot.get("magic")
    return [
        f"当前账户：{account}",
        f"trade_allowed={bool(snapshot.get('trade_allowed', False))}",
        f"magic {magic} 持仓：{int(snapshot.get('magic_positions_count', 0))}",
        f"magic {magic} 挂单：{int(snapshot.get('magic_orders_count', 0))}",
    ]


def mt5_account_state_blockers(
    snapshot: dict[str, Any],
    expected_account_server: str | None = None,
    expected_login: int | None = None,
    require_trade_allowed: bool = True,
    require_zero_magic_positions: bool = False,
    require_zero_magic_orders: bool = False,
    allow_real_account: bool = False,
) -> list[str]:
    """Return blockers for order-enabled runtime startup.

    The caller decides strictness from config. For example, a dry-run scanner can
    collect a snapshot without requiring zero positions, while a demo order smoke
    test can require both zero magic positions and zero magic pending orders.
    """
    blockers: list[str] = []
    if snapshot.get("account_server") is None:
        blockers.append("MT5 account_info unavailable")
    if not snapshot.get("terminal_connected", False):
        blockers.append("MT5 terminal_info unavailable")
    if expected_account_server and snapshot.get("account_server") != expected_account_server:
        blockers.append(
            f"account_server mismatch: expected {expected_account_server}, "
            f"got {snapshot.get('account_server')}"
        )
    if expected_login is not None and snapshot.get("account_login") != expected_login:
        blockers.append(
            f"account_login mismatch: expected {expected_login}, got {snapshot.get('account_login')}"
        )
    if snapshot.get("trade_mode_label") == "REAL" and not allow_real_account:
        blockers.append("REAL account is rejected unless explicit live_trade authorization is enabled")
    if require_trade_allowed and not bool(snapshot.get("trade_allowed", False)):
        blockers.append("trade_allowed is false")
    if require_zero_magic_positions and int(snapshot.get("magic_positions_count", 0)) != 0:
        blockers.append(f"magic positions not zero: {snapshot.get('magic_positions_count')}")
    if require_zero_magic_orders and int(snapshot.get("magic_orders_count", 0)) != 0:
        blockers.append(f"magic pending orders not zero: {snapshot.get('magic_orders_count')}")
    blockers.extend(str(item) for item in snapshot.get("errors", []))
    return blockers


def write_mt5_account_state_snapshot(
    log_dir: Path,
    snapshot: dict[str, Any],
    filename: str = "mt5_account_state.jsonl",
) -> None:
    """Append the account/magic snapshot to runtime logs."""
    append_jsonl(log_dir / filename, {"event": "mt5_account_state_snapshot", **snapshot})


def mt5_comment_id(comment_prefix: str, intent_id: str, max_comment: int = 31, timeframe: str = "") -> str:
    comment_id = intent_id[:8]
    prefix = comment_prefix.strip() or "MT5"
    tf = str(timeframe or "").strip().upper()
    comment = f"{prefix}_{tf}_{comment_id}" if tf else f"{prefix}_{comment_id}"
    if len(comment) > max_comment:
        short_id = comment_id[:4]
        if tf:
            prefix_room = max(0, max_comment - len(tf) - len(short_id) - 2)
            comment = f"{prefix[:prefix_room]}_{tf}_{short_id}" if prefix_room else f"{tf}_{short_id}"
        else:
            prefix_room = max(0, max_comment - len(short_id) - 1)
            comment = f"{prefix[:prefix_room]}_{short_id}" if prefix_room else short_id[:max_comment]
    return comment[:max_comment]


def mt5_filling_mode(mt5: Any, mode: str = "IOC") -> int:
    key = str(mode or "IOC").upper()
    if key == "FOK":
        return mt5.ORDER_FILLING_FOK
    if key == "RETURN":
        return mt5.ORDER_FILLING_RETURN
    return mt5.ORDER_FILLING_IOC


@dataclass
class DemoTradeGates:
    magic: int
    comment_prefix: str
    allow_demo_trade: bool = False
    allow_live_trade: bool = False
    live_trade_ack: str = ""
    mode: str = "demo_trade"
    dry_run_enforce: bool = True
    order_enabled: bool = False
    kill_switch: bool = False
    max_positions: int = 1
    max_comment: int = 31
    deviation_points: int = 20
    filling_mode: str = "IOC"
    order_confirm_timeout_seconds: float = 3.0
    order_confirm_poll_interval_seconds: float = 0.25


def demo_trade_gate_reasons(mt5: Any, gates: DemoTradeGates) -> list[str]:
    """Return order gate blockers for demo or explicitly-authorized live trading."""
    reasons: list[str] = []
    account = mt5.account_info()
    terminal = mt5.terminal_info()
    mode = str(getattr(gates, "mode", "demo_trade") or "demo_trade").lower()
    live_requested = mode == "live_trade" or bool(getattr(gates, "allow_live_trade", False))
    live_ack_ok = str(getattr(gates, "live_trade_ack", "")) == "I_ACCEPT_REAL_MONEY_RISK"
    if gates.kill_switch:
        reasons.append("kill_switch=true")
    if gates.dry_run_enforce:
        reasons.append("dry_run_enforce=true")
    if live_requested:
        if mode != "live_trade":
            reasons.append("allow_live_trade=true requires mode=live_trade")
        if not gates.allow_live_trade:
            reasons.append("allow_live_trade=false")
        if not live_ack_ok:
            reasons.append("live_trade_ack must equal I_ACCEPT_REAL_MONEY_RISK")
    else:
        if not gates.allow_demo_trade:
            reasons.append("allow_demo_trade=false")
    if not gates.order_enabled:
        reasons.append("order_enabled=false")
    if int(gates.magic) <= 0:
        reasons.append("magic must be positive")
    if not gates.comment_prefix:
        reasons.append("comment_prefix is required")
    if account is None:
        reasons.append("MT5 account_info unavailable")
        return reasons
    if terminal is None:
        reasons.append("MT5 terminal_info unavailable")
    trade_mode = int(getattr(account, "trade_mode", -1))
    if trade_mode == TRADE_MODE_REAL:
        if not (live_requested and live_ack_ok and gates.allow_live_trade and mode == "live_trade"):
            reasons.append("REAL account requires explicit live_trade authorization")
    elif trade_mode in (TRADE_MODE_DEMO, TRADE_MODE_CONTEST):
        if live_requested:
            reasons.append("live_trade mode requires a REAL account; use demo_trade for DEMO/CONTEST")
    else:
        reasons.append(f"unknown trade_mode={trade_mode}")
    if not bool(getattr(account, "trade_allowed", False)):
        reasons.append("account trade_allowed is false")
    if terminal is not None and not bool(getattr(terminal, "trade_allowed", True)):
        reasons.append("terminal trade_allowed is false")
    return reasons


def prices_match(actual: float, expected: float, tolerance: float) -> bool:
    return abs(float(actual or 0.0) - float(expected or 0.0)) <= tolerance


def validate_position_identity(position: Any, symbol: str, magic: int, comment: str) -> list[str]:
    conflicts: list[str] = []
    ticket = getattr(position, "ticket", "")
    if str(getattr(position, "symbol", "")) != symbol:
        conflicts.append(f"symbol mismatch ticket={ticket}")
    if int(getattr(position, "magic", 0)) != int(magic):
        conflicts.append(f"magic mismatch ticket={ticket}")
    broker_comment = str(getattr(position, "comment", ""))
    if comment and broker_comment != comment and comment[: len(broker_comment)] != broker_comment:
        conflicts.append(f"comment mismatch ticket={ticket}")
    if conflicts:
        conflicts.append(f"identity mismatch ticket={ticket}")
    return conflicts


def confirm_open_position(
    mt5: Any,
    symbol: str,
    magic: int,
    comment: str,
    expected_sl: float,
    expected_tp: float,
    tick_size: float,
    timeout_seconds: float = 3.0,
    poll_interval_seconds: float = 0.25,
) -> tuple[str, list[Any], list[str]]:
    tolerance = max(float(tick_size), 0.0) * 2.0
    deadline = time.time() + max(0.2, float(timeout_seconds))
    conflicts: list[str] = []
    confirmed: list[Any] = []
    while time.time() <= deadline:
        for position in magic_positions(mt5, magic, symbol):
            identity_conflicts = validate_position_identity(position, symbol, magic, comment)
            if identity_conflicts:
                conflicts.extend(identity_conflicts)
                continue
            sltp_conflicts = []
            if not prices_match(float(getattr(position, "sl", 0.0) or 0.0), expected_sl, tolerance):
                sltp_conflicts.append(f"sltp sl tolerance mismatch ticket={getattr(position, 'ticket', '')}")
            if not prices_match(float(getattr(position, "tp", 0.0) or 0.0), expected_tp, tolerance):
                sltp_conflicts.append(f"sltp tp tolerance mismatch ticket={getattr(position, 'ticket', '')}")
            if sltp_conflicts:
                conflicts.extend(sltp_conflicts)
                continue
            confirmed.append(position)
        if confirmed or conflicts:
            break
        time.sleep(max(0.1, float(poll_interval_seconds)))
    return ("sent_confirmed_open" if confirmed else "sent_not_confirmed"), confirmed, conflicts


def confirm_position_closed(
    mt5: Any,
    position_ticket: int,
    timeout_seconds: float = 3.0,
    poll_interval_seconds: float = 0.25,
) -> bool:
    deadline = time.time() + max(0.2, float(timeout_seconds))
    while time.time() <= deadline:
        remaining = [
            p for p in (mt5.positions_get() or [])
            if int(getattr(p, "ticket", 0)) == int(position_ticket)
        ]
        if not remaining:
            return True
        time.sleep(max(0.1, float(poll_interval_seconds)))
    return False


def send_market_order_once(
    mt5: Any,
    gates: DemoTradeGates,
    symbol: str,
    side: str,
    requested_volume: float,
    sl: float,
    tp: float,
    signal_key: str,
    intent_journal: Path | None = None,
    block_if_symbol_position_exists: bool = True,
    timeframe: str = "",
) -> dict[str, Any]:
    """Send one DEMO market order after gates, journal, and duplicate-state checks."""
    reasons = demo_trade_gate_reasons(mt5, gates)
    if reasons:
        return {"status": "blocked_by_gates", "reasons": reasons, "sent": False}
    if len(magic_positions(mt5, gates.magic)) + len(magic_orders(mt5, gates.magic)) >= gates.max_positions:
        return {"status": "blocked_max_positions", "sent": False}
    if block_if_symbol_position_exists and (magic_positions(mt5, gates.magic, symbol) or magic_orders(mt5, gates.magic, symbol)):
        return {"status": "blocked_existing_symbol_state", "sent": False}

    side = side.upper()
    if side not in ("BUY", "SELL"):
        raise ValueError(f"unsupported side: {side}")
    mt5.symbol_select(symbol, True)
    info = mt5.symbol_info(symbol)
    tick = mt5.symbol_info_tick(symbol)
    if info is None or tick is None:
        return {"status": "blocked_no_symbol_tick", "sent": False}
    _, tick_size, _ = point_tick_info(mt5, symbol)
    volume = normalize_volume(info, requested_volume)
    order_type = mt5.ORDER_TYPE_BUY if side == "BUY" else mt5.ORDER_TYPE_SELL
    entry_price = float(tick.ask if side == "BUY" else tick.bid)
    intent_id = uuid.uuid4().hex
    comment = mt5_comment_id(gates.comment_prefix, intent_id, max_comment=gates.max_comment, timeframe=timeframe)
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": round_price(entry_price, tick_size),
        "sl": round_price(sl, tick_size),
        "tp": round_price(tp, tick_size),
        "deviation": gates.deviation_points,
        "magic": int(gates.magic),
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5_filling_mode(mt5, gates.filling_mode),
    }
    if intent_journal is not None:
        append_jsonl(
            intent_journal,
            {
                "intent_id": intent_id,
                "signal_key": signal_key,
                "status": "created_before_order_send",
                "symbol": symbol,
                "side": side,
                "volume": volume,
                "requested_volume": requested_volume,
                "previous_volume": 0.0,
                "close_scope": "none_open_intent",
                "entry_price": request["price"],
                "sl": request["sl"],
                "tp": request["tp"],
                "theoretical_entry_price": request["price"],
                "theoretical_sl_price": request["sl"],
                "theoretical_tp_price": request["tp"],
                "magic": gates.magic,
                "comment": comment,
            },
        )

    result = mt5.order_send(request)
    retcode = getattr(result, "retcode", None) if result is not None else None
    order_id = getattr(result, "order", "") if result is not None else ""
    deal_id = getattr(result, "deal", "") if result is not None else ""
    status, confirmed, conflicts = confirm_open_position(
        mt5,
        symbol,
        gates.magic,
        comment,
        request["sl"],
        request["tp"],
        tick_size,
        gates.order_confirm_timeout_seconds,
        gates.order_confirm_poll_interval_seconds,
    )
    if conflicts and not confirmed:
        status = "unknown_requires_manual_review"
    position = confirmed[0] if confirmed else None
    summary = {
        "intent_id": intent_id,
        "signal_key": signal_key,
        "status": status,
        "sent": bool(confirmed),
        "retcode": retcode,
        "order": order_id,
        "deal": deal_id,
        "symbol": symbol,
        "side": side,
        "volume": volume,
        "comment": comment,
        "request": request,
        "confirmed_positions": len(confirmed),
        "identity_conflicts": conflicts,
        "actual_position_ticket": getattr(position, "ticket", "") if position else "",
        "actual_open_price": getattr(position, "price_open", "") if position else "",
        "actual_sl": getattr(position, "sl", "") if position else "",
        "actual_tp": getattr(position, "tp", "") if position else "",
    }
    if intent_journal is not None:
        append_jsonl(intent_journal, {k: v for k, v in summary.items() if k != "request"})
    return summary


def close_position_once(
    mt5: Any,
    gates: DemoTradeGates,
    position: Any,
    intent_journal: Path | None = None,
    close_scope: str = "full_close",
) -> dict[str, Any]:
    """Close one MT5 position once, then confirm the ticket is gone."""
    reasons = demo_trade_gate_reasons(mt5, gates)
    if reasons:
        return {"status": "blocked_by_gates", "reasons": reasons, "closed": False}
    symbol = str(getattr(position, "symbol", ""))
    ticket = int(getattr(position, "ticket", 0))
    volume = float(getattr(position, "volume", 0.0) or 0.0)
    mt5.symbol_select(symbol, True)
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return {"status": "blocked_no_tick", "closed": False, "ticket": ticket}
    _, tick_size, _ = point_tick_info(mt5, symbol)
    close_type = mt5.ORDER_TYPE_SELL if int(getattr(position, "type", 0)) == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
    price = float(tick.bid if close_type == mt5.ORDER_TYPE_SELL else tick.ask)
    intent_id = uuid.uuid4().hex
    comment = mt5_comment_id(gates.comment_prefix, intent_id, max_comment=gates.max_comment)
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": close_type,
        "position": ticket,
        "price": round_price(price, tick_size),
        "deviation": gates.deviation_points,
        "magic": int(gates.magic),
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5_filling_mode(mt5, gates.filling_mode),
    }
    if intent_journal is not None:
        append_jsonl(
            intent_journal,
            {
                "intent_id": intent_id,
                "signal_key": "manual_or_runtime_close",
                "status": "close_before_order_send",
                "symbol": symbol,
                "side": "CLOSE",
                "volume": volume,
                "requested_volume": volume,
                "previous_volume": volume,
                "close_scope": close_scope,
                "magic": gates.magic,
                "comment": comment,
                "actual_position_ticket": ticket,
            },
        )
    result = mt5.order_send(request)
    retcode = getattr(result, "retcode", None) if result is not None else None
    order_id = getattr(result, "order", "") if result is not None else ""
    deal_id = getattr(result, "deal", "") if result is not None else ""
    closed = confirm_position_closed(
        mt5,
        ticket,
        gates.order_confirm_timeout_seconds,
        gates.order_confirm_poll_interval_seconds,
    )
    status = "close_confirmed" if closed else "close_not_confirmed"
    summary = {
        "intent_id": intent_id,
        "status": status,
        "closed": closed,
        "retcode": retcode,
        "order": order_id,
        "deal": deal_id,
        "symbol": symbol,
        "volume": volume,
        "comment": comment,
        "ticket": ticket,
    }
    if intent_journal is not None:
        append_jsonl(intent_journal, summary)
    return summary


def load_order_intent_latest(log_dir: Path) -> dict[str, dict[str, Any]]:
    """Merge append-only intent rows by intent_id, preserving original non-empty context."""
    path = log_dir / "order_intents.jsonl"
    latest: dict[str, dict[str, Any]] = {}
    if not path.exists():
        return latest
    with path.open("r", encoding="utf-8") as fobj:
        for line in fobj:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except Exception:
                continue
            intent_id = str(payload.get("intent_id", "")).strip()
            if not intent_id:
                continue
            merged = dict(latest.get(intent_id, {}))
            for key, value in payload.items():
                if value not in ("", None, []):
                    merged[key] = value
                elif key not in merged:
                    merged[key] = value
            latest[intent_id] = merged
    return latest


def export_magic_history_rows(
    mt5: Any,
    magic: int,
    lookback_days: int = 7,
    history_future_buffer_hours: float = 12.0,
) -> dict[str, list[dict[str, Any]]]:
    """Return recent MT5 order/deal history rows for one magic number."""
    utc_to = datetime.now(timezone.utc) + timedelta(hours=max(0.0, history_future_buffer_hours))
    utc_from = utc_to - timedelta(days=max(1, int(lookback_days)))
    orders = [
        item for item in (mt5.history_orders_get(utc_from, utc_to) or [])
        if int(getattr(item, "magic", 0)) == int(magic)
    ]
    deals = [
        item for item in (mt5.history_deals_get(utc_from, utc_to) or [])
        if int(getattr(item, "magic", 0)) == int(magic)
    ]
    order_fields = [
        "ticket", "time_setup", "time_done", "symbol", "type", "state",
        "volume_initial", "volume_current", "price_open", "sl", "tp",
        "price_current", "magic", "comment", "position_id", "reason",
    ]
    deal_fields = [
        "ticket", "order", "time", "time_msc", "type", "entry", "magic",
        "position_id", "symbol", "volume", "price", "commission", "fee",
        "swap", "profit", "comment", "reason",
    ]
    return {
        "orders": [{field: getattr(item, field, "") for field in order_fields} for item in orders],
        "deals": [{field: getattr(item, field, "") for field in deal_fields} for item in deals],
    }


def gates_to_dict(gates: DemoTradeGates) -> dict[str, Any]:
    return asdict(gates)
