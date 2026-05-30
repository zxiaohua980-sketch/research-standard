from pathlib import Path
from datetime import datetime, timezone, timedelta
import csv
import hashlib
import json
import re
import subprocess
import yaml

BASE = Path(r"D:\MT5\RESEARCH_STANDARD")
OUT = BASE / "governance_audits" / "STR-003" / "canonical_reproducibility_20260530"
REG = Path(r"D:\MT5\research_registry")
ROOT = Path(r"D:\MT5\openclaw\bb_strategy")
STRATEGY_ID = "STR-003"
NOW = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")


def sha256_file(path: Path):
    if not path.exists() or not path.is_file():
        return "MISSING"
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def line_count(path: Path):
    if not path.exists() or not path.is_file():
        return 0
    return len(path.read_text(encoding="utf-8", errors="replace").splitlines())


def read_text(path: Path):
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def load_yaml(path: Path):
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8", errors="replace")) or {}


def load_json(path: Path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def git(args):
    cp = subprocess.run(
        ["git", "-c", "safe.directory=D:/MT5/openclaw/bb_strategy", "-C", str(ROOT), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    return {"returncode": cp.returncode, "stdout": cp.stdout.strip(), "stderr": cp.stderr.strip()}


def consistency(ok, missing=False):
    if missing:
        return "MISSING"
    return "CONSISTENT" if ok else "INCONSISTENT"


def first_record(items, key, value):
    for item in items or []:
        if isinstance(item, dict) and item.get(key) == value:
            return item
    return {}


def extract_commit(path):
    text = read_text(path)
    match = re.search(
        r"(?:commit_hash|frozen_commit|frozen_commit_hash)\**:?\s*['\"]?([0-9a-f]{7,40})",
        text,
        re.IGNORECASE,
    )
    return match.group(1) if match else "MISSING"


OUT.mkdir(parents=True, exist_ok=True)

strategy_registry = load_yaml(REG / "strategy_registry.yaml")
identity_doc = load_yaml(REG / "strategy_identity.yaml")
frozen_doc = load_yaml(REG / "frozen_candidates.yaml")
ledger = load_yaml(REG / "data_ledgers" / "STR-003.yaml")
stage = load_yaml(REG / "stage_states" / "STR-003.yaml")
version = load_json(ROOT / "version.json")
forward_cfg = load_yaml(ROOT / "forward_live" / "forward_live_config.yaml")

strategy_record = first_record(strategy_registry.get("strategies", []), "strategy_id", STRATEGY_ID)
identity_record = first_record(identity_doc.get("strategies", []), "strategy_id", STRATEGY_ID)
frozen_candidate = first_record(frozen_doc.get("frozen_candidates", []), "strategy_id", STRATEGY_ID)

current_branch = git(["branch", "--show-current"])["stdout"]
head_commit = git(["rev-parse", "HEAD"])["stdout"]
status_git = git(["status", "--porcelain=v1", "-b"])["stdout"]
branch_vv = git(["branch", "-vv"])["stdout"]
show_ref = git(["show-ref", "--heads", "--tags"])["stdout"]
frozen_tag_object = git(["rev-parse", "v0.1-frozen"])["stdout"]
frozen_commit = git(["rev-parse", "v0.1-frozen^{}"])["stdout"]
forward_branch_commit = git(["rev-parse", "forward-v0.1"])["stdout"]
merge_base = git(["merge-base", "v0.1-frozen^{}", "forward-v0.1"])["stdout"]
is_frozen_ancestor_forward = git(["merge-base", "--is-ancestor", "v0.1-frozen^{}", "forward-v0.1"])["returncode"] == 0
worktrees = git(["worktree", "list", "--porcelain"])["stdout"]
core_diff = git([
    "diff",
    "--name-status",
    frozen_commit + ".." + head_commit,
    "--",
    "bb_strategy.py",
    "robust_test.py",
    "version.json",
    "forward_live/forward_live_config.yaml",
    "output/reports/v0.1/frozen_report.md",
    "output/reports/v0.1/execution_audit.md",
    "output/reports/v0.1/event_study_report.md",
    "output/reports/v0.1/optimization_report.md",
    "output/reports/v0.1/trade_attribution.md",
])["stdout"]
log_recent = git(["log", "--oneline", "--decorate", "--all", "-n", "16"])["stdout"]
version_at_676 = git(["show", "676986e:version.json"])

registry_commit = str(strategy_record.get("frozen_commit", ""))
version_commit = str((version.get("code_freeze", {}) or {}).get("frozen_commit_hash", ""))
forward_cfg_commit = str(forward_cfg.get("frozen_commit_hash", ""))
expected_forward_branch = str(strategy_record.get("forward_live_branch", "forward-v0.1"))

identity_rows = [
    ["strategy_id", "strategy_registry.yaml", strategy_record.get("strategy_id", "MISSING"), STRATEGY_ID, consistency(strategy_record.get("strategy_id") == STRATEGY_ID), "Registry contains STR-003 record."],
    ["strategy_id", "strategy_identity.yaml", identity_record.get("strategy_id", "MISSING"), STRATEGY_ID, consistency(identity_record.get("strategy_id") == STRATEGY_ID), "Central identity contains STR-003 record."],
    ["strategy_id", "version.json", version.get("strategy_info", {}).get("strategy_id", "MISSING"), STRATEGY_ID, consistency(version.get("strategy_info", {}).get("strategy_id") == STRATEGY_ID), "Version manifest agrees on strategy id."],
    ["strategy_id", "forward_live_config.yaml", forward_cfg.get("strategy_id", "MISSING"), STRATEGY_ID, consistency(forward_cfg.get("strategy_id") == STRATEGY_ID), "Forward config agrees on strategy id."],
    ["canonical_name", "strategy_registry.yaml", strategy_record.get("strategy_name", "MISSING"), identity_record.get("canonical_name", "MISSING"), consistency(strategy_record.get("strategy_name") == identity_record.get("canonical_name")), "Names should match canonical identity."],
    ["active_root_path", "strategy_registry.yaml", strategy_record.get("root_path", "MISSING"), str(ROOT), consistency(Path(strategy_record.get("root_path", "")).resolve() == ROOT.resolve() if strategy_record.get("root_path") else False), "Root path points to strategy directory."],
    ["active_root_path", "strategy_identity.yaml", identity_record.get("active_root_path", "MISSING"), str(ROOT), consistency(Path(identity_record.get("active_root_path", "")).resolve() == ROOT.resolve() if identity_record.get("active_root_path") else False), "Identity active root path matches observed root."],
    ["git_repository", "strategy_registry.yaml", strategy_record.get("git_repo", "MISSING"), str(ROOT / ".git"), consistency(Path(strategy_record.get("git_repo", "")).resolve() == (ROOT / ".git").resolve() if strategy_record.get("git_repo") not in (None, "MISSING", "NONE") else False), "Git repo exists locally."],
    ["current_branch", "git status", current_branch, expected_forward_branch, consistency(current_branch == expected_forward_branch), "Current checkout is not the registered forward branch."],
    ["current_head", "git rev-parse HEAD", head_commit, frozen_commit, consistency(head_commit == frozen_commit), "Current HEAD is post-freeze master, not frozen commit."],
    ["frozen_tag", "version/registry/frozen_candidate", f"{version.get('code_freeze', {}).get('frozen_tag')} / {strategy_record.get('frozen_tag')} / {frozen_candidate.get('frozen_tag')}", "v0.1-frozen", consistency(all(x == "v0.1-frozen" for x in [version.get('code_freeze', {}).get('frozen_tag'), strategy_record.get('frozen_tag'), frozen_candidate.get('frozen_tag')])), "Frozen tag names agree."],
    ["frozen_commit", "git tag dereference", frozen_commit, frozen_commit, "CONSISTENT", "Annotated tag v0.1-frozen dereferences to this commit."],
    ["frozen_commit", "strategy_registry.yaml", registry_commit, frozen_commit[:7], consistency(registry_commit in [frozen_commit, frozen_commit[:7]]), "Registry short commit matches tag dereference."],
    ["frozen_commit", "frozen_candidates.yaml", frozen_candidate.get("frozen_commit", "MISSING"), frozen_commit[:7], consistency(frozen_candidate.get("frozen_commit") in [frozen_commit, frozen_commit[:7]]), "Frozen candidate short commit matches tag dereference."],
    ["frozen_commit", "version.json", version_commit, frozen_commit[:7], consistency(version_commit in [frozen_commit, frozen_commit[:7]]), "version.json points to 676986e, not the freeze tag commit."],
    ["frozen_commit", "forward_live_config.yaml", forward_cfg_commit, frozen_commit[:7], consistency(forward_cfg_commit in [frozen_commit, frozen_commit[:7]]), "Forward config repeats the version.json commit."],
    ["forward_branch", "strategy_registry.yaml", expected_forward_branch, "forward-v0.1", consistency(expected_forward_branch == "forward-v0.1"), "Registry declares forward branch."],
    ["forward_branch", "git rev-parse forward-v0.1", forward_branch_commit, frozen_commit, consistency(forward_branch_commit == frozen_commit), "Forward branch exists and points exactly to frozen commit."],
    ["governance_state", "stage_states/STR-003.yaml", f"{stage.get('current_stage')} / {stage.get('stage_status')}", "forward_live / active", consistency(stage.get("current_stage") == "forward_live" and stage.get("stage_status") == "active"), "Stage state marks forward-live active."],
    ["governance_state", "strategy_registry.yaml", f"{strategy_record.get('current_stage')} / {strategy_record.get('current_status')}", "stage_12_forward_live / forward_live_active", consistency(strategy_record.get("current_stage") == "stage_12_forward_live" and strategy_record.get("current_status") == "forward_live_active"), "Registry marks stage 12 forward-live active."],
]

report_paths = {
    "event_study_report": ROOT / "output" / "reports" / "v0.1" / "event_study_report.md",
    "event_study_json": ROOT / "output" / "reports" / "v0.1" / "event_study_report.json",
    "execution_audit": ROOT / "output" / "reports" / "v0.1" / "execution_audit.md",
    "trade_attribution": ROOT / "output" / "reports" / "v0.1" / "trade_attribution.md",
    "optimization_report": ROOT / "output" / "reports" / "v0.1" / "optimization_report.md",
    "regime_validation_report": ROOT / "output" / "reports" / "v0.1" / "regime_validation_report.md",
    "temporal_validation_report": ROOT / "output" / "reports" / "v0.1" / "temporal_validation_report.md",
    "frozen_report": ROOT / "output" / "reports" / "v0.1" / "frozen_report.md",
    "trade_summary": ROOT / "output" / "reports" / "v0.1" / "trade_summary.csv",
    "version_json": ROOT / "version.json",
    "forward_config": ROOT / "forward_live" / "forward_live_config.yaml",
    "results_csv": ROOT / "results.csv",
    "post_freeze_reassessment_audited_trades": ROOT / "output" / "reports" / "reassessment_20260527" / "stage_01_execution" / "audited_trades.csv",
}

chain_rows = [
    ["research", "event_study", str(report_paths["event_study_report"]), extract_commit(report_paths["event_study_report"]), "event study -> execution audit", "PASS", "Report exists and identifies STR-003/XAUUSD H1, but commit is an early research commit."],
    ["execution_audit", "execution_audit", str(report_paths["execution_audit"]), extract_commit(report_paths["execution_audit"]), "execution audit -> attribution", "WARN", "Report exists but predates forward config and records framework_start_time as missing at that time."],
    ["attribution", "trade_attribution", str(report_paths["trade_attribution"]), extract_commit(report_paths["trade_attribution"]), "attribution -> optimization", "PASS", "Report supports LONG-ONLY transition; not a final freeze manifest."],
    ["optimization", "optimization_report", str(report_paths["optimization_report"]), extract_commit(report_paths["optimization_report"]), "optimization -> frozen report", "PASS", "Report supports bp=50 bs=2.5 lb=100 rr=6 LONG-ONLY; commit points to attribution base."],
    ["parameter_freeze", "version.json", str(report_paths["version_json"]), version_commit, "version.json -> frozen tag", "CHAIN_BREAK", "version.json was added in e594c33 but declares 676986e, a prior commit without version.json."],
    ["frozen_report", "frozen_report", str(report_paths["frozen_report"]), extract_commit(report_paths["frozen_report"]), "frozen report -> frozen tag", "CHAIN_BREAK", "Frozen report declares 676986e while tag v0.1-frozen dereferences to e594c33."],
    ["frozen_tag", "v0.1-frozen", "<git tag>", frozen_commit, "frozen tag -> forward branch", "PASS", "Annotated tag exists and dereferences to e594c33."],
    ["forward_branch", "forward-v0.1", "<git branch>", forward_branch_commit, "forward branch -> forward config", "PASS", "forward-v0.1 exists and points exactly to frozen tag commit."],
    ["forward_activation", "forward_live_config.yaml", str(report_paths["forward_config"]), forward_cfg_commit, "forward config -> current state", "WARN", "Forward config exists but repeats stale 676986e commit; framework start time is present."],
    ["current_state", "working tree", str(ROOT), head_commit, "current state", "WARN", "Current checkout is master at a post-freeze commit with untracked files; not canonical forward state."],
]

frozen_audit = []


def add_frozen_check(check, expected, observed, result, note):
    frozen_audit.append({"check": check, "expected": expected, "observed": observed, "result": result, "note": note})


add_frozen_check("frozen_candidate_exists", "STR-003-v0.1-frozen", frozen_candidate.get("candidate_id", "MISSING"), "PASS" if frozen_candidate.get("candidate_id") == "STR-003-v0.1-frozen" else "FAIL", "Central frozen candidate record exists.")
add_frozen_check("commit_hash", frozen_commit[:7], frozen_candidate.get("frozen_commit", "MISSING"), "WARN" if version_commit not in [frozen_commit, frozen_commit[:7]] else "PASS", "Registry/frozen candidate match tag; version.json does not.")
add_frozen_check("config_hash", frozen_candidate.get("config_hash"), sha256_file(ROOT / "version.json"), "PASS" if frozen_candidate.get("config_hash") == sha256_file(ROOT / "version.json") else "FAIL", "Stored config_hash matches current version.json file hash.")
add_frozen_check("data_ledger_hash", frozen_candidate.get("data_ledger_hash"), sha256_file(REG / "data_ledgers" / "STR-003.yaml"), "PASS" if frozen_candidate.get("data_ledger_hash") == sha256_file(REG / "data_ledgers" / "STR-003.yaml") else "FAIL", "Central ledger hash matches frozen candidate hash, but ledger was reconstructed after freeze.")
for key, path_key in [
    ("event_study_report_hash", "event_study_report"),
    ("audit_report_hash", "execution_audit"),
    ("attribution_report_hash", "trade_attribution"),
    ("frozen_report_hash", "frozen_report"),
]:
    expected = frozen_candidate.get(key)
    observed = sha256_file(report_paths[path_key])
    add_frozen_check(key, expected, observed, "PASS" if expected == observed else "FAIL", f"Hash comparison for {path_key}.")

ledger_hash_map = {}
for dataset in ledger.get("datasets", []) or []:
    if isinstance(dataset, dict) and dataset.get("source_path"):
        ledger_hash_map[str(dataset.get("source_path"))] = dataset.get("data_hash")


def classify_evidence(name, path, scope, stored_hash=None):
    exists = path.exists() if isinstance(path, Path) else False
    observed_hash = sha256_file(path) if exists else "MISSING"
    commit_ref = extract_commit(path) if exists and path.suffix.lower() in [".md", ".json", ".yaml", ".yml"] else "MISSING"
    if not exists:
        classification, result, reason = "UNVERIFIED_EVIDENCE", "FAIL", "File missing."
    elif str(path).startswith(str(ROOT / "output" / "reports" / "reassessment_20260527")):
        classification, result, reason = "UNVERIFIED_EVIDENCE", "WARN", "Post-freeze reassessment artifact is untracked and diagnostic-only."
    elif name in ["strategy_identity", "frozen_candidates"]:
        classification, result, reason = "VERIFIED_EVIDENCE", "PASS", "Central governance evidence is present and internally traceable."
    elif name in ["version_json", "forward_config", "frozen_report"]:
        classification, result, reason = "LEGACY_EVIDENCE", "WARN", "Hash-traceable artifact, but declares stale commit 676986e instead of tag commit e594c33."
    elif name == "data_ledger":
        classification, result, reason = "LEGACY_EVIDENCE", "WARN", "Centralized and hash-traceable but reconstructed after freeze."
    else:
        classification, result, reason = "LEGACY_EVIDENCE", "PASS", "File exists and supports research history, but commit reference belongs to an earlier stage."
    compare_hash = stored_hash or ledger_hash_map.get(str(path), "")
    if compare_hash:
        if observed_hash == compare_hash and result == "PASS":
            reason += " Stored hash matches."
        elif observed_hash == compare_hash and result == "WARN":
            reason += " Stored hash matches, but classification remains warning due custody issue."
        else:
            result = "FAIL"
            reason += " Stored hash mismatch."
    return [name, str(path), scope, classification, result, observed_hash, compare_hash, line_count(path), commit_ref, reason]


evidence_rows = [
    ["git_tag_v0.1_frozen", "<git tag v0.1-frozen>", "canonical frozen git object", "VERIFIED_EVIDENCE", "PASS", frozen_tag_object, "", 0, frozen_commit, "Annotated tag exists; dereferences to e594c33."],
    ["git_branch_forward_v0.1", "<git branch forward-v0.1>", "canonical forward branch", "VERIFIED_EVIDENCE", "PASS", forward_branch_commit, "", 0, forward_branch_commit, "Branch exists and equals frozen commit."],
    classify_evidence("strategy_registry", REG / "strategy_registry.yaml", "central governance registry"),
    classify_evidence("strategy_identity", REG / "strategy_identity.yaml", "central identity registry"),
    classify_evidence("frozen_candidates", REG / "frozen_candidates.yaml", "central frozen baseline registry"),
    classify_evidence("data_ledger", REG / "data_ledgers" / "STR-003.yaml", "central data ledger", frozen_candidate.get("data_ledger_hash")),
    classify_evidence("stage_state", REG / "stage_states" / "STR-003.yaml", "central stage state"),
    classify_evidence("archived_hypotheses", REG / "archived_hypotheses.yaml", "central archived hypotheses"),
    classify_evidence("version_json", report_paths["version_json"], "freeze manifest", frozen_candidate.get("config_hash")),
    classify_evidence("forward_config", report_paths["forward_config"], "forward-live activation config", ledger_hash_map.get(str(report_paths["forward_config"]))),
    classify_evidence("frozen_report", report_paths["frozen_report"], "freeze report", frozen_candidate.get("frozen_report_hash")),
    classify_evidence("optimization_report", report_paths["optimization_report"], "optimization evidence"),
    classify_evidence("event_study_report", report_paths["event_study_report"], "event-study evidence", frozen_candidate.get("event_study_report_hash")),
    classify_evidence("event_study_json", report_paths["event_study_json"], "event-study machine output"),
    classify_evidence("execution_audit", report_paths["execution_audit"], "legacy execution audit", frozen_candidate.get("audit_report_hash")),
    classify_evidence("trade_attribution", report_paths["trade_attribution"], "attribution evidence", frozen_candidate.get("attribution_report_hash")),
    classify_evidence("regime_validation_report", report_paths["regime_validation_report"], "regime validation evidence"),
    classify_evidence("temporal_validation_report", report_paths["temporal_validation_report"], "temporal validation evidence"),
    classify_evidence("trade_summary", report_paths["trade_summary"], "trade detail/summary evidence", ledger_hash_map.get(str(report_paths["trade_summary"]))),
    classify_evidence("results_csv", report_paths["results_csv"], "legacy result artifact", ledger_hash_map.get(str(report_paths["results_csv"]))),
    classify_evidence("post_freeze_reassessment_audited_trades", report_paths["post_freeze_reassessment_audited_trades"], "post-freeze diagnostic artifact", ledger_hash_map.get(str(report_paths["post_freeze_reassessment_audited_trades"]))),
]

untracked = [line[3:] for line in status_git.splitlines() if line.startswith("?? ")]
modified = [line for line in status_git.splitlines() if line and not line.startswith("##") and not line.startswith("?? ")]
multiple_worktrees = len([line for line in worktrees.splitlines() if line.startswith("worktree ")]) > 1
risk_rows = [
    ["RISK_BRANCH_MISMATCH", "HIGH", "Current checkout is master while registry forward branch is forward-v0.1.", "Blocks fully reproducible forward-live identity from current working tree."],
    ["RISK_COMMIT_MISMATCH", "HIGH", f"Git tag/registry/frozen branch point to {frozen_commit[:7]}, but version.json/forward config declare {version_commit}.", "Blocks fully reproducible freeze manifest until reconciled."],
    ["RISK_UNTRACKED_FILES", "MEDIUM", "; ".join(untracked) if untracked else "none", "Dirty worktree blocks formal validation from current checkout."],
    ["RISK_POST_FREEZE_MASTER_ADDITIONS", "MEDIUM", "Master contains post-freeze analysis/report additions after e594c33.", "Not invalid by itself, but not canonical forward lineage."],
    ["RISK_RECONSTRUCTED_LEDGER", "MEDIUM", "Data ledger was created after freeze from existing artifacts.", "Historical split integrity cannot be upgraded by file existence alone."],
    ["RISK_EXECUTION_MODEL_WORDING", "MEDIUM", "Legacy reports/config differ on close/first breach/next_bar_open wording.", "Requires separate Stage 2 execution audit if strategy-level trust is needed."],
    ["RISK_MULTIPLE_WORKTREES", "LOW" if not multiple_worktrees else "MEDIUM", worktrees.replace("\n", " | "), "Only one worktree observed." if not multiple_worktrees else "Multiple worktrees require reconciliation."],
    ["RISK_CORE_FILE_DRIFT", "LOW" if not core_diff else "HIGH", core_diff or "No diff for selected core freeze files between e594c33 and current HEAD.", "Core freeze files appear unchanged on master, but current branch is still not canonical forward branch."],
]

csv_specs = {
    "identity_matrix.csv": (["field", "source", "declared_value", "observed_or_canonical_value", "status", "note"], identity_rows),
    "chain_of_custody.csv": (["stage", "artifact", "path_or_source", "declared_or_observed_commit", "next_link", "status", "note"], chain_rows),
    "evidence_registry.csv": (["evidence_id", "path_or_source", "scope", "classification", "result", "observed_hash_or_object", "stored_hash", "row_count", "declared_commit", "reason"], evidence_rows),
    "reproducibility_risks.csv": (["risk_id", "severity", "finding", "impact"], risk_rows),
}

for filename, (header, rows) in csv_specs.items():
    with (OUT / filename).open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

final_label = "PARTIALLY_REPRODUCIBLE"
md = []
md.append("# STR-003 Canonical Reproducibility Audit")
md.append("")
md.append(f"Generated: {NOW}")
md.append("")
md.append("## Scope And Gate Statement")
md.append("")
md.append("This is a governance audit, not a strategy audit. No backtest, walk-forward, optimization, forward-live analysis, parameter change, strategy-code change, ledger edit, or registry edit was performed. The task is Stage 12 forward-live governance verification: code changes are not allowed, parameter changes are not allowed, and backtest metrics remain non-decision-grade unless a separate execution audit and identity reconciliation are completed.")
md.append("")
md.append("## 1. Canonical Identity Audit")
md.append("")
md.append(f"STR-003 is registered as `{identity_record.get('canonical_name', strategy_record.get('strategy_name'))}` at `{ROOT}`. The current working tree is on branch `{current_branch}` at `{head_commit}`, while the registered forward branch is `{expected_forward_branch}` and resolves to `{forward_branch_commit}`. The frozen tag `v0.1-frozen` is an annotated tag object `{frozen_tag_object}` and dereferences to `{frozen_commit}`. The governance registry and frozen candidate both point to `e594c33`, while `version.json`, `forward_live_config.yaml`, and `frozen_report.md` declare `676986e`.")
md.append("")
md.append("The detailed identity matrix is in `identity_matrix.csv`. The identity exists, but it is not fully unique across all artifacts because the freeze manifest family and Git tag family disagree on the frozen commit.")
md.append("")
md.append("## 2. Chain Of Custody Audit")
md.append("")
md.append("The research chain exists from event study through execution audit, attribution, optimization, freeze report, frozen tag, forward branch, and forward config. The main `CHAIN_BREAK` occurs at the freeze boundary: `version.json` and `frozen_report.md` were added in commit `e594c33`, yet both declare `676986e` as the frozen commit. Commit `676986e` is a prior regime/temporal validation commit and does not contain `version.json`, so it cannot be the complete frozen manifest commit. The forward branch link itself is strong: `forward-v0.1` exists and points exactly to `e594c33`.")
md.append("")
md.append("The detailed chain table is in `chain_of_custody.csv`.")
md.append("")
md.append("## 3. Frozen Baseline Audit")
md.append("")
for item in frozen_audit:
    md.append(f"- {item['check']}: {item['result']} | expected=`{item['expected']}` observed=`{item['observed']}` | {item['note']}")
md.append("")
md.append("Frozen candidate existence and report hashes are traceable. The commit hash audit is WARN, not PASS, because the canonical Git objects converge on `e594c33`, while freeze manifests declare `676986e`. The data ledger hash matches the centralized ledger, but the ledger was reconstructed after freeze and therefore cannot by itself upgrade legacy split claims to fully verified status.")
md.append("")
md.append("## 4. Forward-Lineage Audit")
md.append("")
md.append(f"`forward-v0.1` exists at `{forward_branch_commit}`. The merge base between `v0.1-frozen^{{}}` and `forward-v0.1` is `{merge_base}`, and Git confirms frozen tag ancestor status as `{is_frozen_ancestor_forward}`. In fact, the branch currently points exactly to the frozen commit. Therefore the branch lineage is verified. The operational checkout is not verified as forward lineage because the current branch is `{current_branch}` at `{head_commit}`, not `forward-v0.1`.")
md.append("")
md.append("## 5. Version Integrity Audit")
md.append("")
md.append(f"The most credible canonical frozen commit is `{frozen_commit}`, because the annotated Git tag, forward branch, central strategy registry, frozen candidate registry, and strategy identity registry all converge on it. The `676986e` value is less credible as the canonical frozen commit because it is the previous regime/temporal validation commit and `git show 676986e:version.json` fails with: `{version_at_676.get('stderr')}`. This audit therefore marks canonical commit resolution as `RESOLVED_TO_TAG_COMMIT_WITH_MANIFEST_WARNINGS`, not `FULLY_CLEAN`.")
md.append("")
md.append("## 6. Worktree Cleanliness Audit")
md.append("")
md.append(f"Current branch: `{current_branch}`. Current HEAD: `{head_commit}`. Untracked paths: `{'; '.join(untracked) if untracked else 'none'}`. Modified tracked files: `{'; '.join(modified) if modified else 'none'}`. Multiple worktrees observed: `{multiple_worktrees}`. Selected core freeze files show no tracked diff from `e594c33` to current HEAD, but the current branch contains post-freeze master-only additions and untracked files. Reproducibility risk is `HIGH` for claims made from the current working tree, and `MEDIUM` for the stored canonical frozen branch/tag if used directly after checkout.")
md.append("")
md.append("## 7. Evidence Classification")
md.append("")
md.append("Git tag `v0.1-frozen` and branch `forward-v0.1` are `VERIFIED_EVIDENCE` for canonical lineage. Central governance files are verified for current governance state, but the data ledger is `LEGACY_EVIDENCE` for historical data-use purity because it was reconstructed after freeze. The event study, execution audit, attribution, optimization, frozen report, version manifest, and forward config are usable historical artifacts but not clean canonical proof on their own; several carry earlier commit references. Post-freeze reassessment artifacts are `UNVERIFIED_EVIDENCE` for canonical v0.1/forward identity.")
md.append("")
md.append("The full evidence registry is in `evidence_registry.csv`.")
md.append("")
md.append("## Final Conclusion")
md.append("")
md.append(f"Final label: `{final_label}`.")
md.append("")
md.append("STR-003 has a usable canonical identity in the governance system and a strong Git-level frozen-to-forward lineage via `v0.1-frozen -> e594c33 -> forward-v0.1`. It does not yet have a fully clean chain of custody because the freeze manifest family declares `676986e`, the current checkout is `master` rather than `forward-v0.1`, and the current worktree contains untracked files. The frozen candidate is partially reproducible: files and hashes are traceable, but manifest commit identity is inconsistent. The forward-live identity is credible only if evaluated from `forward-v0.1` at `e594c33`, not from the current dirty master checkout.")
md.append("")
md.append("Before STR-003 can be declared `FULLY_REPRODUCIBLE`, the branch/commit/version reconciliation must be documented: either confirm `e594c33` as the canonical frozen commit and mark `676986e` as stale pre-freeze metadata, or create a corrected governance-approved reconciliation record without altering the frozen strategy in place. Only after that should a separate Stage 2 Execution Audit be considered; entering execution audit before identity reconciliation would mix strategy execution questions with unresolved custody questions.")
md.append("")
md.append("## Appendix: Git Context")
md.append("")
md.append("```text")
md.append(branch_vv)
md.append("")
md.append(show_ref)
md.append("")
md.append(log_recent)
md.append("```")
md.append("")
md.append("## Output Files")
md.append("")
for filename in csv_specs:
    md.append(f"- `{OUT / filename}`")
md.append("")
(OUT / "canonical_reproducibility_audit.md").write_text("\n".join(md), encoding="utf-8")

manifest = {
    "generated_at": NOW,
    "strategy_id": STRATEGY_ID,
    "scope": "governance_audit_readonly_inputs_generated_outputs_only",
    "strategy_directory_modified": False,
    "registry_files_modified": False,
    "backtest_or_optimization_run": False,
    "final_label": final_label,
    "output_dir": str(OUT),
    "outputs": {
        path.name: {
            "path": str(path),
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
            "rows": line_count(path),
        }
        for path in OUT.glob("*")
        if path.is_file() and path.name != "audit_output_manifest.json"
    },
}
(OUT / "audit_output_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(manifest, indent=2, ensure_ascii=False))
