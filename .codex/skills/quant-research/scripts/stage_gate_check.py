#!/usr/bin/env python
"""Read-only research stage gate guard for quant-research v1.2."""

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

VERSION = "1.0.0"

DEFAULT_GATES = {
    "registration": {
        "allowed": {"register_strategy", "write_hypothesis", "init_ledger"},
        "blocked": {"backtest", "parameter_search", "locked_final_evaluation", "forward_live_collection"},
        "next_gate": "hypothesis_written",
    },
    "hypothesis": {
        "allowed": {"write_hypothesis", "init_ledger", "plan_event_study"},
        "blocked": {"parameter_search", "modify_sl_tp", "walk_forward", "locked_final_evaluation"},
        "next_gate": "event_study_ready",
    },
    "event_study": {
        "allowed": {"event_study", "mfe_mae_distribution", "counterfactual_analysis", "event_report"},
        "blocked": {"modify_sl_tp", "parameter_search", "walk_forward", "locked_final_evaluation", "claim_strategy_profitability"},
        "next_gate": "event_evidence_passed",
    },
    "execution_audit": {
        "allowed": {"execution_audit", "signal_timing_check", "lookahead_audit", "session_timezone_check"},
        "blocked": {"trust_backtest_metrics", "parameter_search", "locked_final_evaluation"},
        "next_gate": "audit_passed",
    },
    "baseline_backtest": {
        "allowed": {"fixed_rule_backtest", "output_integrity_check", "report_baseline"},
        "blocked": {"implicit_optimization", "parameter_search", "locked_final_evaluation"},
        "next_gate": "baseline_audited",
    },
    "trade_attribution": {
        "allowed": {"trade_attribution", "exit_attribution", "tail_dependency_check", "logic_change_proposal"},
        "blocked": {"implement_change_without_proposal", "parameter_search", "locked_final_evaluation"},
        "next_gate": "bounded_candidate_proposed",
    },
    "logic_refinement": {
        "allowed": {"implement_bounded_candidate", "re_audit_execution", "dev_validation"},
        "blocked": {"multi_change_rescue", "locked_final_evaluation", "forward_live_collection"},
        "next_gate": "candidate_accepted_on_dev",
    },
    "parameter_robustness": {
        "allowed": {"parameter_search", "parameter_plateau_check", "local_robustness_check"},
        "blocked": {"search_on_locked_final", "hide_candidate_results", "forward_live_collection"},
        "next_gate": "candidate_fixed",
    },
    "walk_forward_diagnostic": {
        "allowed": {"walk_forward", "robustness_diagnostic"},
        "blocked": {"use_locked_final_for_selection", "modify_candidate_from_final", "forward_live_collection"},
        "next_gate": "diagnostics_complete",
    },
    "regime_temporal_diagnostic": {
        "allowed": {"regime_diagnostic", "temporal_diagnostic"},
        "blocked": {"delete_bad_regime", "modify_candidate_from_final", "forward_live_collection"},
        "next_gate": "diagnostics_complete",
    },
    "locked_final_evaluation": {
        "allowed": {"locked_final_evaluation", "failure_report", "freeze_candidate_if_pass"},
        "blocked": {"parameter_search", "modify_rule_after_final", "reuse_locked_final"},
        "next_gate": "freeze_or_reject",
    },
    "frozen": {
        "allowed": {"integrity_check", "prepare_forward_live", "locked_final_report_if_unopened"},
        "blocked": {"modify_parameters", "add_filter", "change_sl_tp", "change_sizing", "historical_backfill"},
        "next_gate": "forward_live_start",
    },
    "forward_live": {
        "allowed": {"forward_live_collection", "append_new_signal", "append_new_trade", "gate_check", "log_intervention"},
        "blocked": {"historical_backfill", "modify_frozen_logic", "retune_from_early_losses", "merge_forward_to_frozen"},
        "next_gate": "gate_a_or_b",
    },
    "production": {
        "allowed": {"monitor_live", "risk_check", "incident_report"},
        "blocked": {"unlogged_rule_change", "unlogged_manual_override"},
        "next_gate": "production_review",
    },
    "archived": {
        "allowed": {"read_only_review", "new_hypothesis"},
        "blocked": {"reuse_as_active_without_new_stage", "retune_archived_result"},
        "next_gate": "new_registration_or_hypothesis",
    },
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


def simple_field(text, name):
    m = re.search(rf"^{re.escape(name)}:\s*['\"]?([^'\"\n#]+)", text, flags=re.M)
    return m.group(1).strip() if m else ""


def list_field(text, name):
    m = re.search(rf"^{re.escape(name)}:\s*\n((?:\s*-\s*.+\n?)*)", text, flags=re.M)
    if not m:
        return []
    return [line.split("-", 1)[1].strip().strip("'\"") for line in m.group(1).splitlines() if "-" in line]


def main():
    p = argparse.ArgumentParser(description="Read-only stage gate guard for allowed/blocked research actions.")
    p.add_argument("--state", required=True, help="research_stage_state.yaml path.")
    p.add_argument("--action", required=True, help="Requested action.")
    p.add_argument("--stage", help="Override current_stage from state file.")
    p.add_argument("--output", help="Optional JSON output path. Inputs are never modified.")
    args = p.parse_args()

    path = Path(args.state)
    checks = []
    if not path.exists():
        text = ""
        input_hash = None
        row_count = 0
        add(checks, "state_exists", "FAIL", "blocking", "Stage state file does not exist.")
    else:
        text = path.read_text(encoding="utf-8", errors="ignore")
        input_hash = sha256_file(path)
        row_count = len(text.splitlines())
        add(checks, "state_exists", "PASS", "info", "Stage state file exists.")

    stage = args.stage or simple_field(text, "current_stage")
    if not stage:
        add(checks, "current_stage_present", "FAIL", "blocking", "current_stage missing.")
        stage = "unknown"
    else:
        add(checks, "current_stage_present", "PASS", "info", f"current_stage={stage}.")

    gate = DEFAULT_GATES.get(stage)
    explicit_allowed = set(list_field(text, "allowed_actions"))
    explicit_blocked = set(list_field(text, "blocked_actions"))

    if gate is None:
        add(checks, "known_stage", "WARN", "warning", f"Unknown stage {stage}; falling back to explicit allowed/blocked lists only.")
        allowed = explicit_allowed
        blocked = explicit_blocked
        next_gate = simple_field(text, "next_gate") or "unknown"
    else:
        add(checks, "known_stage", "PASS", "info", f"Known stage {stage}.")
        allowed = set(gate["allowed"]) | explicit_allowed
        blocked = set(gate["blocked"]) | explicit_blocked
        next_gate = gate["next_gate"]

    if args.action in blocked:
        decision = "BLOCK"
        add(checks, "action_gate", "FAIL", "blocking", f"Action {args.action} is blocked at stage {stage}.")
    elif args.action in allowed:
        decision = "ALLOW"
        add(checks, "action_gate", "PASS", "info", f"Action {args.action} is allowed at stage {stage}.")
    else:
        decision = "WARN"
        add(checks, "action_gate", "WARN", "warning", f"Action {args.action} is not explicitly allowed at stage {stage}; require supervisor review.")

    overall = "FAIL" if any(c["status"] == "FAIL" for c in checks) else "WARN" if any(c["status"] == "WARN" for c in checks) else "PASS"
    result = {
        "script_name": "stage_gate_check.py",
        "script_version": VERSION,
        "generated_at_utc": utc_now(),
        "read_only": True,
        "no_auto_fix": True,
        "no_parameter_optimization": True,
        "no_trading_advice": True,
        "requested_action": args.action,
        "current_stage": stage,
        "gate_decision": decision,
        "next_gate": next_gate,
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
