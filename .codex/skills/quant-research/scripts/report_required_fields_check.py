#!/usr/bin/env python
"""Read-only required-field audit for quant research reports."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

VERSION = "1.0.0"

REQUIRED = {
    "hypothesis": ["hypothesis", "假说"],
    "data_scope": ["data scope", "data range", "数据范围"],
    "timezone": ["timezone", "时区"],
    "parameters": ["parameter", "fixed parameter", "参数"],
    "audit_status": ["audit status", "审计"],
    "conclusion_label": ["conclusion label", "decision_grade", "结论"],
    "profit_source": ["profit source", "收益来源", "attribution"],
    "limitations": ["limitation", "限制", "局限"],
}


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
    p = argparse.ArgumentParser(description="Read-only audit for required strategy report sections and fields.")
    p.add_argument("--input", required=True, help="Markdown report to inspect.")
    p.add_argument("--output", help="Optional JSON output path. Inputs are never modified.")
    args = p.parse_args()

    path = Path(args.input)
    text = path.read_text(encoding="utf-8", errors="ignore")
    lower = text.lower()
    checks = []

    if not text.strip():
        add(checks, "non_empty", "FAIL", "blocking", "Report is empty.")
    else:
        add(checks, "non_empty", "PASS", "info", "Report has content.", len(text.splitlines()))

    for field, tokens in REQUIRED.items():
        ok = any(token.lower() in lower for token in tokens)
        add(checks, f"required_report_field:{field}", "PASS" if ok else "FAIL", "info" if ok else "blocking",
            f"Required report field {field} present: {ok}.")

    forbidden = ["guaranteed profit", "risk-free", "sure win", "稳赚", "无风险"]
    found_forbidden = [x for x in forbidden if x.lower() in lower]
    add(checks, "forbidden_claims", "FAIL" if found_forbidden else "PASS", "blocking" if found_forbidden else "info",
        "Forbidden claims found: " + ", ".join(found_forbidden) if found_forbidden else "No forbidden profit claims found.", len(found_forbidden))

    overall = "FAIL" if any(c["status"] == "FAIL" for c in checks) else "WARN" if any(c["status"] == "WARN" for c in checks) else "PASS"
    result = {
        "script_name": "report_required_fields_check.py",
        "script_version": VERSION,
        "generated_at_utc": utc_now(),
        "read_only": True,
        "no_auto_fix": True,
        "no_parameter_optimization": True,
        "no_trading_advice": True,
        "input_files": [{"path": str(path), "hash": sha256_file(path), "row_count": len(text.splitlines())}],
        "checks": checks,
        "overall_status": overall,
    }
    text_out = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text_out + "\n", encoding="utf-8")
    print(text_out)


if __name__ == "__main__":
    main()
