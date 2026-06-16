#!/usr/bin/env python
"""Audit an MT5 Python runtime package for portability and safety basics."""
from __future__ import annotations

import argparse
import re
from pathlib import Path


HARD_CODED_TERMINAL = re.compile(
    r"(?:AppData\\Roaming\\MetaQuotes\\Terminal\\|MetaQuotes\\Terminal\\)[A-Fa-f0-9]{12,}",
    re.IGNORECASE,
)
USER_PATH = re.compile(r"C:\\Users\\[^\\]+\\AppData\\Roaming\\MetaQuotes\\Terminal", re.IGNORECASE)
WINDOWS_ABSOLUTE_PATH = re.compile(r"^[A-Za-z]:[\\/]")
UNC_PATH = re.compile(r"^\\\\")
LOCAL_TEXT_PATH_PATTERNS = [
    re.compile(r"D:\\MT5(?:\\|$)", re.IGNORECASE),
    re.compile(r"C:\\Users\\[^\\]+", re.IGNORECASE),
    re.compile(r"AppData\\Roaming\\MetaQuotes\\Terminal", re.IGNORECASE),
    re.compile(r"MetaQuotes\\Terminal\\[A-Fa-f0-9]{12,}", re.IGNORECASE),
]
LOCAL_BINARY_PATH_NEEDLES = [
    "D:\\MT5",
    "C:\\Users\\",
    "AppData\\Roaming\\MetaQuotes\\Terminal",
    "MetaQuotes\\Terminal\\",
]
TEXT_SUFFIXES = {
    ".bat",
    ".cmd",
    ".csv",
    ".ini",
    ".json",
    ".jsonl",
    ".md",
    ".ps1",
    ".txt",
    ".yaml",
    ".yml",
}
PORTABLE_FORBIDDEN_SUFFIXES = {".bat", ".cmd", ".ps1", ".py", ".pyc", ".pyo", ".spec"}
PORTABLE_FORBIDDEN_NAMES = {"run_rebuild.bat", "run_verify.bat", "build_exe.bat"}
PORTABLE_FORBIDDEN_DIRS = {"build", "dist", "__pycache__"}


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        return ""


def result(rows, status, check, detail):
    rows.append((status, check, detail))


def contains_any(text: str, needles: list[str]) -> bool:
    lower = text.lower()
    return any(n.lower() in lower for n in needles)


def config_has_key(text: str, key: str) -> bool:
    return re.search(rf"^\s*{re.escape(key)}\s*=", text, re.I | re.M) is not None


def config_value(text: str, key: str) -> str | None:
    match = re.search(rf"^\s*{re.escape(key)}\s*=\s*(.*?)\s*$", text, re.I | re.M)
    if not match:
        return None
    return match.group(1).strip().strip('"').strip("'")


def has_exe_and_config(path: Path) -> bool:
    return path.is_dir() and (path / "config.ini").exists() and any(path.glob("*.exe"))


def find_portable_deliverables(root: Path) -> list[Path]:
    candidates: list[Path] = []
    if has_exe_and_config(root):
        candidates.append(root)
    portable_root = root / "portable"
    if portable_root.exists():
        if has_exe_and_config(portable_root):
            candidates.append(portable_root)
        for child in portable_root.iterdir():
            if has_exe_and_config(child):
                candidates.append(child)
    return sorted(set(path.resolve() for path in candidates), key=str)


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def find_post_package_smoke_reports(root: Path, portable_dirs: list[Path]) -> list[Path]:
    report_names = {
        "post_package_smoke_report.json",
        "post_package_log_check_report.json",
        "runtime_smoke_report.json",
        "portable_smoke_report.json",
        "smoke_log_check_report.json",
        "log_check_report.json",
    }
    reports: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.name.lower() not in report_names:
            continue
        if any(is_relative_to(path, portable_dir) for portable_dir in portable_dirs):
            continue
        reports.append(path)
    return sorted(reports, key=str)


def scan_text_for_local_paths(root: Path) -> list[str]:
    matches: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = read(path)
        for pattern in LOCAL_TEXT_PATH_PATTERNS:
            if pattern.search(text):
                matches.append(f"{path.relative_to(root)} matches {pattern.pattern}")
    return matches


def binary_needles() -> list[tuple[str, bytes]]:
    needles: list[tuple[str, bytes]] = []
    for item in LOCAL_BINARY_PATH_NEEDLES:
        for variant in {item, item.lower(), item.upper()}:
            needles.append((item, variant.encode("utf-8")))
            needles.append((item, variant.encode("utf-16le")))
    return needles


def scan_exes_for_local_path_bytes(root: Path) -> list[str]:
    matches: list[str] = []
    needles = binary_needles()
    for path in root.rglob("*.exe"):
        try:
            data = path.read_bytes()
        except OSError as exc:
            matches.append(f"{path.relative_to(root)} unreadable: {exc}")
            continue
        found = sorted({label for label, needle in needles if needle and needle in data})
        if found:
            matches.append(f"{path.relative_to(root)} contains {', '.join(found)}")
    return matches


def portable_artifact_hits(root: Path) -> list[str]:
    hits: list[str] = []
    for path in root.rglob("*"):
        name = path.name.lower()
        if path.is_dir() and name in PORTABLE_FORBIDDEN_DIRS:
            hits.append(str(path.relative_to(root)))
        elif path.is_file() and (
            path.suffix.lower() in PORTABLE_FORBIDDEN_SUFFIXES or name in PORTABLE_FORBIDDEN_NAMES
        ):
            hits.append(str(path.relative_to(root)))
    return hits


