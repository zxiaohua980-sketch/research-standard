#!/usr/bin/env python
"""Read-only research data ledger guard for quant-research v1.2."""

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

VERSION = "1.0.0"

FINAL_ACTIONS = {"locked_final_evaluation", "final_oos", "freeze"}
SELECTION_ACTIONS = {"parameter_search", "logic_selection", "dev_validation", "trade_attribution", "event_study", "baseline_backtest"}


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


def find_dataset_blocks(text):
    blocks = []
    matches = list(re.finditer(r"dataset_id:\s*['\"]?([^'\"\n]+)['\"]?", text))
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        blocks.append((m.group(1).strip(), text[start:end]))
    return blocks


def field(block, name):
    m = re.search(rf"{re.escape(name)}:\s*(.+)", block)
    if not m:
        return ""
    value = m.group(1).split("#", 1)[0].strip().strip("'\"")
    return value


def bool_field(block, name):
    value = field(block, name).lower()
    return value in {"true", "yes", "1"}


def int_field(block, name):
    try:
        return int(field(block, name))
    except ValueError:
        return 0


def main():
    p = argparse.ArgumentParser(description="Read-only guard for machine-readable data ledger consumption and evidence-role conflicts.")
    p.add_argument("--ledger", required=True, help="Machine-readable research data ledger YAML/text file.")
    p.add_argument("--action", required=True, help="Requested research action, e.g. event_study, parameter_search, locked_final_evaluation, forward_live_collection.")
    p.add_argument("--dataset-id", action="append", default=[], help="Dataset id read by this action. May be repeated.")
    p.add_argument("--output", help="Optional JSON output path. Inputs are never modified.")
    args = p.parse_args()

    path = Path(args.ledger)
    checks = []
    if not path.exists():
        add(checks, "ledger_exists", "FAIL", "blocking", "Ledger file does not exist.")
        input_hash = None
        row_count = 0
        text = ""
    else:
        text = path.read_text(encoding="utf-8", errors="ignore")
        input_hash = sha256_file(path)
        row_count = len(text.splitlines())
        add(checks, "ledger_exists", "PASS", "info", "Ledger file exists.")

    required_tokens = ["dataset_id", "evidence_role", "usage_type", "research_stage", "consumed", "use_count"]
    for token in required_tokens:
        present = token in text
        add(checks, f"required_field:{token}", "PASS" if present else "FAIL", "info" if present else "blocking", f"Required ledger field {token} present: {present}.")

    blocks = dict(find_dataset_blocks(text))
    if not blocks and path.exists():
        add(checks, "dataset_entries", "FAIL", "blocking", "No dataset_id entries found.")
    else:
        add(checks, "dataset_entries", "PASS" if blocks else "FAIL", "info" if blocks else "blocking", f"Dataset entries found: {len(blocks)}.", len(blocks))
        blank_ids = sum(1 for dataset_id in blocks if not dataset_id)
        if blank_ids:
            add(checks, "blank_dataset_id", "WARN", "warning", f"Dataset entries with blank dataset_id: {blank_ids}.", blank_ids)

    selected = args.dataset_id or list(blocks.keys())
    for dataset_id in selected:
        block = blocks.get(dataset_id)
        if block is None:
            add(checks, f"dataset:{dataset_id}", "FAIL", "blocking", f"Requested dataset_id not found: {dataset_id}.")
            continue
        role = field(block, "evidence_role")
        consumed = bool_field(block, "consumed")
        use_count = int_field(block, "use_count")
        if role == "locked_final_holdout" and args.action in SELECTION_ACTIONS:
            add(checks, f"final_holdout_selection_use:{dataset_id}", "FAIL", "blocking", f"locked_final_holdout cannot be used for selection action {args.action}.")
        elif role == "locked_final_holdout" and use_count > 0 and args.action in FINAL_ACTIONS:
            add(checks, f"final_holdout_reuse:{dataset_id}", "FAIL", "blocking", f"locked_final_holdout already has use_count={use_count}.")
        elif role == "development_validation" and consumed and args.action in FINAL_ACTIONS:
            add(checks, f"consumed_dev_as_final:{dataset_id}", "FAIL", "blocking", "Consumed development_validation cannot be used as final evidence.")
        elif role == "forward_live" and "framework_start_time" not in text:
            add(checks, f"forward_framework_missing:{dataset_id}", "WARN", "warning", "forward_live role found but framework_start_time token is missing.")
        else:
            add(checks, f"dataset_allowed:{dataset_id}", "PASS", "info", f"Dataset {dataset_id} role={role}, consumed={consumed}, use_count={use_count} allowed for read-only guard.")

    overall = "FAIL" if any(c["status"] == "FAIL" for c in checks) else "WARN" if any(c["status"] == "WARN" for c in checks) else "PASS"
    result = {
        "script_name": "data_ledger_guard.py",
        "script_version": VERSION,
        "generated_at_utc": utc_now(),
        "read_only": True,
        "no_auto_fix": True,
        "no_parameter_optimization": True,
        "no_trading_advice": True,
        "requested_action": args.action,
        "input_files": [{"path": str(path), "hash": input_hash, "row_count": row_count}],
        "checks": checks,
        "overall_status": overall,
    }
    out = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(out + "\n", encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
