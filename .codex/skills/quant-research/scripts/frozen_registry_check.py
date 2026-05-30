#!/usr/bin/env python
"""Read-only frozen baseline registry guard for quant-research v1.2."""

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


def read(path):
    p = Path(path) if path else None
    if not p or not p.exists():
        return p, "", None, 0
    text = p.read_text(encoding="utf-8", errors="ignore")
    return p, text, sha256_file(p), len(text.splitlines())


def block_for(text, key, value):
    if not value:
        return ""
    m = re.search(rf"{re.escape(key)}:\s*['\"]?{re.escape(value)}['\"]?(.*?)(?:\n\s*-\s*[a-zA-Z0-9_]+:|\Z)", text, flags=re.S)
    return m.group(0) if m else ""


def has_field(block, name):
    return bool(re.search(rf"{re.escape(name)}:\s*(?!\s*$).+", block))


def list_field(block, name):
    m = re.search(rf"^\s*{re.escape(name)}:\s*\n((?:\s*-\s*.+\n?)*)", block, flags=re.M)
    if not m:
        return []
    values = []
    for line in m.group(1).splitlines():
        if "-" not in line:
            continue
        values.append(line.split("-", 1)[1].split("#", 1)[0].strip().strip("'\""))
    return values


def main():
    p = argparse.ArgumentParser(description="Read-only guard for frozen candidates and archived hypotheses registries.")
    p.add_argument("--strategy-registry", help="Central strategy_registry.yaml path.")
    p.add_argument("--frozen-candidates", required=True, help="frozen_candidates.yaml path.")
    p.add_argument("--archived-hypotheses", help="archived_hypotheses.yaml path.")
    p.add_argument("--strategy-id", required=True, help="Strategy id to check.")
    p.add_argument("--candidate-id", help="Frozen candidate id to check.")
    p.add_argument("--hypothesis-id", help="Hypothesis id to check against archive.")
    p.add_argument("--action", required=True, help="Requested action, e.g. modify_parameters, locked_final_evaluation, forward_live_collection.")
    p.add_argument("--output", help="Optional JSON output path. Inputs are never modified.")
    args = p.parse_args()

    checks = []
    input_files = []

    for label, raw in [("strategy_registry", args.strategy_registry), ("frozen_candidates", args.frozen_candidates), ("archived_hypotheses", args.archived_hypotheses)]:
        if not raw:
            continue
        path, text, h, rows = read(raw)
        input_files.append({"role": label, "path": str(path), "hash": h, "row_count": rows})
        add(checks, f"{label}_exists", "PASS" if h else ("WARN" if label == "archived_hypotheses" else "FAIL"),
            "info" if h else "warning" if label == "archived_hypotheses" else "blocking",
            f"{label} exists: {bool(h)}.")
        if label == "strategy_registry":
            add(checks, "strategy_in_central_registry", "PASS" if args.strategy_id in text else "FAIL",
                "info" if args.strategy_id in text else "blocking", f"strategy_id {args.strategy_id} in central registry: {args.strategy_id in text}.")
        elif label == "frozen_candidates" and h:
            candidate_block = block_for(text, "candidate_id", args.candidate_id) if args.candidate_id else block_for(text, "strategy_id", args.strategy_id)
            if not candidate_block:
                add(checks, "frozen_candidate_found", "FAIL", "blocking", "No matching frozen candidate found.")
            else:
                add(checks, "frozen_candidate_found", "PASS", "info", "Matching frozen candidate found.")
                for field in ["frozen_commit", "frozen_tag", "config_hash", "data_ledger_hash"]:
                    add(checks, f"frozen_field:{field}", "PASS" if has_field(candidate_block, field) else "FAIL",
                        "info" if has_field(candidate_block, field) else "blocking", f"Frozen field {field} present.")
                blocked_actions = set(list_field(candidate_block, "blocked_actions"))
                if args.action in blocked_actions:
                    add(checks, "requested_action_blocked", "FAIL", "blocking", f"Requested action {args.action} appears in blocked_actions.")
                else:
                    add(checks, "requested_action_not_blocked", "PASS", "info", f"Requested action {args.action} not found in blocked_actions.")
        elif label == "archived_hypotheses" and h and args.hypothesis_id:
            archived_block = block_for(text, "hypothesis_id", args.hypothesis_id)
            if archived_block:
                may_revisit = re.search(r"may_revisit:\s*true", archived_block, flags=re.I)
                add(checks, "hypothesis_archived", "WARN" if may_revisit else "FAIL",
                    "warning" if may_revisit else "blocking",
                    f"Hypothesis {args.hypothesis_id} is archived; may_revisit={bool(may_revisit)}.")
            else:
                add(checks, "hypothesis_not_archived", "PASS", "info", "Hypothesis not found in archived registry.")

    overall = "FAIL" if any(c["status"] == "FAIL" for c in checks) else "WARN" if any(c["status"] == "WARN" for c in checks) else "PASS"
    result = {
        "script_name": "frozen_registry_check.py",
        "script_version": VERSION,
        "generated_at_utc": utc_now(),
        "read_only": True,
        "no_auto_fix": True,
        "no_parameter_optimization": True,
        "no_trading_advice": True,
        "requested_action": args.action,
        "strategy_id": args.strategy_id,
        "candidate_id": args.candidate_id,
        "hypothesis_id": args.hypothesis_id,
        "input_files": input_files,
        "checks": checks,
        "overall_status": overall,
    }
    out = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(out + "\n", encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
