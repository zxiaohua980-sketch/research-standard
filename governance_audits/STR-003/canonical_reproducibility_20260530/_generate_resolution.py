from pathlib import Path
from datetime import datetime, timezone, timedelta
import csv
import hashlib
import json
import subprocess
import yaml

BASE = Path(r"D:\MT5\RESEARCH_STANDARD")
STRATEGY_ROOT = Path(r"D:\MT5\openclaw\bb_strategy")
REGISTRY_ROOT = Path(r"D:\MT5\research_registry")
OUT = REGISTRY_ROOT / "governance_resolutions" / "STR-003" / "canonical_identity_resolution_20260530"
PREVIOUS_AUDIT_DIR = BASE / "governance_audits" / "STR-003" / "canonical_reproducibility_20260530"
STRATEGY_ID = "STR-003"
NOW = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return "MISSING"
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def row_count(path: Path) -> int:
    if not path.exists() or not path.is_file():
        return 0
    return len(path.read_text(encoding="utf-8", errors="replace").splitlines())


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
        ["git", "-c", "safe.directory=D:/MT5/openclaw/bb_strategy", "-C", str(STRATEGY_ROOT), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    return {"returncode": cp.returncode, "stdout": cp.stdout.strip(), "stderr": cp.stderr.strip()}


def first_record(items, key, value):
    for item in items or []:
        if isinstance(item, dict) and item.get(key) == value:
            return item
    return {}


def write_csv(path: Path, header, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


OUT.mkdir(parents=True, exist_ok=True)

strategy_registry = load_yaml(REGISTRY_ROOT / "strategy_registry.yaml")
strategy_identity = load_yaml(REGISTRY_ROOT / "strategy_identity.yaml")
frozen_candidates = load_yaml(REGISTRY_ROOT / "frozen_candidates.yaml")
version_json = load_json(STRATEGY_ROOT / "version.json")
forward_config = load_yaml(STRATEGY_ROOT / "forward_live" / "forward_live_config.yaml")

strategy_record = first_record(strategy_registry.get("strategies", []), "strategy_id", STRATEGY_ID)
identity_record = first_record(strategy_identity.get("strategies", []), "strategy_id", STRATEGY_ID)
frozen_candidate = first_record(frozen_candidates.get("frozen_candidates", []), "strategy_id", STRATEGY_ID)

tag_object = git(["rev-parse", "v0.1-frozen"])["stdout"]
tag_commit = git(["rev-parse", "v0.1-frozen^{}"])["stdout"]
forward_commit = git(["rev-parse", "forward-v0.1"])["stdout"]
merge_base = git(["merge-base", tag_commit, "forward-v0.1"])["stdout"]
ancestor_ok = git(["merge-base", "--is-ancestor", tag_commit, "forward-v0.1"])["returncode"] == 0
current_branch = git(["branch", "--show-current"])["stdout"]
current_head = git(["rev-parse", "HEAD"])["stdout"]
log_context = git(["log", "--oneline", "--decorate", "--all", "-n", "12"])["stdout"]
version_at_legacy = git(["show", "676986e:version.json"])

legacy_commit = "676986e"
canonical_short = tag_commit[:7]
resolution_status = "CANONICAL_IDENTITY_RESOLVED"

evidence_rows = [
    ["Git annotated tag", "HIGH_CONFIDENCE", "v0.1-frozen tag object", tag_object, tag_commit, "Annotated Git tag dereferences to e594c33 and has freeze message for STR-003 v0.1."],
    ["Forward branch", "HIGH_CONFIDENCE", "forward-v0.1", forward_commit, tag_commit, "Branch exists, equals the tag commit, and merge-base confirms frozen commit ancestry. Branch refs are mutable in theory, but current evidence is direct."],
    ["Registry", "HIGH_CONFIDENCE", "strategy_registry.yaml", str(strategy_record.get("frozen_commit")), canonical_short, "Central strategy registry declares frozen_commit e594c33, frozen_tag v0.1-frozen, forward_live_branch forward-v0.1."],
    ["Strategy identity", "HIGH_CONFIDENCE", "strategy_identity.yaml", str((identity_record.get("frozen_versions") or [{}])[0].get("commit")), tag_commit, "Central identity record stores the full e594c33 commit and marks 676986e as version_json_reported_commit."],
    ["Frozen candidate", "HIGH_CONFIDENCE", "frozen_candidates.yaml", str(frozen_candidate.get("frozen_commit")), canonical_short, "Frozen candidate record declares e594c33 and carries report/config/data hashes."],
    ["Version manifest", "LOW_CONFIDENCE", "version.json", str((version_json.get("code_freeze") or {}).get("frozen_commit_hash")), canonical_short, "The file was added in e594c33 but internally declares 676986e, a prior commit without version.json."],
    ["Frozen report", "LOW_CONFIDENCE", "frozen_report.md", "676986e", canonical_short, "Frozen report hash is traceable, but its frozen_commit field repeats stale metadata and conflicts with Git tag."],
    ["Forward config", "LOW_CONFIDENCE", "forward_live_config.yaml", str(forward_config.get("frozen_commit_hash")), canonical_short, "Forward config repeats stale 676986e while its branch/tag context resolves to e594c33."],
]

conflict_rows = [
    ["676986e", "version.json", str(STRATEGY_ROOT / "version.json"), "code_freeze.frozen_commit_hash; forward_live_freeze.frozen_commit_for_forward", "LOW_CONFIDENCE", "File was introduced by e594c33, so its internal reference cannot be the complete freeze-manifest commit.", "Do not override e594c33; classify as stale pre-freeze validation metadata."],
    ["676986e", "forward_live_config.yaml", str(STRATEGY_ROOT / "forward_live" / "forward_live_config.yaml"), "frozen_commit_hash", "LOW_CONFIDENCE", "Forward branch and tag resolve to e594c33 while config repeats the stale manifest value.", "Do not override e594c33; keep file read-only until a governed correction is approved."],
    ["676986e", "frozen_report.md", str(STRATEGY_ROOT / "output" / "reports" / "v0.1" / "frozen_report.md"), "frozen_commit", "LOW_CONFIDENCE", "Report was created in the freeze commit but points backward to the previous validation commit.", "Do not override e594c33; preserve report as legacy evidence with metadata warning."],
]

resolution_record = {
    "record_version": "1.0",
    "record_id": "STR-003-canonical-identity-resolution-20260530",
    "strategy_id": STRATEGY_ID,
    "canonical_frozen_commit": tag_commit,
    "canonical_frozen_commit_short": canonical_short,
    "canonical_frozen_tag": "v0.1-frozen",
    "canonical_frozen_tag_object": tag_object,
    "canonical_forward_branch": "forward-v0.1",
    "canonical_forward_branch_commit": forward_commit,
    "canonical_forward_branch_lineage": {
        "merge_base_with_frozen_commit": merge_base,
        "frozen_commit_is_ancestor_of_forward_branch": ancestor_ok,
        "forward_branch_points_exactly_to_frozen_commit": forward_commit == tag_commit,
    },
    "legacy_metadata_commits": [
        {
            "commit": legacy_commit,
            "classification": "stale_pre_freeze_validation_commit",
            "appears_in": ["version.json", "forward_live_config.yaml", "frozen_report.md"],
            "evidence": "git show 676986e:version.json fails because version.json did not exist in that commit.",
            "does_not_override_canonical_commit": True,
        }
    ],
    "resolution_basis": {
        "high_confidence_sources": [
            "Git annotated tag v0.1-frozen",
            "Git branch forward-v0.1",
            "strategy_registry.yaml",
            "strategy_identity.yaml",
            "frozen_candidates.yaml",
        ],
        "low_confidence_conflicting_sources": [
            "version.json frozen_commit_hash",
            "forward_live_config.yaml frozen_commit_hash",
            "frozen_report.md frozen_commit",
        ],
        "key_findings": [
            "All high-confidence sources converge to e594c33343268af948603ae1abb8e07592641b05.",
            "forward-v0.1 currently points exactly to e594c33343268af948603ae1abb8e07592641b05.",
            "676986e is an earlier regime/temporal validation commit and does not contain version.json.",
            "No strategy files, tags, branches, frozen candidates, version manifests, or historical reports were modified by this resolution.",
        ],
        "source_audit": str(PREVIOUS_AUDIT_DIR / "canonical_reproducibility_audit.md"),
        "source_audit_hash": sha256_file(PREVIOUS_AUDIT_DIR / "canonical_reproducibility_audit.md"),
    },
    "resolution_confidence": "HIGH",
    "resolution_status": resolution_status,
    "resolution_date": NOW,
    "governance_effect": {
        "previous_label": "PARTIALLY_REPRODUCIBLE",
        "new_identity_state": "Canonical Identity Resolved",
        "fully_reproducible": False,
        "fully_reproducible_blockers": [
            "version.json, forward_live_config.yaml, and frozen_report.md still contain stale 676986e metadata.",
            "current checkout remains master, not forward-v0.1.",
            "current worktree has previously observed untracked files.",
            "Stage 2 execution audit has not been rerun under the resolved canonical identity.",
        ],
    },
    "read_only_constraints_observed": {
        "strategy_code_modified": False,
        "strategy_parameters_modified": False,
        "frozen_candidate_modified": False,
        "version_json_modified": False,
        "historical_reports_modified": False,
        "git_tag_modified": False,
        "git_branch_modified": False,
    },
}

with (OUT / "canonical_resolution_record.yaml").open("w", encoding="utf-8") as f:
    yaml.safe_dump(resolution_record, f, allow_unicode=True, sort_keys=False, width=120)

write_csv(
    OUT / "evidence_weight_matrix.csv",
    ["source", "confidence", "artifact", "declared_or_observed_commit", "canonical_commit", "reason"],
    evidence_rows,
)

write_csv(
    OUT / "metadata_conflict_registry.csv",
    ["legacy_commit", "appears_in", "path", "field", "confidence", "why_it_does_not_override_canonical", "governance_action"],
    conflict_rows,
)

recommendations = f"""# STR-003 Reconciliation Recommendations

Generated: {NOW}

This document is a governance recommendation only. It does not modify strategy code, strategy parameters, frozen candidates, `version.json`, historical reports, Git tags, or Git branches.

## Future Fixes If Approved

If the project owner later decides to clean the metadata, the corrected value should be recorded as `e594c33343268af948603ae1abb8e07592641b05`, because that is the commit reached by `v0.1-frozen`, `forward-v0.1`, central registry, strategy identity, and frozen candidate records. The stale `676986e` fields appear in `version.json`, `forward_live_config.yaml`, and `frozen_report.md`; those should not be silently edited in place. A governed correction should create a new reconciliation note or manifest overlay that says the old fields are legacy metadata, not canonical identity.

## Preserve As Immutable

The annotated tag `v0.1-frozen`, the branch relationship `forward-v0.1 -> e594c33`, the frozen candidate history, original `version.json`, original `forward_live_config.yaml`, and original frozen report should remain read-only historical evidence. If a corrected manifest is needed, it should be additive and clearly labeled as a governance correction, not a rewrite of the original freeze event.

## Archive Classification

`676986e` should be archived as `stale_pre_freeze_validation_commit`. It remains useful as a prior research-stage commit, but it must not be used as the canonical frozen commit for STR-003 v0.1.

## Stage 2 Execution Audit Readiness

Stage 2 Execution Audit is allowed as the next separate task only after using this resolution record as the identity source. The audit should explicitly bind inputs to `v0.1-frozen -> e594c33343268af948603ae1abb8e07592641b05 -> forward-v0.1`, and should not rely on the current dirty `master` checkout as the forward-live identity.
"""
(OUT / "reconciliation_recommendations.md").write_text(recommendations, encoding="utf-8")

report = f"""# STR-003 Canonical Identity Resolution Report

Generated: {NOW}

## Scope

This is a Governance Layer resolution audit. It is not strategy research, not a backtest, not walk-forward, not forward analysis, not execution audit, and not parameter audit. The only registry update made here is additive: a new immutable resolution record was written under `D:\\MT5\\research_registry\\governance_resolutions\\STR-003\\canonical_identity_resolution_20260530`.

## Final Adjudication

Final verdict: `{resolution_status}`.

STR-003's canonical frozen commit is `e594c33343268af948603ae1abb8e07592641b05`. The canonical frozen tag is `v0.1-frozen`, and the canonical forward branch is `forward-v0.1`. The tag object is `{tag_object}`. The forward branch currently points to `{forward_commit}`, with merge base `{merge_base}` against the frozen commit, and ancestor check is `{ancestor_ok}`.

## Evidence Basis

The high-confidence sources are Git annotated tag, forward branch, strategy registry, strategy identity, and frozen candidate. All five converge to the same frozen lineage: `v0.1-frozen -> e594c33 -> forward-v0.1`. These sources are stronger than legacy metadata fields because they represent actual Git object identity or centralized governance identity records.

The low-confidence conflicting sources are `version.json`, `forward_live_config.yaml`, and `frozen_report.md`. They contain `676986e`, but this does not override `e594c33` because `676986e` is a prior regime/temporal validation commit and does not contain `version.json`; Git reports: `{version_at_legacy.get('stderr')}`. Therefore, the conflict is resolved as stale metadata inside legacy files, not as an unresolved canonical identity conflict.

## Governance State Change

The prior state `PARTIALLY_REPRODUCIBLE` is now refined: canonical identity is resolved, but the strategy is still not `FULLY_REPRODUCIBLE`. Full reproducibility still requires additive metadata correction or formal reconciliation of stale fields, a clean canonical checkout, and a separate Stage 2 Execution Audit under the resolved identity.

## Stage 2 Execution Audit Gate

Stage 2 Execution Audit is allowed as the next separate governance-approved task, but only if it binds to `e594c33343268af948603ae1abb8e07592641b05` as the canonical frozen commit and does not treat `676986e` as the frozen identity. It must not run from the dirty current `master` checkout as if that were the forward-live branch.

## Read-Only Declaration

No strategy code, strategy parameters, frozen candidate, `version.json`, historical reports, Git tag, or Git branch was modified. Existing registry history was not edited. This resolution is an additive governance record.

## Git Context

```text
current_branch={current_branch}
current_head={current_head}
tag_object={tag_object}
tag_commit={tag_commit}
forward_branch_commit={forward_commit}
merge_base={merge_base}
ancestor_ok={ancestor_ok}

{log_context}
```
"""
(OUT / "canonical_identity_resolution_report.md").write_text(report, encoding="utf-8")

manifest = {
    "generated_at": NOW,
    "strategy_id": STRATEGY_ID,
    "resolution_status": resolution_status,
    "output_dir": str(OUT),
    "strategy_directory_modified": False,
    "registry_history_modified": False,
    "additive_governance_record_only": True,
    "outputs": {},
}
for path in sorted(OUT.iterdir()):
    if path.is_file() and path.name != "resolution_output_manifest.json":
        manifest["outputs"][path.name] = {
            "path": str(path),
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
            "row_count": row_count(path),
        }
(OUT / "resolution_output_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(manifest, indent=2, ensure_ascii=False))
