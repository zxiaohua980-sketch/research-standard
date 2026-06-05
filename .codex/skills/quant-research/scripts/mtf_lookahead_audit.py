#!/usr/bin/env python
"""Read-only audit for multi-timeframe lookahead risk."""

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

VERSION = "1.0.0"

FAIL_PATTERNS = [
    ("negative_shift", r"\.shift\s*\(\s*-\d+|shift_\s*-\d+"),
    ("merge_asof_forward", r"merge_asof\s*\([^)]*direction\s*=\s*['\"]forward['\"]"),
    ("backfill", r"\.bfill\s*\(|fillna\s*\([^)]*method\s*=\s*['\"]bfill['\"]|backfill"),
    ("centered_rolling", r"rolling\s*\([^)]*center\s*=\s*True"),
]

WARN_PATTERNS = [
    ("merge_asof_nearest", r"merge_asof\s*\([^)]*direction\s*=\s*['\"]nearest['\"]"),
    ("raw_merge_asof", r"merge_asof\s*\("),
    ("resample", r"\.resample\s*\("),
    ("ffill", r"\.ffill\s*\(|fillna\s*\([^)]*method\s*=\s*['\"]ffill['\"]"),
    ("iloc_next", r"iloc\s*\[[^\]]*(i\s*\+\s*1|\+\s*1)"),
    ("future_tokens", r"\b(future|next_|target|label|outcome|max_forward|min_forward)\b"),
    ("zigzag_or_pivot", r"\b(zigzag|pivot|fractal|swing_high|swing_low|confirmed_high|confirmed_low)\b"),
]

MTF_HINTS = re.compile(r"\b(htf|higher_?timeframe|m30|h1|h4|d1|w1|multi_?timeframe|mtf)\b", re.I)
TIME_COLUMNS = {
    "decision": ["decision_time", "signal_time", "bar_close_time", "time"],
    "available": ["feature_available_at", "htf_available_at", "source_available_at", "available_at"],
    "source_close": ["source_close_time", "htf_close_time", "source_htf_bar_close_time"],
}


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def add(checks, cid, status, severity, message, path=None, count=0):
    checks.append({
        "id": cid,
        "status": status,
        "severity": severity,
        "message": message,
        "path": str(path) if path else None,
        "count": count,
    })


def read_text(path):
    return path.read_text(encoding="utf-8", errors="ignore")


def sniff_reader(path):
    f = open(path, "r", encoding="utf-8-sig", newline="")
    sample = f.read(8192)
    f.seek(0)
    try:
        dialect = csv.Sniffer().sniff(sample)
    except csv.Error:
        dialect = csv.excel
    return f, csv.DictReader(f, dialect=dialect)


def find_column(headers, candidates):
    by_lower = {h.lower(): h for h in headers}
    for candidate in candidates:
        if candidate in by_lower:
            return by_lower[candidate]
    return None


def parse_dt(value):
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    raw = raw.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y.%m.%d %H:%M:%S"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def audit_patterns(path, text, checks):
    for cid, pattern in FAIL_PATTERNS:
        matches = re.findall(pattern, text, flags=re.I | re.S)
        if matches:
            add(checks, f"static:{cid}", "FAIL", "blocking", f"Blocking MTF/lookahead-prone pattern found: {cid}.", path, len(matches))
    for cid, pattern in WARN_PATTERNS:
        matches = re.findall(pattern, text, flags=re.I | re.S)
        if matches:
            status = "WARN"
            severity = "warning"
            if cid == "raw_merge_asof" and re.search(r"available_at|direction\s*=\s*['\"]backward['\"]", text, flags=re.I):
                status = "INFO"
                severity = "info"
            add(checks, f"static:{cid}", status, severity, f"Review MTF timing pattern: {cid}.", path, len(matches))


def audit_csv(path, checks):
    f, reader = sniff_reader(path)
    with f:
        headers = reader.fieldnames or []
        lower_headers = [h.lower() for h in headers]
        has_mtf_hint = any(MTF_HINTS.search(h) for h in headers)
        decision_col = find_column(headers, TIME_COLUMNS["decision"])
        available_col = find_column(headers, TIME_COLUMNS["available"])
        source_close_col = find_column(headers, TIME_COLUMNS["source_close"])

        if has_mtf_hint and not (available_col or source_close_col):
            add(checks, "csv:missing_mtf_available_time", "FAIL", "blocking",
                "MTF-like columns found but no feature/source available time column exists.", path)

        if not decision_col:
            add(checks, "csv:missing_decision_time", "WARN", "warning",
                "No decision_time/signal_time/bar_close_time column found for timing assertions.", path)
            return

        failures = 0
        parsed_rows = 0
        checked_cols = [c for c in (available_col, source_close_col) if c]
        for row in reader:
            decision = parse_dt(row.get(decision_col))
            if not decision:
                continue
            for col in checked_cols:
                source_time = parse_dt(row.get(col))
                if not source_time:
                    continue
                parsed_rows += 1
                if source_time > decision:
                    failures += 1

        if checked_cols:
            add(checks, "csv:available_at_lte_decision_time", "FAIL" if failures else "PASS",
                "blocking" if failures else "info",
                f"Checked {parsed_rows} source/available timestamps against decision time; failures={failures}.",
                path, failures)
        elif has_mtf_hint:
            add(checks, "csv:no_assertable_mtf_timing_columns", "FAIL", "blocking",
                "MTF output cannot prove feature_available_at <= decision_time.", path)
        else:
            add(checks, "csv:no_mtf_timing_columns", "INFO", "info",
                "No MTF timing columns detected; static review still applies.", path)

        for suspicious in ("future", "target", "outcome", "label", "mfe", "mae"):
            hits = [h for h in lower_headers if suspicious in h]
            if hits:
                add(checks, f"csv:suspicious_column:{suspicious}", "WARN", "warning",
                    "Suspicious label/hindsight-style columns found: " + ", ".join(hits), path, len(hits))


def main():
    p = argparse.ArgumentParser(description="Read-only MTF lookahead audit for code, CSVs and reports.")
    p.add_argument("--inputs", nargs="+", required=True, help="Files to inspect.")
    p.add_argument("--output", help="Optional JSON output path.")
    args = p.parse_args()

    checks = []
    input_files = []
    for raw in args.inputs:
        path = Path(raw)
        if not path.exists():
            add(checks, "file_exists", "FAIL", "blocking", f"Missing file: {path}", path)
            input_files.append({"path": str(path), "hash": None})
            continue
        input_files.append({"path": str(path), "hash": sha256_file(path)})
        text = read_text(path)
        audit_patterns(path, text, checks)
        if path.suffix.lower() in {".csv", ".tsv"}:
            audit_csv(path, checks)

    if not checks:
        add(checks, "no_checks", "WARN", "warning", "No checks were produced.")

    overall = "FAIL" if any(c["status"] == "FAIL" for c in checks) else "WARN" if any(c["status"] == "WARN" for c in checks) else "PASS"
    result = {
        "script_name": "mtf_lookahead_audit.py",
        "script_version": VERSION,
        "generated_at_utc": utc_now(),
        "read_only": True,
        "no_auto_fix": True,
        "no_parameter_optimization": True,
        "no_trading_advice": True,
        "input_files": input_files,
        "checks": checks,
        "overall_status": overall,
    }
    text_out = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text_out + "\n", encoding="utf-8")
    print(text_out)


if __name__ == "__main__":
    main()