def portable_operator_shape(root: Path) -> tuple[bool, str]:
    details: list[str] = []
    exe_files = sorted(root.glob("*.exe"))
    if len(exe_files) != 1:
        details.append(f"expected exactly one top-level EXE, found {len(exe_files)}")
    if not (root / "config.ini").is_file():
        details.append("config.ini missing")

    logs = root / "logs"
    if not logs.is_dir():
        details.append("logs missing")
    else:
        log_entries = list(logs.iterdir())
        if log_entries:
            details.append(f"logs has {len(log_entries)} item(s)")

    config_text = read(root / "config.ini")
    data_cache_value = config_value(config_text, "data_cache_dir")
    data_cache = root / "data_cache"
    if data_cache_value:
        if not data_cache.is_dir():
            details.append("data_cache missing while config uses data_cache_dir")
        else:
            cache_entries = list(data_cache.iterdir())
            if cache_entries:
                details.append(f"data_cache has {len(cache_entries)} item(s)")
    elif data_cache.exists():
        cache_entries = list(data_cache.iterdir()) if data_cache.is_dir() else [data_cache]
        if cache_entries:
            details.append(f"data_cache present but not empty ({len(cache_entries)} item(s))")

    forbidden = portable_artifact_hits(root)
    if forbidden:
        details.append("forbidden operator artifacts: " + ", ".join(forbidden[:8]))

    allowed_top_level = {"config.ini", "logs", "data_cache"}
    allowed_top_level.update(path.name for path in exe_files)
    extras = [item.name for item in root.iterdir() if item.name not in allowed_top_level]
    if extras:
        details.append("unexpected top-level operator files/dirs: " + ", ".join(sorted(extras)[:8]))

    return not details, "; ".join(details) if details else "one EXE + config.ini + empty logs + optional empty data_cache"


def is_absolute_or_local_path(value: str) -> bool:
    stripped = value.strip().strip('"').strip("'")
    return (
        bool(WINDOWS_ABSOLUTE_PATH.search(stripped))
        or bool(UNC_PATH.search(stripped))
        or any(pattern.search(stripped) for pattern in LOCAL_TEXT_PATH_PATTERNS)
    )


