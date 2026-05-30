#!/usr/bin/env python
"""Read-only output integrity audit for quant-research."""

import argparse
import csv
import hashlib
import json
import re
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


def row_count(path):
    if path.suffix.lower() == ".csv":
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            return max(sum(1 for _ in f) - 1, 0)
    return len(path.read_text(encoding="utf-8", errors="ignore").splitlines())


def headers(path):
    if path.suffix.lower() != ".csv":
        return []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.excel
        reader = csv.reader(f, dialect=dialect)
        return next(reader, [])


def add(checks, cid, status, severity, message, count=0):
    checks.append({"id": cid, "status": status, "severity": severity, "message": message, "count": count})


def main():
    p = argparse.ArgumentParser(description="Read-only audit for non-empty reports/CSVs, hashes, row counts, timestamps, and key fields.")
    p.add_argument("--inputs", nargs="+", required=True, help="Report or CSV files to inspect.")
    p.add_argument("--required-field", action="append", default=[], help="Required text token or CSV column. May be repeated.")
    p.add_argument("--output", help="Optional JSON output path. Inputs are never modified.")
    args = p.parse_args()

    checks = []
    input_files = []
    for raw in args.inputs:
        path = Path(raw)
        if not path.exists():
            add(checks, "file_exists", "FAIL", "blocking", f"Missing file: {path}")
            input_files.append({"path": str(path), "hash": None, "row_count": 0})
            continue
        rc = row_count(path)
        input_files.append({"path": str(path), "hash": sha256_file(path), "row_count": rc})
        add(checks, f"non_empty:{path.name}", "PASS" if path.stat().st_size > 0 and rc >= 0 else "FAIL",
            "info" if path.stat().st_size > 0 else "blocking", f"File size bytes: {path.stat().st_size}; row_count: {rc}.", rc)
        text = path.read_text(encoding="utf-8", errors="ignore")
        has_hash = bool(re.search(r"(sha256|hash|commit|config_hash|data_hash)", text, flags=re.IGNORECASE))
        has_time = bool(re.search(r"(generated_at|timestamp|created_at|updated_at|\d{4}-\d{2}-\d{2})", text, flags=re.IGNORECASE))
        add(checks, f"metadata_hash:{path.name}", "PASS" if has_hash else "WARN", "info" if has_hash else "warning", "Hash/commit metadata found." if has_hash else "No hash/commit metadata token found.")
        add(checks, f"metadata_time:{path.name}", "PASS" if has_time else "WARN", "info" if has_time else "warning", "Timestamp metadata found." if has_time else "No timestamp metadata token found.")
        lower_headers = {h.lower() for h in headers(path)}
        lower_text = text.lower()
        for field in args.required_field:
            ok = field.lower() in lower_headers or field.lower() in lower_text
            add(checks, f"required_field:{path.name}:{field}", "PASS" if ok else "FAIL", "info" if ok else "blocking",
                f"Required field/token {field!r} present: {ok}.")

    overall = "FAIL" if any(c["status"] == "FAIL" for c in checks) else "WARN" if any(c["status"] == "WARN" for c in checks) else "PASS"
    result = {
        "script_name": "output_integrity_check.py",
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
