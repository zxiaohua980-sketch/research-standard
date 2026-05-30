#!/usr/bin/env python
"""Read-only trade consistency audit for quant-research."""

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

VERSION = "1.0.0"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_csv(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.excel
        return list(csv.DictReader(f, dialect=dialect))


def get(row, *names):
    for name in names:
        for key, value in row.items():
            if key and key.lower() == name.lower():
                return value
    return None


def as_float(value):
    try:
        if value is None or str(value).strip() == "":
            return None
        return float(str(value).strip())
    except ValueError:
        return None


def add(checks, cid, status, severity, message, count=0):
    checks.append({"id": cid, "status": status, "severity": severity, "message": message, "count": count})


def main():
    p = argparse.ArgumentParser(description="Read-only audit for SL/TP direction, duplicate orders, conflicting positions, costs, open trades, and exit_reason.")
    p.add_argument("--input", required=True, help="CSV trade detail file.")
    p.add_argument("--output", help="Optional JSON output path. Inputs are never modified.")
    args = p.parse_args()

    path = Path(args.input)
    rows = read_csv(path)
    headers = {h.lower() for h in rows[0].keys()} if rows else set()
    checks = []

    if not rows:
        add(checks, "non_empty", "FAIL", "blocking", "Input CSV has no trade rows.")
    else:
        add(checks, "non_empty", "PASS", "info", "Input CSV has trade rows.", len(rows))

    id_col = next((c for c in ["trade_id", "order_id", "ticket"] if c in headers), None)
    if not id_col:
        add(checks, "trade_identifier", "WARN", "warning", "No trade_id/order_id/ticket column found.")
    else:
        seen = set()
        dup = 0
        for row in rows:
            v = str(get(row, id_col) or "").strip()
            if v in seen and v:
                dup += 1
            seen.add(v)
        add(checks, "duplicate_trade_ids", "FAIL" if dup else "PASS", "blocking" if dup else "info",
            f"Duplicate identifiers: {dup}.", dup)

    required_costs = ["spread", "commission", "slippage"]
    missing_costs = [c for c in required_costs if c not in headers]
    add(checks, "cost_columns", "WARN" if missing_costs else "PASS", "warning" if missing_costs else "info",
        "Missing cost columns: " + ", ".join(missing_costs) if missing_costs else "Required cost columns present.")

    missing_exit_reason = "exit_reason" not in headers
    if missing_exit_reason:
        add(checks, "exit_reason_column", "FAIL", "blocking", "Missing exit_reason column.")
    else:
        empty_exit = sum(1 for r in rows if not str(get(r, "exit_reason") or "").strip())
        open_like = sum(1 for r in rows if str(get(r, "exit_reason") or "").strip().lower() in {"open", "unclosed", "mtm", "mark_to_market"})
        add(checks, "exit_reason_values", "FAIL" if empty_exit else ("WARN" if open_like else "PASS"),
            "blocking" if empty_exit else "warning" if open_like else "info",
            f"Empty exit_reason rows: {empty_exit}; open/MTM rows: {open_like}.", empty_exit + open_like)

    direction_bad = 0
    direction_unknown = 0
    for row in rows:
        side = str(get(row, "side", "direction", "trade_type") or "").strip().lower()
        entry = as_float(get(row, "entry_price", "entry_fill_price"))
        sl = as_float(get(row, "initial_sl", "initial_stop_price", "sl"))
        tp = as_float(get(row, "initial_tp", "initial_target_price", "tp"))
        if side in {"buy", "long"} and entry is not None and sl is not None and tp is not None:
            if not (sl < entry < tp):
                direction_bad += 1
        elif side in {"sell", "short"} and entry is not None and sl is not None and tp is not None:
            if not (tp < entry < sl):
                direction_bad += 1
        else:
            direction_unknown += 1
    add(checks, "sl_tp_direction", "FAIL" if direction_bad else ("WARN" if direction_unknown else "PASS"),
        "blocking" if direction_bad else "warning" if direction_unknown else "info",
        f"Illegal SL/TP direction rows: {direction_bad}; incomplete rows: {direction_unknown}.", direction_bad)

    if {"entry_time", "exit_time", "symbol"}.issubset(headers):
        add(checks, "conflicting_positions_review", "WARN", "warning",
            "Overlapping-position logic is strategy-specific; manually review hedging/netting rules.", 0)
    else:
        add(checks, "conflicting_positions_review", "WARN", "warning",
            "Cannot review conflicting positions without symbol, entry_time, and exit_time.", 0)

    overall = "FAIL" if any(c["status"] == "FAIL" for c in checks) else "WARN" if any(c["status"] == "WARN" for c in checks) else "PASS"
    result = {
        "script_name": "trade_consistency_check.py",
        "script_version": VERSION,
        "generated_at_utc": utc_now(),
        "read_only": True,
        "no_auto_fix": True,
        "no_parameter_optimization": True,
        "no_trading_advice": True,
        "input_files": [{"path": str(path), "hash": sha256_file(path), "row_count": len(rows)}],
        "checks": checks,
        "overall_status": overall,
    }
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