def portable_config_path_problems(config_text: str) -> list[str]:
    problems: list[str] = []
    for key in ["log_dir", "tmp_dir", "cache_dir", "candidate_dir", "candidate_constituents_path"]:
        value = config_value(config_text, key)
        if value is None or value == "":
            problems.append(f"{key} missing/blank")
        elif is_absolute_or_local_path(value):
            problems.append(f"{key}={value}")
    terminal_path = config_value(config_text, "terminal_path")
    if terminal_path and is_absolute_or_local_path(terminal_path):
        problems.append(f"terminal_path={terminal_path}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit MT5 runtime package portability/safety.")
    parser.add_argument("runtime_dir", help="Runtime source directory, e.g. D:\\MT5\\MA\\v1.1_runtime")
    args = parser.parse_args()

    root = Path(args.runtime_dir).resolve()
    executor = root / "mt5_executor.py"
    build_bat = root / "build_exe.bat"
    config = root / "config.ini"
    dist = root / "dist"

    rows: list[tuple[str, str, str]] = []

    executor_text = read(executor)
    build_text = read(build_bat)
    config_text = read(config)

    result(rows, "PASS" if executor.exists() else "FAIL", "executor_exists", str(executor))
    result(rows, "PASS" if build_bat.exists() else "FAIL", "build_script_exists", str(build_bat))
    result(rows, "PASS" if config.exists() else "FAIL", "external_config_exists", str(config))

    combined_source = "\n".join([executor_text, build_text, config_text])
    hard = HARD_CODED_TERMINAL.findall(combined_source)
    user_paths = USER_PATH.findall(combined_source)
    if hard:
        result(rows, "FAIL", "no_hardcoded_terminal_hash", f"found {len(hard)} terminal-hash path reference(s)")
    elif user_paths:
        result(rows, "WARN", "no_user_specific_metaquotes_path", f"found {len(user_paths)} user AppData path reference(s)")
    else:
        result(rows, "PASS", "no_hardcoded_mt5_terminal_path", "no Terminal hash/user AppData path found")

    auto_path_markers = ["terminal_info", "data_path", "terminal_path"]
    result(
        rows,
        "PASS" if contains_any(executor_text + config_text, auto_path_markers) else "WARN",
        "mt5_path_auto_discovery_or_config",
        "expects terminal_info().data_path or external terminal_path",
    )

    result(
        rows,
        "PASS" if "RUNTIME_DIR" in executor_text and "_MEIPASS" in executor_text else "WARN",
        "pyinstaller_runtime_dir_pattern",
        "use RUNTIME_DIR for external state and _MEIPASS/BUNDLE_DIR for bundled files",
    )

    result(
        rows,
        "PASS" if "tmp" in executor_text.lower() and "RUNTIME_DIR" in executor_text else "WARN",
        "runtime_local_tmp",
        "generated temp files should go under exe/runtime dir",
    )

    allow_live_false = re.search(r"^\s*allow_live_trade\s*=\s*false\s*$", config_text, re.I | re.M) is not None
    result(rows, "PASS" if allow_live_false else "FAIL", "config_default_allow_live_trade_false", str(config))

    default_mode = (config_value(config_text, "mode") or "dry_run").lower()
    demo_default = default_mode == "demo_trade"
    if demo_default:
        demo_profile_checks = {
            "allow_demo_trade": "true",
            "dry_run_enforce": "false",
            "order_enabled": "true",
            "kill_switch": "false",
        }
        missing = [
            f"{key}={expected}"
            for key, expected in demo_profile_checks.items()
            if not re.search(rf"^\s*{re.escape(key)}\s*=\s*{expected}\s*$", config_text, re.I | re.M)
        ]
        result(
            rows,
            "PASS" if not missing else "FAIL",
            "config_default_demo_order_profile",
            "default demo_trade is explicitly enabled and DEMO-only" if not missing else "missing " + ", ".join(missing),
        )
    else:
        dry_profile_checks = {
            "allow_demo_trade": "false",
            "dry_run_enforce": "true",
            "order_enabled": "false",
        }
        missing = [
            f"{key}={expected}"
            for key, expected in dry_profile_checks.items()
            if not re.search(rf"^\s*{re.escape(key)}\s*=\s*{expected}\s*$", config_text, re.I | re.M)
        ]
        result(
            rows,
            "PASS" if not missing else "FAIL",
            "config_default_read_only_profile",
            "read-only scanner defaults are locked" if not missing else "missing " + ", ".join(missing),
        )

    runtime_smoke_keys = [
        "run_mt5_smoke_on_build",
        "expected_account_server",
        "expected_login",
        "print_account_magic_snapshot",
        "write_account_magic_snapshot",
        "require_trade_allowed_for_orders",
        "require_zero_magic_positions_before_smoke",
        "require_zero_magic_orders_before_smoke",
    ]
    missing_runtime_smoke = [key for key in runtime_smoke_keys if not config_has_key(config_text, key)]
    smoke_on_build = (config_value(config_text, "run_mt5_smoke_on_build") or "false").lower() == "true"
    result(
        rows,
        "PASS" if not smoke_on_build else "FAIL",
        "config_does_not_auto_smoke_mt5_on_build",
        "offline packaging must not open MT5 by default",
    )
    result(
        rows,
        "PASS" if not missing_runtime_smoke else "WARN",
        "runtime_smoke_config_visible",
        (
            "runtime smoke/account snapshot controls are config-visible"
            if not missing_runtime_smoke
            else "missing " + ", ".join(missing_runtime_smoke)
        ),
    )

    real_reject_markers = ["LIVE ACCOUNT", "TRADE_MODE_REAL", "trade_mode == 2", "trade_mode==2"]
    demo_only_markers = ["TRADE_MODE_DEMO", "trade_mode == 0", "trade_mode==0", "0=DEMO"]
    result(
        rows,
        "PASS" if contains_any(executor_text, real_reject_markers + demo_only_markers) else "FAIL",
        "real_account_rejected",
        "executor should hard reject REAL accounts or positively require DEMO/CONTEST mode",
    )
    can_send_orders = "order_send" in executor_text
    lower_executor = executor_text.lower()
    build_opens_mt5 = (
        "mt5.initialize" in build_text
        or "MetaTrader5" in build_text
        or "terminal64.exe" in build_text.lower()
        or "terminal.exe" in build_text.lower()
    )
    result(
        rows,
        "PASS" if not build_opens_mt5 else "FAIL",
        "offline_build_does_not_open_mt5",
        "build/static preflight must not initialize or open MT5",
    )
    result(
        rows,
        "PASS" if (
            not can_send_orders
            or (config_has_key(config_text, "magic_number") and "magic_number" in executor_text)
        ) else "WARN",
        "configurable_magic_number",
        "magic_number should be external config and unique per strategy/version/environment",
    )
    hardcoded_comment_requests = re.findall(r"""['"]comment['"]\s*:\s*['"]([^'"]+)['"]""", executor_text)
    comment_prefix_configured = config_has_key(config_text, "comment_prefix") and "comment_prefix" in executor_text
    result(
        rows,
        "PASS" if (not can_send_orders or (comment_prefix_configured and not hardcoded_comment_requests)) else "WARN",
        "configurable_comment_prefix",
        (
            "MT5 comment namespace should be external config, not hardcoded shared strings"
            if not hardcoded_comment_requests
            else f"found {len(hardcoded_comment_requests)} hardcoded order comment(s)"
        ),
    )
    identity_keys = ["strategy_id", "runtime_id", "environment_id"]
    result(
        rows,
        "PASS" if (
            not can_send_orders
            or all(config_has_key(config_text, key) for key in identity_keys)
        ) else "WARN",
        "strategy_runtime_identity_config",
        "config should identify strategy_id, runtime_id, and environment_id for audit isolation",
    )
    has_account_snapshot_path = (
        contains_any(
            executor_text,
            [
                "mt5_account_state_snapshot",
                "account_state_snapshot",
                "format_mt5_account_state_lines",
                "mt5_account_state_blockers",
            ],
        )
        or (
            "account_info" in executor_text
            and "terminal_info" in executor_text
            and "positions_get" in executor_text
            and "orders_get" in executor_text
            and "trade_allowed" in executor_text
        )
    )
    result(
        rows,
        "PASS" if (not can_send_orders or has_account_snapshot_path) else "FAIL",
        "runtime_account_magic_snapshot_path",
        "order-capable runtime should print/log account, trade_allowed, magic positions and magic pending orders when intentionally run",
    )
    cost_risk_keys = [
        "position_sizing_mode",
        "include_commission_in_risk",
        "commission_per_lot_round_turn_usd",
        "commission_free_symbols",
        "include_spread_in_risk",
        "spread_source",
        "fixed_spread_points_default",
        "include_slippage_in_risk",
        "slippage_points_entry",
        "slippage_points_exit",
        "volume_rounding",
        "max_risk_overshoot_pct",
    ]
    missing_cost_risk = [key for key in cost_risk_keys if not config_has_key(config_text, key)]
    cost_risk_markers = [
        "total_risk_cash_per_lot",
        "commission_per_lot_round_turn_usd",
        "include_spread_in_risk",
        "include_slippage_in_risk",
        "floor_to_step",
        "max_risk_overshoot_pct",
    ]
    result(
        rows,
        "PASS" if (
            not can_send_orders
            or (not missing_cost_risk and contains_any(executor_text + config_text, cost_risk_markers))
        ) else "FAIL",
        "cost_inclusive_position_sizing_config",
        (
            "position sizing config includes commission/spread/slippage risk denominator"
            if not missing_cost_risk
            else "missing " + ", ".join(missing_cost_risk)
        ),
    )
    spread_source = (config_value(config_text, "spread_source") or "").lower()
    spread_price_source = (config_value(config_text, "spread_price_source") or "").lower()
    fixed_spread_default = config_value(config_text, "fixed_spread_points_default")
    has_symbol_spread_override = re.search(r"^\s*spread_points_[A-Za-z0-9_.-]+\s*=", config_text, re.I | re.M) is not None
    valid_spread_sources = {"mt5_tick", "fixed_points", "symbol_override", "same_as_risk"}
    spread_source_config_ok = (
        spread_source in valid_spread_sources
        and (not spread_price_source or spread_price_source in valid_spread_sources)
        and (
            spread_source != "fixed_points"
            or bool((fixed_spread_default or "").strip())
            or has_symbol_spread_override
        )
    )
    mt5_tick_spread_markers = [
        "spread_price_from_tick",
        "symbol_info_tick",
        ".ask",
        ".bid",
        "ask - bid",
        "tick.ask - tick.bid",
    ]
    spread_source_code_ok = (
        not can_send_orders
        or spread_source != "mt5_tick"
        or contains_any(executor_text + config_text, mt5_tick_spread_markers)
    )
    result(
        rows,
        "PASS" if (not can_send_orders or (spread_source_config_ok and spread_source_code_ok)) else "FAIL",
        "explicit_spread_source_and_sign",
        (
            "spread source is explicit; mt5_tick means symbol_info_tick().ask - symbol_info_tick().bid; fixed spreads are config-keyed"
            if spread_source_config_ok and spread_source_code_ok
            else (
                "spread_source=mt5_tick needs symbol_info_tick bid/ask spread code"
                if spread_source_config_ok and not spread_source_code_ok
                else "missing/invalid spread_source, spread_price_source, or fixed_spread_points_default/symbol override"
            )
        ),
    )
    market_entry_keys = [
        "entry_execution_mode",
        "market_entry_price_policy",
        "market_entry_use_tick_side",
        "spread_adjust_market_entry",
        "spread_risk_accounting",
    ]
    missing_market_entry = [key for key in market_entry_keys if not config_has_key(config_text, key)]
    market_entry_markers = [
        "broker_tick_side_no_manual_spread",
        "market_entry_price_from_tick",
        "symbol_info_tick",
        ".ask",
        ".bid",
        "spread_adjust_market_entry",
        "actual_fill_no_extra_spread",
    ]
    manual_spread_entry_patterns = [
        r"raw_open\s*\+\s*spread",
        r"raw_entry\s*\+\s*spread",
        r"open_price\s*\+\s*spread",
        r"raw_open\s*-\s*spread",
        r"raw_entry\s*-\s*spread",
        r"open_price\s*-\s*spread",
    ]
    manual_market_spread_entry = any(re.search(pattern, lower_executor) for pattern in manual_spread_entry_patterns)
    result(
        rows,
        "PASS" if (
            not can_send_orders
            or (
                not missing_market_entry
                and contains_any(executor_text + config_text, market_entry_markers)
                and not manual_market_spread_entry
            )
        ) else "FAIL",
        "market_open_entry_no_manual_spread_adjustment",
        (
            "market/open entries use broker tick side and do not manually add spread to entry"
            if not missing_market_entry and not manual_market_spread_entry
            else (
                "manual raw_open/raw_entry/open_price +/- spread pattern found"
                if manual_market_spread_entry
                else "missing " + ", ".join(missing_market_entry)
            )
        ),
    )
    pending_price_keys = [
        "live_quote_source",
        "require_fresh_tick_before_order",
        "max_tick_age_ms",
        "pending_price_policy",
        "sltp_price_policy",
        "signal_price_basis",
        "spread_price_source",
        "adjust_buy_pending_entry_for_spread",
        "adjust_sell_pending_entry_for_spread",
        "adjust_buy_sltp_for_spread",
        "adjust_sell_sltp_for_spread",
        "reject_if_adjusted_sl_invalid",
    ]
    missing_pending_price = [key for key in pending_price_keys if not config_has_key(config_text, key)]
    pending_price_markers = [
        "raw_entry",
        "adjusted_entry",
        "adjusted_sl",
        "adjusted_tp",
        "broker_trigger_side",
        "broker_exit_trigger_side",
        "broker_bidask_from_bid_chart",
        "broker_bidask_exact",
        "live_quote_source",
        "symbol_info_tick",
        "buy_pending_entry",
        "sell_pending_entry",
        "sell_sltp",
        "reject_if_adjusted_sl_invalid",
    ]
    pending_policy = (config_value(config_text, "pending_price_policy") or "").lower()
    sltp_policy = (config_value(config_text, "sltp_price_policy") or "").lower()
    legacy_conservative_policy = pending_policy == "conservative_full_spread" or sltp_policy == "conservative_full_spread"
    result(
        rows,
        "PASS" if (
            not can_send_orders
            or (
                not missing_pending_price
                and contains_any(executor_text + config_text, pending_price_markers)
                and not legacy_conservative_policy
            )
        ) else "FAIL",
        "spread_aware_pending_price_policy",
        (
            "pending entry/SL/TP bid/ask policy is side-specific and auditable"
            if not missing_pending_price and not legacy_conservative_policy
            else (
                "conservative_full_spread is legacy/testing only, not default MT5 order policy"
                if legacy_conservative_policy
                else "missing " + ", ".join(missing_pending_price)
            )
        ),
    )
    pending_tick_keys = [
        "pending_monitor_mode",
        "tick_poll_interval_ms",
        "pending_too_close_policy",
        "market_if_pending_triggered",
        "pending_reprice_to_min_distance",
    ]
    missing_pending_tick = [key for key in pending_tick_keys if not config_has_key(config_text, key)]
    pending_tick_markers = [
        "trade_stops_level",
        "trade_freeze_level",
        "pending_entry_state_from_tick",
        "armed_trigger_watch",
        "market_if_pending_triggered",
        "tick_poll_interval_ms",
        "invalid_stops",
        "invalid price",
        "price_changed",
        "requote",
    ]
    result(
        rows,
        "PASS" if (
            not can_send_orders
            or (not missing_pending_tick and contains_any(executor_text + config_text, pending_tick_markers))
        ) else "FAIL",
        "pending_too_close_tick_monitor",
        (
            "pending too-close handling uses tick-level watch and market conversion when trigger side already crossed"
            if not missing_pending_tick and contains_any(executor_text + config_text, pending_tick_markers)
            else (
                "missing pending too-close/tick-level code markers"
                if not missing_pending_tick
                else "missing " + ", ".join(missing_pending_tick)
            )
        ),
    )
    duplicate_guard_keys = [
        "signal_execution_ledger_path",
        "signal_key_fields",
        "consume_signal_before_order_send",
        "block_duplicate_signal_bar",
    ]
    missing_duplicate_guard = [key for key in duplicate_guard_keys if not config_has_key(config_text, key)]
    result(
        rows,
        "PASS" if (not can_send_orders or not missing_duplicate_guard) else "FAIL",
        "duplicate_signal_bar_config",
        (
            "same completed signal bar duplicate-open guard is config-visible"
            if not missing_duplicate_guard
            else "missing " + ", ".join(missing_duplicate_guard)
        ),
    )
    result(
        rows,
        "PASS" if (
            "log_flush_each_line" in executor_text + config_text
            and "fsync" in executor_text
            and "executor_" in executor_text
        ) else "WARN",
        "immediate_runtime_log_append",
        "runtime log should append and flush/fsync lines instead of only buffering until exit",
    )
    result(
        rows,
        "PASS" if ("runtime_event_jsonl" in executor_text + config_text and ".jsonl" in executor_text + config_text) else "WARN",
        "runtime_event_jsonl",
        "structured runtime events should be written as JSONL for operator/audit review",
    )
    output_controls = {
        "market_data_cache_enabled": "true",
        "append_scan_outputs": "true",
        "write_timestamped_scan_files": "false",
        "write_full_trade_history": "false",
        "write_fail_reasons": "false",
        "keep_scan_tmp_files": "false",
        "append_mt5_history_jsonl": "false",
        "append_trade_lifecycle_jsonl": "false",
    }
    bad_output_controls = [
        f"{key}={expected}"
        for key, expected in output_controls.items()
        if not re.search(rf"^\s*{re.escape(key)}\s*=\s*{expected}\s*$", config_text, re.I | re.M)
    ]
    result(
        rows,
        "PASS" if not bad_output_controls else "WARN",
        "continuous_monitor_light_output_defaults",
        (
            "scan outputs append and bulk/temp/history logs are disabled by default"
            if not bad_output_controls
            else "review disk-growth defaults: " + ", ".join(bad_output_controls)
        ),
    )
    cache_refresh_present = re.search(r"^\s*cache_refresh_bars\s*=\s*\d+\s*$", config_text, re.I | re.M) is not None
    result(
        rows,
        "PASS" if cache_refresh_present else "WARN",
        "market_data_cache_refresh_configured",
        "cache_refresh_bars should bound each monitor-cycle MT5 download after initial seed",
    )
    result(
        rows,
        "PASS" if (
            "load_or_update_ohlc_cache" in executor_text
            and "incremental_tail_merge" in executor_text
            and "cache_refresh_bars" in executor_text
            and "normalize_ohlc_rows" in executor_text
        ) else "WARN",
        "market_data_cache_incremental_merge",
        "continuous monitor should merge recent closed bars into stable bounded OHLC cache files",
    )
    result(
        rows,
        "PASS" if (
            "data_cache_paths" in executor_text
            and "ZigZag_d" in executor_text
            and "write_zigzag_csv" in executor_text
        ) else "WARN",
        "zigzag_cache_stable_rewrite",
        "ZigZag should be recalculated into a stable cache file per parameter set, not appended blindly",
    )
    result(
        rows,
        "PASS" if (
            "append_csv_rows" in executor_text
            and "realtime_scan_summary_log.csv" in executor_text
            and "realtime_latest_signals_log.csv" in executor_text
        ) else "WARN",
        "scan_outputs_append_not_rewrite",
        "scan output should append to rolling logs instead of rewriting per-cycle files",
    )
    result(
        rows,
        "PASS" if (
            "cleanup_after_scan" in executor_text
            and "keep_scan_tmp_files" in executor_text
            and "shutil.rmtree" in executor_text
        ) else "WARN",
        "scan_tmp_cleanup_default",
        "per-scan OHLC/ZigZag temp folders should be deleted unless troubleshooting keeps them",
    )
    result(
        rows,
        "PASS" if (
            "latest_sink" in executor_text
            and "latest_rows" in executor_text
            and "execute_demo_orders_from_latest" in executor_text
        ) else "WARN",
        "demo_orders_use_in_memory_latest",
        "demo order execution should use current scan rows in memory, not depend on rewriting latest CSV",
    )
    result(
        rows,
        "PASS" if (not can_send_orders or "order_send_confirmed" in executor_text) else "WARN",
        "order_state_reconciliation",
        "check broker/account state after order_send",
    )
    result(
        rows,
        "PASS" if (not can_send_orders or "orders_get" in executor_text) else "WARN",
        "pending_order_scan",
        "startup/recovery should inspect pending orders with orders_get()",
    )
    result(
        rows,
        "PASS" if (not can_send_orders or "history_deals_get" in executor_text or "history_orders_get" in executor_text) else "WARN",
        "history_reconciliation",
        "startup/recovery should inspect recent order/deal history",
    )
    startup_markers = [
        "startup_reconcile",
        "reconcile_startup",
        "recover_intent",
        "reconcile_account",
        "sync_account_state",
    ]
    result(
        rows,
        "PASS" if (not can_send_orders or contains_any(executor_text, startup_markers)) else "WARN",
        "startup_reconciliation_before_signals",
        "reconcile positions/orders/history before processing new signals",
    )
    intent_markers = ["intent_id", "intent journal", "order_intent", "unresolved_intent"]
    has_intent_journal = contains_any(executor_text, intent_markers)
    result(
        rows,
        "PASS" if (not can_send_orders or has_intent_journal) else "WARN",
        "persistent_order_intent_journal",
        "persist local order intent before order_send",
    )
    atomic_markers = [
        "os.replace",
        "fsync",
        ".tmp",
        "sqlite3",
        "begin immediate",
        "commit()",
        "atomic_write",
    ]
    result(
        rows,
        "PASS" if (not can_send_orders or (has_intent_journal and contains_any(executor_text, atomic_markers))) else "WARN",
        "atomic_intent_persistence",
        "intent journal should use SQLite transaction or temp-file + fsync + os.replace()",
    )
    intent_merge_markers = [
        "latest.get(intent_id",
        "merged",
        "preserve",
        "value not in",
    ]
    result(
        rows,
        "PASS" if (
            not can_send_orders
            or not has_intent_journal
            or contains_any(executor_text, intent_merge_markers)
        ) else "WARN",
        "intent_updates_preserve_context",
        "append-only intent status updates should not erase original comment/theoretical SL/TP context",
    )
    intent_id_markers = ["uuid4", "uuid.uuid4", "time_ns", "milliseconds", "comment_id", "intent_id"]
    result(
        rows,
        "PASS" if (not can_send_orders or (has_intent_journal and contains_any(executor_text, intent_id_markers))) else "WARN",
        "unique_intent_id_generation",
        "intent_id should be collision-resistant; MT5 comment should carry only a short comment_id",
    )
    comment_limit_markers = ["comment_id", "truncate", "max_comment", "comment_limit"]
    result(
        rows,
        "PASS" if (
            not can_send_orders
            or ("comment" in lower_executor and contains_any(executor_text, comment_limit_markers))
        ) else "WARN",
        "mt5_comment_length_control",
        "comments should account for broker truncation limits while preserving a short intent id",
    )
    history_window_markers = [
        "recovery_lookback_days",
        "history_lookback_days",
        "lookback_days",
        "timedelta(days",
    ]
    result(
        rows,
        "PASS" if (not can_send_orders or contains_any(executor_text + config_text, history_window_markers)) else "WARN",
        "configured_history_window",
        "history_orders_get/history_deals_get should use configured recovery lookback",
    )
    history_future_buffer_markers = [
        "history_future_buffer_hours",
        "future_buffer_hours",
        "future_buffer",
    ]
    result(
        rows,
        "PASS" if (not can_send_orders or contains_any(executor_text + config_text, history_future_buffer_markers)) else "WARN",
        "broker_history_future_buffer",
        "history export should allow a configurable future buffer for broker/server clock offsets",
    )
    confirm_window_markers = [
        "order_confirm_timeout_seconds",
        "order_confirm_poll_interval_seconds",
        "confirm_timeout",
        "poll_interval",
    ]
    result(
        rows,
        "PASS" if (not can_send_orders or contains_any(executor_text + config_text, confirm_window_markers)) else "WARN",
        "configured_order_confirm_window",
        "post-send account-state polling window should be explicit, not a vague wait",
    )
    truth_markers = ["source of truth", "broker_state", "account_state", "mt5_state", "reconcile_account"]
    result(
        rows,
        "PASS" if (not can_send_orders or (contains_any(executor_text, truth_markers) and "positions_get" in executor_text)) else "WARN",
        "mt5_state_authoritative",
        "recovery should treat MT5 positions/orders/history as authoritative, not the local journal",
    )
    ticket_markers = ["position_ticket", ".ticket", "ticket"]
    identity_conflict_markers = ["magic mismatch", "symbol mismatch", "identity mismatch", "comment mismatch"]
    result(
        rows,
        "PASS" if (
            not can_send_orders
            or (contains_any(executor_text, ticket_markers) and contains_any(executor_text, identity_conflict_markers))
        ) else "WARN",
        "ticket_first_identity_validation",
        "match by ticket/order/deal id first; validate magic/symbol/comment conflicts",
    )
    sltp_tolerance_markers = ["tolerance", "trade_tick_size", "point * 2", "abs("]
    result(
        rows,
        "PASS" if (
            not can_send_orders
            or (contains_any(executor_text, sltp_tolerance_markers) and "sltp" in executor_text.lower())
        ) else "WARN",
        "sltp_tolerance_validation",
        "confirm SL/TP with point/tick tolerance, not exact float equality",
    )
    has_partial_close_semantics = (
        "partial" in lower_executor
        and ("close_scope" in lower_executor or "partial_close" in lower_executor)
        and ("requested_volume" in lower_executor or "previous_volume" in lower_executor)
    )
    result(
        rows,
        "PASS" if (not can_send_orders or has_partial_close_semantics) else "WARN",
        "partial_close_semantics",
        "close intents should distinguish full close from partial close",
    )
    has_disconnect_basics = (
        "initialize" in lower_executor
        and "last_error" in lower_executor
        and "terminal_info" in lower_executor
    )
    has_disconnect_policy = contains_any(
        executor_text,
        ["reconnect", "safe_mode", "safe mode", "unavailable", "backoff", "do not send"],
    )
    result(
        rows,
        "PASS" if (not can_send_orders or (has_disconnect_basics and has_disconnect_policy)) else "WARN",
        "mt5_disconnect_recovery_branch",
        "startup should distinguish MT5 unavailable/network-disconnected from process-crash recovery",
    )
    unknown_markers = ["unknown_requires_manual_review", "quarantine_state", "freeze_new_opens"]
    result(
        rows,
        "PASS" if (not can_send_orders or contains_any(executor_text, unknown_markers)) else "WARN",
        "unknown_state_policy",
        "unknown broker state should stop duplicate opens and require review",
    )
    lifecycle_markers = [
        "demo_trade_lifecycle",
        "actual_net_profit",
        "theoretical_entry_price",
        "actual_commission",
    ]
    result(
        rows,
        "PASS" if (not can_send_orders or contains_any(executor_text, lifecycle_markers)) else "WARN",
        "execution_lifecycle_export",
        "logs should join theoretical intent with actual MT5 deal profit/commission/net where possible",
    )
    signal_ledger_markers = [
        "signal_execution_ledger",
        "signal_execution_key",
        "last_closed_bar_time",
        "matched_signal_bar",
    ]
    signal_consumed_markers = [
        "send_attempted",
        "sent_confirmed_open",
        "sent_not_confirmed",
        "duplicate_signal",
        "already executed",
    ]
    result(
        rows,
        "PASS" if (
            not can_send_orders
            or (
                contains_any(executor_text + config_text, signal_ledger_markers)
                and contains_any(executor_text, signal_consumed_markers)
            )
        ) else "WARN",
        "signal_execution_ledger",
        "same completed signal bar should not reopen after same-candle close or runtime restart",
    )
    result(
        rows,
        "PASS" if (
            not can_send_orders
            or ("manually_resolved" in executor_text and "resolution_note" in executor_text)
        ) else "WARN",
        "quarantine_release_policy",
        "manual/broker-evidence release conditions should be explicit and auditable",
    )
    startup_report_markers = ["startup_report.csv", "startup_report", "manual_review_required.json"]
    result(
        rows,
        "PASS" if (not can_send_orders or contains_any(executor_text + config_text, startup_report_markers)) else "WARN",
        "startup_report_append",
        "startup reconciliation should append an operator report before signal scanning",
    )
    result(
        rows,
        "PASS" if "--onefile" in build_text and "--add-data" in build_text else "WARN",
        "pyinstaller_onefile_add_data",
        "build script should bundle runtime helper modules",
    )
    result(
        rows,
        "PASS" if "--add-binary" in build_text else "WARN",
        "native_dll_bundling",
        "conda/native DLLs often need explicit --add-binary",
    )
    result(
        rows,
        "PASS",
        "operator_docs_optional",
        "operator folder should stay minimal; docs/hash evidence should be outside it unless explicitly requested",
    )
    lower_build = build_text.lower()
    result(
        rows,
        "PASS" if ("portable_dir" in lower_build and "portable" in lower_build and "config_sha256" in lower_build) else "WARN",
        "build_creates_portable_deliverable",
        "build script should create a separate clean portable folder for the user to copy",
    )
    cleanup_blocking = (
        "could not be removed" in lower_build
        and "exit /b 1" in lower_build
        and "if exist build" in lower_build
        and "if exist dist" in lower_build
        and "if exist portable" in lower_build
    )
    result(
        rows,
        "PASS" if cleanup_blocking else "WARN",
        "build_cleanup_failure_is_blocking",
        "build script must fail instead of shipping after file-in-use/access-denied cleanup errors",
    )

    portable_dirs = find_portable_deliverables(root)
    result(
        rows,
        "PASS" if portable_dirs else "WARN",
        "portable_deliverable_exists",
        "; ".join(str(path) for path in portable_dirs) if portable_dirs else str(root / "portable"),
    )
    if portable_dirs:
        smoke_reports = find_post_package_smoke_reports(root, portable_dirs)
        result(
            rows,
            "PASS" if smoke_reports else "FAIL",
            "post_package_exe_smoke_log_check_evidence",
            (
                "; ".join(str(path.relative_to(root)) for path in smoke_reports[:5])
                if smoke_reports
                else "missing smoke/log-check report outside operator folder"
            ),
        )
        all_have_config = all((path / "config.ini").exists() for path in portable_dirs)
        all_have_exe = all(any(path.glob("*.exe")) for path in portable_dirs)
        result(
            rows,
            "PASS" if all_have_config and all_have_exe else "FAIL",
            "portable_has_exe_and_external_config",
            "each portable deliverable should contain an EXE plus external config.ini",
        )

        text_path_matches: list[str] = []
        exe_path_matches: list[str] = []
        artifact_hits: list[str] = []
        operator_shape_problems: list[str] = []
        config_path_problems: list[str] = []
        for path in portable_dirs:
            prefix = path.relative_to(root) if path != root else Path(".")
            text_path_matches.extend(f"{prefix}\\{item}" for item in scan_text_for_local_paths(path))
            exe_path_matches.extend(f"{prefix}\\{item}" for item in scan_exes_for_local_path_bytes(path))
            artifact_hits.extend(f"{prefix}\\{item}" for item in portable_artifact_hits(path))
            operator_ok, operator_detail = portable_operator_shape(path)
            if not operator_ok:
                operator_shape_problems.append(f"{prefix}: {operator_detail}")
            problems = portable_config_path_problems(read(path / "config.ini"))
            config_path_problems.extend(f"{prefix}: {item}" for item in problems)

        result(
            rows,
            "PASS" if not text_path_matches else "FAIL",
            "portable_no_local_text_paths",
            "no machine-specific paths in portable text files" if not text_path_matches else "; ".join(text_path_matches[:5]),
        )
        result(
            rows,
            "PASS" if not exe_path_matches else "FAIL",
            "portable_exe_no_local_path_bytes",
            "no machine-specific path bytes in portable EXE(s)" if not exe_path_matches else "; ".join(exe_path_matches[:5]),
        )
        result(
            rows,
            "PASS" if not artifact_hits else "FAIL",
            "portable_no_operator_forbidden_artifacts",
            "no BAT/CMD/PS1/source/build artifacts in operator folder" if not artifact_hits else "; ".join(artifact_hits[:8]),
        )
        result(
            rows,
            "PASS" if not operator_shape_problems else "FAIL",
            "portable_operator_minimal_shape",
            (
                "one EXE + config.ini + empty logs + optional empty data_cache"
                if not operator_shape_problems
                else "; ".join(operator_shape_problems)
            ),
        )
        result(
            rows,
            "PASS" if not config_path_problems else "FAIL",
            "portable_config_paths_relative",
            (
                "log_dir/tmp_dir/cache_dir/candidate paths are relative and terminal_path is not machine-specific"
                if not config_path_problems
                else "; ".join(config_path_problems[:8])
            ),
        )

    legacy_wrappers = [name for name in ["run_status.bat", "run_dry_run.bat", "run_demo.bat"] if (root / name).exists()]
    result(
        rows,
        "PASS",
        "legacy_bat_wrappers_optional",
        (
            "legacy wrappers present outside operator folder: " + ", ".join(legacy_wrappers)
            if legacy_wrappers
            else "no legacy BAT wrappers required"
        ),
    )

    if dist.exists():
        for name in [
            "config.ini",
            "run_status.bat",
            "run_dry_run.bat",
            "run_demo.bat",
            "PACKAGING_RUNTIME_EXE_GUIDE.md",
        ]:
            path = dist / name
            result(rows, "PASS" if path.exists() else "WARN", f"dist_{name}_exists", str(path))
    else:
        result(rows, "WARN", "dist_exists", str(dist))

    max_status = "PASS"
    for status, _, _ in rows:
        if status == "FAIL":
            max_status = "FAIL"
            break
        if status == "WARN":
            max_status = "WARN"

    print(f"MT5 runtime package audit: {max_status}")
    print(f"runtime_dir: {root}")
    print()
    print(f"{'status':<6} {'check':<42} detail")
    print("-" * 90)
    for status, check, detail in rows:
        print(f"{status:<6} {check:<42} {detail}")

    return 1 if max_status == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
