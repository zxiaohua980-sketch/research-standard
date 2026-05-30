#!/usr/bin/env python
"""Read-only session and timezone audit for quant-research."""

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


def parse_time(value):
    if value is None or str(value).strip() == "":
        return None
    text = str(value).strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def get(row, name):
    for key, value in row.items():
        if key and key.lower() == name.lower():
            return value
    return None


def add(checks, cid, status, severity, message, count=0):
    checks.append({"id": cid, "status": status, "severity": severity, "message": message, "count": count})


def main():
    p = argparse.ArgumentParser(description="Read-only audit for session labels, timezone fields, boundaries, DST/rollover risk, and cross-day sessions.")
    p.add_argument("--input", required=True, help="CSV file containing session/time columns.")
    p.add_argument("--time-column", default="signal_time", help="Timestamp column to inspect. Default: signal_time.")
    p.add_argument("--output", help="Optional JSON output path. Inputs are never modified.")
    args = p.parse_args()

    path = Path(args.input)
    rows = read_csv(path)
    headers = {h.lower() for h in rows[0].keys()} if rows else set()
    checks = []

    if not rows:
        add(checks, "non_empty", "FAIL", "blocking", "Input CSV has no rows.")
    else:
        add(checks, "non_empty", "PASS", "info", "Input CSV has rows.", len(rows))

    if "session" not in headers:
        add(checks, "session_column", "FAIL", "blocking", "Missing session column.")
    else:
        empty = sum(1 for r in rows if not str(get(r, "session") or "").strip())
        add(checks, "session_values", "FAIL" if empty else "PASS", "blocking" if empty else "info",
            f"Rows with empty session: {empty}.", empty)

    if "timezone" not in headers:
        add(checks, "timezone_column", "FAIL", "blocking", "Missing timezone column.")
    else:
        values = {str(get(r, "timezone") or "").strip() for r in rows}
        empty = "" in values
        mixed = len(values - {""}) > 1
        status = "FAIL" if empty else "WARN" if mixed else "PASS"
        add(checks, "timezone_values", status, "blocking" if empty else "warning" if mixed else "info",
            f"Timezone values observed: {sorted(values)}.")

    if args.time_column.lower() not in headers:
        add(checks, "time_column", "WARN", "warning", f"Missing time column: {args.time_column}.")
    else:
        boundary_hits = 0
        unparsable = 0
        cross_day_suspects = 0
        for row in rows:
            dt = parse_time(get(row, args.time_column))
            if dt is None:
                unparsable += 1
                continue
            if dt.minute == 0 and dt.hour in {0, 7, 8, 13, 14, 16, 17, 21, 22, 23}:
                boundary_hits += 1
            session = str(get(row, "session") or "").lower()
            if ("ny" in session or "new" in session or "us" in session) and dt.hour in {0, 1, 2, 3, 4, 5}:
                cross_day_suspects += 1
        add(checks, "session_boundary_review", "WARN" if boundary_hits else "PASS", "warning" if boundary_hits else "info",
            f"Rows on common session/rollover boundary hours: {boundary_hits}.", boundary_hits)
        add(checks, "cross_day_session_review", "WARN" if cross_day_suspects else "PASS", "warning" if cross_day_suspects else "info",
            f"Potential cross-day NY/session rows requiring manual review: {cross_day_suspects}.", cross_day_suspects)
        if unparsable:
            add(checks, "timestamp_parse", "WARN", "warning", f"Unparsable timestamp rows: {unparsable}.", unparsable)

    overall = "FAIL" if any(c["status"] == "FAIL" for c in checks) else "WARN" if any(c["status"] == "WARN" for c in checks) else "PASS"
    result = {
        "script_name": "session_timezone_check.py",
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
