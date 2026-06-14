#!/usr/bin/env python
"""Check MT5 runtime smoke-test logs for fatal/error evidence.

Use after launching the packaged EXE once from the operator folder or a smoke
copy of it. This script does not open MT5 and does not modify runtime state.
It only scans text logs and optionally writes a JSON report outside the
operator folder.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TEXT_LOG_SUFFIXES = {".log", ".txt", ".csv", ".json", ".jsonl", ".md"}
ERROR_NAME_PATTERNS = [
    re.compile(r"fatal", re.I),
    re.compile(r"error", re.I),
    re.compile(r"exception", re.I),
    re.compile(r"traceback", re.I),
]
ERROR_LINE_PATTERNS = [
    re.compile(r"Traceback \(most recent call last\)", re.I),
    re.compile(r"\bCRITICAL\b"),
    re.compile(r"\bFATAL\b"),
    re.compile(r"\bERROR\b"),
    re.compile(r"Unhandled exception", re.I),
    re.compile(r"RuntimeError", re.I),
    re.compile(r"Exception:", re.I),
    re.compile(r'"level"\s*:\s*"(?:error|critical|fatal)"', re.I),
    re.compile(r'"status"\s*:\s*"(?:error|failed|fatal)"', re.I),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def resolve_logs_dir(path: Path) -> Path:
    if path.name.lower() == "logs":
        return path
    return path / "logs"


def read_text(path: Path, max_bytes: int) -> str:
    data = path.read_bytes()[:max_bytes]
    return data.decode("utf-8", errors="ignore")


def scan_logs(logs_dir: Path, max_bytes_per_file: int = 2_000_000) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    files_scanned = 0
    non_empty_files = 0

    if not logs_dir.exists():
        return {
            "status": "FAIL",
            "logs_dir": str(logs_dir),
            "files_scanned": 0,
            "non_empty_files": 0,
            "findings": [{"file": str(logs_dir), "reason": "logs directory missing"}],
        }
    if not logs_dir.is_dir():
        return {
            "status": "FAIL",
            "logs_dir": str(logs_dir),
            "files_scanned": 0,
            "non_empty_files": 0,
            "findings": [{"file": str(logs_dir), "reason": "logs path is not a directory"}],
        }

    for path in sorted(item for item in logs_dir.rglob("*") if item.is_file()):
        files_scanned += 1
        size = path.stat().st_size
        if size > 0:
            non_empty_files += 1
        name_hit = any(pattern.search(path.name) for pattern in ERROR_NAME_PATTERNS)
        if name_hit and size > 0:
            findings.append(
                {
                    "file": str(path),
                    "reason": "non-empty error/fatal/exception-named log file",
                    "bytes": size,
                }
            )
            continue
        if path.suffix.lower() not in TEXT_LOG_SUFFIXES or size == 0:
            continue
        text = read_text(path, max_bytes_per_file)
        for lineno, line in enumerate(text.splitlines(), start=1):
            if any(pattern.search(line) for pattern in ERROR_LINE_PATTERNS):
                findings.append(
                    {
                        "file": str(path),
                        "line": lineno,
                        "reason": "error pattern in log line",
                        "text": line[:500],
                    }
                )
                break

    return {
        "status": "FAIL" if findings else "PASS",
        "logs_dir": str(logs_dir),
        "files_scanned": files_scanned,
        "non_empty_files": non_empty_files,
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="operator package folder or logs folder")
    parser.add_argument("--report", help="optional JSON report path outside the operator folder")
    parser.add_argument("--max-bytes-per-file", type=int, default=2_000_000)
    args = parser.parse_args()

    target = Path(args.path).resolve()
    logs_dir = resolve_logs_dir(target)
    result = scan_logs(logs_dir, max_bytes_per_file=args.max_bytes_per_file)
    result = {"checked_at_utc": utc_now(), **result}

    print(f"runtime log check: {result['status']}")
    print(f"logs_dir: {result['logs_dir']}")
    print(f"files_scanned: {result['files_scanned']}")
    print(f"non_empty_files: {result['non_empty_files']}")
    if result["findings"]:
        print("findings:")
        for finding in result["findings"]:
            print("- " + json.dumps(finding, ensure_ascii=False))

    if args.report:
        report_path = Path(args.report).resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"report: {report_path}")

    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
