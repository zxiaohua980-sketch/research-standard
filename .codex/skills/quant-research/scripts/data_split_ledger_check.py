#!/usr/bin/env python
"""Read-only data usage ledger audit for quant-research."""

import argparse
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


def add(checks, cid, status, severity, message, count=0):
    checks.append({"id": cid, "status": status, "severity": severity, "message": message, "count": count})


def main():
    p = argparse.ArgumentParser(description="Read-only audit for data_usage_ledger split status and locked_final_holdout use.")
    p.add_argument("--ledger", required=True, help="Path to data_usage_ledger YAML/text file.")
    p.add_argument("--output", help="Optional JSON output path. Inputs are never modified.")
    args = p.parse_args()

    path = Path(args.ledger)
    checks = []
    if not path.exists():
        result = {
            "script_name": "data_split_ledger_check.py",
            "script_version": VERSION,
            "generated_at_utc": utc_now(),
            "read_only": True,
            "no_auto_fix": True,
            "no_parameter_optimization": True,
            "no_trading_advice": True,
            "input_files": [{"path": str(path), "hash": None, "row_count": 0}],
            "checks": [{"id": "ledger_exists", "status": "FAIL", "severity": "blocking", "message": "Ledger file does not exist.", "count": 0}],
            "overall_status": "FAIL",
        }
        text_out = json.dumps(result, indent=2, ensure_ascii=False)
        if args.output:
            Path(args.output).write_text(text_out + "\n", encoding="utf-8")
        print(text_out)
        return

    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()

    for required in ["discovery_train", "development_validation", "locked_final_holdout", "forward_live"]:
        add(checks, f"{required}_section", "PASS" if required in text else "FAIL",
            "info" if required in text else "blocking", f"Section {required} present: {required in text}.")

    use_counts = [int(x) for x in re.findall(r"use_count:\s*(\d+)", text)]
    final_block = ""
    m = re.search(r"locked_final_holdout:\s*(.*?)(?:\n\s{0,2}[a-zA-Z0-9_]+:|\Z)", text, flags=re.S)
    if m:
        final_block = m.group(1)
    final_opened = bool(re.search(r"opened_at:\s*(?!null\b|None\b|$).+", final_block))
    final_use = re.search(r"use_count:\s*(\d+)", final_block)
    final_use_count = int(final_use.group(1)) if final_use else 0
    if final_use_count > 1:
        add(checks, "locked_final_reuse", "FAIL", "blocking", f"locked_final_holdout use_count is {final_use_count}.", final_use_count)
    elif final_opened or final_use_count == 1:
        add(checks, "locked_final_opened", "WARN", "warning", "locked_final_holdout appears opened; ensure it was one final evaluation only.", final_use_count)
    else:
        add(checks, "locked_final_sealed", "PASS", "info", "locked_final_holdout appears sealed or unused.")

    if "consumed" in text and "development_validation" in text:
        add(checks, "development_consumption", "WARN", "warning", "Ledger mentions consumed development data; final reports must not call it clean OOS.")
    else:
        add(checks, "development_consumption", "PASS", "info", "No consumed development marker found.")

    overall = "FAIL" if any(c["status"] == "FAIL" for c in checks) else "WARN" if any(c["status"] == "WARN" for c in checks) else "PASS"
    result = {
        "script_name": "data_split_ledger_check.py",
        "script_version": VERSION,
        "generated_at_utc": utc_now(),
        "read_only": True,
        "no_auto_fix": True,
        "no_parameter_optimization": True,
        "no_trading_advice": True,
        "input_files": [{"path": str(path), "hash": sha256_file(path), "row_count": len(lines)}],
        "checks": checks,
        "overall_status": overall,
    }
    text_out = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text_out + "\n", encoding="utf-8")
    print(text_out)


if __name__ == "__main__":
    main()
