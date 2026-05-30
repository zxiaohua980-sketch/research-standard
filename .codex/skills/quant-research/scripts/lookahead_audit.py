#!/usr/bin/env python
"""Read-only lookahead risk audit for quant-research."""

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

VERSION = "1.0.0"
SUSPICIOUS_COLUMNS = [
    "future", "next_", "forward", "label", "outcome", "target_hit", "max_forward",
    "min_forward", "mfe", "mae", "zigzag", "swing_high", "swing_low", "pivot",
    "confirmed_high", "confirmed_low"
]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def add(checks, cid, status, severity, message, count=0):
    checks.append({"id": cid, "status": status, "severity": severity, "message": message, "count": count})


def read_headers(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample)
            reader = csv.reader(f, dialect=dialect)
            return next(reader, [])
        except Exception:
            return []


def count_csv_rows(path):
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            return max(sum(1 for _ in f) - 1, 0)
    except OSError:
        return 0


def main():
    p = argparse.ArgumentParser(description="Read-only audit for lookahead-prone column names, rolling/shift patterns, label leakage, and same-bar timing risk.")
    p.add_argument("--input", required=True, help="CSV, Python, or text file to inspect.")
    p.add_argument("--output", help="Optional JSON output path. Inputs are never modified.")
    args = p.parse_args()

    path = Path(args.input)
    text = path.read_text(encoding="utf-8", errors="ignore")
    headers = read_headers(path) if path.suffix.lower() in {".csv", ".tsv"} else []
    checks = []
    row_count = count_csv_rows(path) if headers else text.count("\n") + 1

    suspicious = [h for h in headers if any(token in h.lower() for token in SUSPICIOUS_COLUMNS)]
    if suspicious:
        add(checks, "suspicious_feature_or_label_columns", "WARN", "warning",
            "Columns may be labels or delayed confirmations: " + ", ".join(suspicious), len(suspicious))
    else:
        add(checks, "suspicious_feature_or_label_columns", "PASS", "info", "No obvious lookahead-prone column names found.")

    rolling_mentions = len(re.findall(r"\.rolling\s*\(|rolling_", text, flags=re.IGNORECASE))
    shift_mentions = len(re.findall(r"\.shift\s*\(|shift_", text, flags=re.IGNORECASE))
    if rolling_mentions and not shift_mentions:
        add(checks, "rolling_shift_review", "WARN", "warning", "Rolling logic found without an obvious shift pattern.", rolling_mentions)
    else:
        add(checks, "rolling_shift_review", "PASS", "info", f"Rolling mentions: {rolling_mentions}; shift mentions: {shift_mentions}.")

    current_bar_terms = len(re.findall(r"\b(current_|bar_)?(high|low|close)\b", text, flags=re.IGNORECASE))
    if current_bar_terms:
        add(checks, "current_bar_feature_review", "WARN", "warning", "High/low/close terms require timing review.", current_bar_terms)
    else:
        add(checks, "current_bar_feature_review", "PASS", "info", "No obvious high/low/close terms found.")

    same_bar_risk = 0
    if {"signal_bar_index", "entry_bar_index"}.issubset({h.lower() for h in headers}):
        same_bar_risk = 1
        add(checks, "same_bar_timing_review", "WARN", "warning", "Bar index columns present; run signal_timing_check.py for exact same-bar violations.")
    else:
        add(checks, "same_bar_timing_review", "INFO", "info", "No bar index pair found for same-bar timing review.")

    label_mentions = len(re.findall(r"\b(label|target|outcome|future)\b", text, flags=re.IGNORECASE))
    add(checks, "label_leakage_review", "WARN" if label_mentions else "PASS", "warning" if label_mentions else "info",
        f"Label/outcome token mentions: {label_mentions}.", label_mentions)

    overall = "FAIL" if any(c["status"] == "FAIL" for c in checks) else "WARN" if any(c["status"] == "WARN" for c in checks) else "PASS"
    result = {
        "script_name": "lookahead_audit.py",
        "script_version": VERSION,
        "generated_at_utc": utc_now(),
        "read_only": True,
        "no_auto_fix": True,
        "no_parameter_optimization": True,
        "no_trading_advice": True,
        "input_files": [{"path": str(path), "hash": sha256_file(path), "row_count": row_count}],
        "checks": checks,
        "overall_status": overall,
    }
    text_out = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text_out + "\n", encoding="utf-8")
    print(text_out)


if __name__ == "__main__":
    main()
