"""
Reusable MT5 DEMO execution helper.

This module is for demo execution plumbing only. It does not generate strategy
signals, choose SL/TP rules, choose position size, or enable live trading.

Safety defaults:
- import has no side effects
- order methods require allow_demo_order=True
- REAL accounts are rejected
- each order_send is reconciled against account state
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional


TRADE_MODE_DEMO = 0
TRADE_MODE_REAL = 2


class MT5DemoTradeError(Exception):
    """Raised when a demo execution safety check or broker operation fails."""


@dataclass
class ExecutionResult:
    ok: bool
    action: str
    via: str
    retcode: Optional[int]
    comment: str
    order: Optional[int] = None
    deal: Optional[int] = None
    position_ticket: Optional[int] = None
    price: Optional[float] = None
    volume: Optional[float] = None


@dataclass
class PositionSnapshot:
    time: str
    ticket: int
    symbol: str
    side: str
    volume: float
    price_open: float
    price_current: float
    profit: float
    sl: float
    tp: float


class MT5DemoTradeClient:
    """Small demo-only wrapper around the MetaTrader5 Python package."""

    def __init__(
        self,
        *,
        magic: int,
        allow_demo_order: bool = False,
        max_positions: int = 1,
        deviation: int = 20,
        terminal_path: str = "",
        state_wait_seconds: float = 2.0,
        logger: Optional[Callable[[str], None]] = None,
    ):
        self.magic = int(magic)
        self.allow_demo_order = bool(allow_demo_order)
        self.max_positions = int(max_positions)
        self.deviation = int(deviation)
        self.terminal_path = terminal_path
        self.state_wait_seconds = float(state_wait_seconds)
        self.logger = logger or print
        self.mt5 = None
        self.account = None
        self.connected = False

    def log(self, msg: str):
        self.logger(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

    def connect(self):
        try:
            import MetaTrader5 as mt5
        except ImportError as exc:
            raise MT5DemoTradeError("MetaTrader5 package is not installed") from exc

        init_args = {}
        if self.terminal_path:
            init_args["path"] = self.terminal_path
        if not mt5.initialize(**init_args):
            raise MT5DemoTradeError(f"mt5.initialize() failed: {mt5.last_error()}")

        self.mt5 = mt5
        self.connected = True
        self.account = mt5.account_info()
        if self.account is None:
            self.disconnect()
            raise MT5DemoTradeError("account_info() returned None")

        if self.account.trade_mode == TRADE_MODE_REAL:
            self.disconnect()
            raise MT5DemoTradeError("LIVE ACCOUNT DETECTED. Demo helper aborted.")
        if self.account.trade_mode != TRADE_MODE_DEMO:
            self.disconnect()
            raise MT5DemoTradeError(f"Account is not DEMO trade_mode=0. Got {self.account.trade_mode}.")
        if not self.account.trade_allowed:
            self.disconnect()
            raise MT5DemoTradeError("trade_allowed=False on account")

        self.log(
            f"DEMO connected login={self.account.login} server={self.account.server} "
            f"balance={self.account.balance} {self.account.currency}"
        )
        return self

    def disconnect(self):
        if self.connected and self.mt5 is not None:
            self.mt5.shutdown()
        self.connected = False

    def reconnect(self):
        self.disconnect()
        time.sleep(self.state_wait_seconds)
        return self.connect()

    def _require_connected(self):
        if not self.connected or self.mt5 is None or self.account is None:
            raise MT5DemoTradeError("MT5DemoTradeClient is not connected")

    def _order_gate(self):
        self._require_connected()
        if not self.allow_demo_order:
            raise MT5DemoTradeError("allow_demo_order=False. Demo orders are blocked.")
        if self.account.trade_mode == TRADE_MODE_REAL:
            raise MT5DemoTradeError("LIVE ACCOUNT DETECTED. Demo orders are blocked.")
        if self.account.trade_mode != TRADE_MODE_DEMO:
            raise MT5DemoTradeError(f"Account is not DEMO trade_mode=0. Got {self.account.trade_mode}.")
        if not self.account.trade_allowed:
            raise MT5DemoTradeError("trade_allowed=False on account")

    def select_symbol(self, symbol: str):
        self._require_connected()
        if not self.mt5.symbol_select(symbol, True):
            raise MT5DemoTradeError(f"symbol_select({symbol}) failed: {self.mt5.last_error()}")
        info = self.mt5.symbol_info(symbol)
        if info is None:
            raise MT5DemoTradeError(f"symbol_info({symbol}) returned None")
        return info

    def tick(self, symbol: str):
        self._require_connected()
        tick = self.mt5.symbol_info_tick(symbol)
        if tick is None:
            raise MT5DemoTradeError(f"symbol_info_tick({symbol}) returned None: {self.mt5.last_error()}")
        return tick

    def normalize_volume(self, symbol: str, volume="auto_min") -> float:
        info = self.select_symbol(symbol)
        if volume == "auto_min":
            value = float(info.volume_min)
        else:
            value = float(volume)
        step = float(info.volume_step)
        value = round(value / step) * step
        return max(float(info.volume_min), min(float(info.volume_max), value))

    def positions_by_magic(self, symbol: Optional[str] = None):
        self._require_connected()
        positions = self.mt5.positions_get(symbol=symbol) if symbol else self.mt5.positions_get()
        return [p for p in positions if p.magic == self.magic] if positions else []

    def get_position(self, ticket: int):
        self._require_connected()
        positions = self.mt5.positions_get(ticket=ticket)
        if positions is None or len(positions) == 0:
            return None
        return positions[0]

    def snapshot_position(self, ticket: int) -> Optional[PositionSnapshot]:
        pos = self.get_position(ticket)
        if pos is None:
            return None
        side = "BUY" if pos.type == self.mt5.ORDER_TYPE_BUY else "SELL"
        return PositionSnapshot(
            time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ticket=int(pos.ticket),
            symbol=pos.symbol,
            side=side,
            volume=float(pos.volume),
            price_open=float(pos.price_open),
            price_current=float(pos.price_current),
            profit=float(pos.profit),
            sl=float(pos.sl),
            tp=float(pos.tp),
        )

    def _retcode_done(self, result) -> bool:
        if result is None:
            return False
        done = {self.mt5.TRADE_RETCODE_DONE}
        if hasattr(self.mt5, "TRADE_RETCODE_DONE_PARTIAL"):
            done.add(self.mt5.TRADE_RETCODE_DONE_PARTIAL)
        return result.retcode in done

    def _sltp_matches(self, ticket: int, sl: float, tp: float, digits: int) -> bool:
        pos = self.get_position(ticket)
        if pos is None:
            return False
        tol = 2 * (10 ** -digits)
        return abs(float(pos.sl) - float(sl)) <= tol and abs(float(pos.tp) - float(tp)) <= tol

    def order_send_confirmed(
        self,
        request: dict,
        *,
        action: str,
        confirm: Optional[str] = None,
        before_tickets=None,
        digits: int = 5,
    ) -> ExecutionResult:
        """Send once, then reconcile against account state."""
        self._order_gate()
        result = self.mt5.order_send(request)
        retcode = getattr(result, "retcode", None) if result is not None else None
        comment = getattr(result, "comment", str(self.mt5.last_error())) if result is not None else str(self.mt5.last_error())
        order = getattr(result, "order", None) if result is not None else None
        deal = getattr(result, "deal", None) if result is not None else None
        price = getattr(result, "price", None) if result is not None else None
        volume = getattr(result, "volume", None) if result is not None else None

        if self._retcode_done(result):
            return ExecutionResult(True, action, "retcode_done", retcode, comment, order, deal, order, price, volume)

        time.sleep(self.state_wait_seconds)
        if confirm == "open":
            before_tickets = before_tickets or set()
            symbol = request.get("symbol")
            new_positions = [p for p in self.positions_by_magic(symbol) if p.ticket not in before_tickets]
            if len(new_positions) == 1:
                pos = new_positions[0]
                return ExecutionResult(
                    True, action, "position_observed", retcode, comment,
                    order, deal, int(pos.ticket), float(pos.price_open), float(pos.volume)
                )

        if confirm == "sltp":
            ticket = int(request.get("position"))
            if self._sltp_matches(ticket, float(request.get("sl", 0)), float(request.get("tp", 0)), digits):
                return ExecutionResult(True, action, "sltp_observed", retcode, comment, order, deal, ticket, price, volume)

        if confirm == "close":
            ticket = int(request.get("position"))
            if self.get_position(ticket) is None:
                return ExecutionResult(True, action, "close_observed", retcode, comment, order, deal, ticket, price, volume)

        return ExecutionResult(False, action, "not_confirmed", retcode, comment, order, deal, None, price, volume)

    def _validate_sltp(self, side: str, price: float, sl: float, tp: Optional[float]):
        side = side.upper()
        if sl is None or float(sl) <= 0:
            raise MT5DemoTradeError("Initial SL is required and must be > 0")
        if side == "BUY":
            if float(sl) >= price:
                raise MT5DemoTradeError(f"BUY SL must be below entry price. price={price} sl={sl}")
            if tp not in (None, 0) and float(tp) <= price:
                raise MT5DemoTradeError(f"BUY TP must be above entry price. price={price} tp={tp}")
        elif side == "SELL":
            if float(sl) <= price:
                raise MT5DemoTradeError(f"SELL SL must be above entry price. price={price} sl={sl}")
            if tp not in (None, 0) and float(tp) >= price:
                raise MT5DemoTradeError(f"SELL TP must be below entry price. price={price} tp={tp}")
        else:
            raise MT5DemoTradeError("side must be BUY or SELL")

    def open_market(
        self,
        *,
        symbol: str,
        side: str,
        volume="auto_min",
        sl: float,
        tp: Optional[float] = None,
        comment: str = "demo_strategy",
    ) -> ExecutionResult:
        """Open a demo market position with strategy-supplied SL/TP."""
        self._order_gate()
        if len(self.positions_by_magic()) >= self.max_positions:
            raise MT5DemoTradeError(f"max_positions={self.max_positions} reached for magic={self.magic}")

        info = self.select_symbol(symbol)
        tick = self.tick(symbol)
        side = side.upper()
        price = float(tick.ask if side == "BUY" else tick.bid)
        self._validate_sltp(side, price, sl, tp)
        order_type = self.mt5.ORDER_TYPE_BUY if side == "BUY" else self.mt5.ORDER_TYPE_SELL
        digits = int(info.digits)
        vol = self.normalize_volume(symbol, volume)
        before_tickets = {p.ticket for p in self.positions_by_magic(symbol)}

        request = {
            "action": self.mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": vol,
            "type": order_type,
            "price": round(price, digits),
            "sl": round(float(sl), digits),
            "tp": round(float(tp or 0), digits),
            "deviation": self.deviation,
            "magic": self.magic,
            "comment": comment,
            "type_time": self.mt5.ORDER_TIME_GTC,
            "type_filling": self.mt5.ORDER_FILLING_IOC,
        }

        check = self.mt5.order_check(request)
        if check is None:
            raise MT5DemoTradeError(f"order_check returned None: {self.mt5.last_error()}")
        if check.retcode != 0:
            raise MT5DemoTradeError(f"order_check failed retcode={check.retcode} comment={check.comment}")

        result = self.order_send_confirmed(
            request, action="open_market", confirm="open",
            before_tickets=before_tickets, digits=digits
        )
        if not result.ok:
            raise MT5DemoTradeError(f"open not confirmed retcode={result.retcode} comment={result.comment}")
        self.log(f"OPEN {side} {symbol} ticket={result.position_ticket} via={result.via}")
        return result

    def modify_sltp(self, *, ticket: int, symbol: str, sl: float, tp: Optional[float] = None) -> ExecutionResult:
        self._order_gate()
        info = self.select_symbol(symbol)
        digits = int(info.digits)
        request = {
            "action": self.mt5.TRADE_ACTION_SLTP,
            "symbol": symbol,
            "position": int(ticket),
            "sl": round(float(sl), digits),
            "tp": round(float(tp or 0), digits),
        }
        result = self.order_send_confirmed(request, action="modify_sltp", confirm="sltp", digits=digits)
        if not result.ok:
            raise MT5DemoTradeError(f"SL/TP modify not confirmed retcode={result.retcode} comment={result.comment}")
        self.log(f"MODIFY SLTP ticket={ticket} via={result.via}")
        return result

    def poll_position(
        self,
        *,
        ticket: int,
        hold_seconds: float,
        interval_seconds: float = 60,
        on_snapshot: Optional[Callable[[PositionSnapshot], None]] = None,
    ):
        """Poll an open position. No orders are sent from this method."""
        self._require_connected()
        snapshots = []
        deadline = time.time() + float(hold_seconds)
        while time.time() < deadline:
            snap = self.snapshot_position(ticket)
            if snap is None:
                raise MT5DemoTradeError(f"position ticket={ticket} not found during polling")
            snapshots.append(snap)
            if on_snapshot:
                on_snapshot(snap)
            else:
                self.log(
                    f"HOLD ticket={snap.ticket} {snap.symbol} {snap.side} "
                    f"price={snap.price_current} profit={snap.profit} sl={snap.sl} tp={snap.tp}"
                )
            sleep_for = min(float(interval_seconds), max(0.0, deadline - time.time()))
            if sleep_for > 0:
                time.sleep(sleep_for)
        return snapshots

    def close_position(self, *, ticket: int, symbol: Optional[str] = None, comment: str = "demo_close") -> ExecutionResult:
        self._order_gate()
        pos = self.get_position(ticket)
        if pos is None:
            return ExecutionResult(True, "close_position", "already_closed", None, "position not found", position_ticket=ticket)

        symbol = symbol or pos.symbol
        tick = self.tick(symbol)
        close_type = self.mt5.ORDER_TYPE_SELL if pos.type == self.mt5.ORDER_TYPE_BUY else self.mt5.ORDER_TYPE_BUY
        price = tick.bid if close_type == self.mt5.ORDER_TYPE_SELL else tick.ask
        request = {
            "action": self.mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(pos.volume),
            "type": close_type,
            "position": int(ticket),
            "price": price,
            "deviation": self.deviation,
            "magic": self.magic,
            "comment": comment,
            "type_time": self.mt5.ORDER_TIME_GTC,
            "type_filling": self.mt5.ORDER_FILLING_IOC,
        }
        check = self.mt5.order_check(request)
        if check is None:
            raise MT5DemoTradeError(f"close order_check returned None: {self.mt5.last_error()}")
        if check.retcode != 0:
            self.log(f"close order_check warning retcode={check.retcode} comment={check.comment}")

        result = self.order_send_confirmed(request, action="close_position", confirm="close")
        if not result.ok:
            raise MT5DemoTradeError(f"close not confirmed retcode={result.retcode} comment={result.comment}")
        self.log(f"CLOSE ticket={ticket} via={result.via}")
        return result

    def close_all_magic(self, symbol: Optional[str] = None):
        self._order_gate()
        results = []
        for pos in list(self.positions_by_magic(symbol)):
            results.append(self.close_position(ticket=int(pos.ticket), symbol=pos.symbol, comment="demo_close_all_magic"))
        return results
