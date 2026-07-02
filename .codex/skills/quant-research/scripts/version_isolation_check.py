#!/usr/bin/env python
"""Read-only check for one-version-one-folder isolation."""

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

VERSION = "1.0.0"
VERSION_RE = re.compile(r"versions[\\/](v[^\\/:\s\"']+)", re.I)
LOOSE_NAMES = re.compile(r"\b(latest|final|best|new|copy|saved_runs)\b", re.I)
ABS_PATH_RE = re.compile(r"[A-Za-z]:[\\/][^\s\"'<>|]+")
REL_VERSION_PATH_RE = re.compile(r'(?:\\.\\./|\\.\\.\\\\)+versions[\\/](v[^\\/\\s]+)', re.I)
MUTABLE_EXTS = {".py", ".yaml", ".yml", ".json", ".md", ".txt", ".csv", ".ini", ".ps1", ".bat", ".toml", ".cfg"}


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


def is_relative_to(path, root):
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def iter_scan_files(paths):
    for raw in paths:
        path = Path(raw)
        if path.is_file():
            yield path
        elif path.is_dir():
            for child in path.rglob("*"):
                if child.is_file() and (child.suffix.lower() in MUTABLE_EXTS or child.name.lower() in {"requirements.txt"}):
                    yield child


def main():
    p = argparse.ArgumentParser(description="Read-only audit for version-root isolation and cross-version references.")
    p.add_argument("--version-root", required=True, help="Active version root, for example strategy_root/versions/v0_2.")
    p.add_argument("--manifest", help="version_manifest.yaml to inspect.")
    p.add_argument("--artifacts", nargs="*", default=[], help="Outputs/reports that must live under version-root.")
    p.add_argument("--scan", nargs="*", default=[], help="Files or directories to scan for cross-version path references.")
    p.add_argument("--allowed-read-root", action="append", default=[], help="Extra immutable read roots allowed for input references.")
    p.add_argument("--strict", action="store_true", help="Treat loose output naming as blocking and enforce extra hardening checks.")
    p.add_argument("--output", help="Optional JSON output path.")
    args = p.parse_args()

    checks = []
    version_root = Path(args.version_root).resolve()
    current_version = version_root.name

    if not version_root.exists():
        add(checks, "version_root_exists", "FAIL", "blocking", f"Version root does not exist: {version_root}")
    else:
        add(checks, "version_root_exists", "PASS", "info", f"Version root exists: {version_root}")

    if version_root.parent.name.lower() != "versions":
        add(checks, "version_root_under_versions", "WARN", "warning", "Version root is not directly under a versions/ folder.", version_root)
    else:
        add(checks, "version_root_under_versions", "PASS", "info", "Version root is directly under versions/.", version_root)

    manifest_path = Path(args.manifest).resolve() if args.manifest else version_root / "version_manifest.yaml"
    if manifest_path.exists():
        text = manifest_path.read_text(encoding="utf-8", errors="ignore")
        required_tokens = ["strategy_id", "version", "version_root", "allowed_input_roots", "output_root"]
        missing = [token for token in required_tokens if token not in text]
        add(
            checks,
            "manifest_required_tokens",
            "FAIL" if missing else "PASS",
            "blocking" if missing else "info",
            "Missing manifest tokens: " + ", ".join(missing) if missing else "Manifest has required tokens.",
            manifest_path,
            len(missing),
        )
    else:
        add(checks, "manifest_exists", "FAIL", "blocking", f"Missing version manifest: {manifest_path}", manifest_path)

    for raw in args.artifacts:
        path = Path(raw).resolve()
        if not is_relative_to(path, version_root):
            add(checks, "artifact_under_version_root", "FAIL", "blocking", f"Artifact is outside active version root: {path}", path)
        else:
            add(checks, "artifact_under_version_root", "PASS", "info", f"Artifact is inside active version root: {path}", path)

    scan_roots = args.scan or [str(version_root)]
    scanned = 0
    cross_refs = 0
    loose_refs = 0
    abs_other_version_refs = 0
    for path in iter_scan_files(scan_roots):
        scanned += 1
        text = path.read_text(encoding="utf-8", errors="ignore")
        for match in VERSION_RE.finditer(text):
            referenced_version = match.group(1)
            if referenced_version != current_version:
                cross_refs += 1
                add(
                    checks,
                    "cross_version_reference",
                    "FAIL",
                    "blocking",
                    f"Reference to sibling version {referenced_version} while active version is {current_version}.",
                    path,
                )

        loose = LOOSE_NAMES.findall(text)
        if loose:
            loose_refs += len(loose)
            add(
                checks,
                "loose_output_name_reference",
                "FAIL" if args.strict else "WARN",
                "blocking" if args.strict else "warning",
                "Loose output naming token found; verify this is not a cross-version/shared output dependency.",
                path,
                len(loose),
            )

        # relative path variants that still reach sibling version folders (e.g. ../versions/vX/.. or ..\\versions\\vX\\..)
        for rel_path in REL_VERSION_PATH_RE.finditer(text):
            referenced_version = rel_path.group(1)
            if referenced_version != current_version:
                cross_refs += 1
                add(
                    checks,
                    "cross_version_reference_relative",
                    "FAIL",
                    "blocking",
                    f"Relative path references sibling version {referenced_version} while active version is {current_version}.",
                    path,
                )

        for raw_abs in ABS_PATH_RE.findall(text):
            normalized = raw_abs.replace("\\", "/")
            if "/versions/" in normalized.lower() and f"/versions/{current_version}/".lower() not in normalized.lower():
                abs_other_version_refs += 1
                add(
                    checks,
                    "absolute_other_version_path",
                    "FAIL",
                    "blocking",
                    f"Absolute path appears to reference another version: {raw_abs}",
                    path,
                )

    if args.strict and loose_refs > 0:
        add(
            checks,
            "strict_loose_naming_gate",
            "FAIL",
            "blocking",
            "Strict mode: loose naming tokens must be removed or moved to _trash_review and cannot remain in formal phase inputs/outputs.",
        )

    add(checks, "files_scanned", "INFO", "info", f"Scanned {scanned} files for version references.", count=scanned)
    if cross_refs == 0 and abs_other_version_refs == 0:
        add(checks, "no_cross_version_refs", "PASS", "info", "No sibling version references found.")

    overall = "FAIL" if any(c["status"] == "FAIL" for c in checks) else "WARN" if any(c["status"] == "WARN" for c in checks) else "PASS"
    result = {
        "script_name": "version_isolation_check.py",
        "script_version": VERSION,
        "generated_at_utc": utc_now(),
        "read_only": True,
        "no_auto_fix": True,
        "no_parameter_optimization": True,
        "no_trading_advice": True,
        "version_root": str(version_root),
        "current_version": current_version,
        "manifest": str(manifest_path),
        "checks": checks,
        "overall_status": overall,
    }
    text_out = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text_out + "\n", encoding="utf-8")
    print(text_out)


if __name__ == "__main__":
    main()


