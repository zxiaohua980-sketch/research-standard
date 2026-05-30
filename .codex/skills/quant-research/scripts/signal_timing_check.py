#!/usr/bin/env python
"""Read-only signal timing audit for quant-research."""

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
    p = argparse.ArgumentParser(description="Read-only audit for signal_time/entry_time and signal_bar_index/entry_bar_index ordering.")
    p.add_argument("--input", required=True, help="CSV file containing signal and entry timing columns.")
    p.add_argument("--output", help="Optional JSON output path. Inputs are never modified.")
    args = p.parse_args()

    path = Path(args.input)
    rows = read_csv(path)
    checks = []
    headers = {h.lower() for h in rows[0].keys()} if rows else set()

    if not rows:
        add(checks, "non_empty", "FAIL", "blocking", "Input CSV has no rows.")
    else:
        add(checks, "non_empty", "PASS", "info", "Input CSV has rows.", len(rows))

    missing = [c for c in ["signal_time", "entry_time"] if c not in headers]
    if missing:
        add(checks, "time_columns", "FAIL", "blocking", "Missing timing columns: " + ", ".join(missing))
    else:
        bad = 0
        unparsable = 0
        for row in rows:
            s = parse_time(get(row, "signal_time"))
            e = parse_time(get(row, "entry_time"))
            if s is None or e is None:
                unparsable += 1
            elif not s < e:
                bad += 1
        add(checks, "signal_before_entry_time", "FAIL" if bad else ("WARN" if unparsable else "PASS"),
            "blocking" if bad else "warning" if unparsable else "info",
            f"Rows with signal_time >= entry_time: {bad}; unparsable rows: {unparsable}.", bad)

    missing_idx = [c for c in ["signal_bar_index", "entry_bar_index"] if c not in headers]
    if missing_idx:
        add(checks, "bar_index_columns", "WARN", "warning", "Missing bar index columns: " + ", ".join(missing_idx))
    else:
        bad_idx = 0
        unparsable_idx = 0
        for row in rows:
            try:
                s = int(float(str(get(row, "signal_bar_index")).strip()))
                e = int(float(str(get(row, "entry_bar_index")).strip()))
            except (TypeError, ValueError):
                unparsable_idx += 1
                continue
            if not s < e:
                bad_idx += 1
        add(checks, "signal_before_entry_bar", "FAIL" if bad_idx else ("WARN" if unparsable_idx else "PASS"),
            "blocking" if bad_idx else "warning" if unparsable_idx else "info",
            f"Rows with signal_bar_index >= entry_bar_index: {bad_idx}; unparsable rows: {unparsable_idx}.", bad_idx)

    overall = "FAIL" if any(c["status"] == "FAIL" for c in checks) else "WARN" if any(c["status"] == "WARN" for c in checks) else "PASS"
    result = {
        "script_name": "signal_timing_check.py",
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
