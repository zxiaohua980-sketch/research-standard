# STR-003 Canonical Reproducibility Audit

Generated: 2026-05-30T16:12:57+08:00

## Scope And Gate Statement

This is a governance audit, not a strategy audit. No backtest, walk-forward, optimization, forward-live analysis, parameter change, strategy-code change, ledger edit, or registry edit was performed. The task is Stage 12 forward-live governance verification: code changes are not allowed, parameter changes are not allowed, and backtest metrics remain non-decision-grade unless a separate execution audit and identity reconciliation are completed.

## 1. Canonical Identity Audit

STR-003 is registered as `Bollinger Band Breakout LONG-ONLY on XAUUSD H1` at `D:\MT5\openclaw\bb_strategy`. The current working tree is on branch `master` at `43e8b8e0dd2aece8f73e50fa76ef4e2ca022f645`, while the registered forward branch is `forward-v0.1` and resolves to `e594c33343268af948603ae1abb8e07592641b05`. The frozen tag `v0.1-frozen` is an annotated tag object `1ab4d800f45c073862758582c124218d44467463` and dereferences to `e594c33343268af948603ae1abb8e07592641b05`. The governance registry and frozen candidate both point to `e594c33`, while `version.json`, `forward_live_config.yaml`, and `frozen_report.md` declare `676986e`.

The detailed identity matrix is in `identity_matrix.csv`. The identity exists, but it is not fully unique across all artifacts because the freeze manifest family and Git tag family disagree on the frozen commit.

## 2. Chain Of Custody Audit

The research chain exists from event study through execution audit, attribution, optimization, freeze report, frozen tag, forward branch, and forward config. The main `CHAIN_BREAK` occurs at the freeze boundary: `version.json` and `frozen_report.md` were added in commit `e594c33`, yet both declare `676986e` as the frozen commit. Commit `676986e` is a prior regime/temporal validation commit and does not contain `version.json`, so it cannot be the complete frozen manifest commit. The forward branch link itself is strong: `forward-v0.1` exists and points exactly to `e594c33`.

The detailed chain table is in `chain_of_custody.csv`.

## 3. Frozen Baseline Audit

- frozen_candidate_exists: PASS | expected=`STR-003-v0.1-frozen` observed=`STR-003-v0.1-frozen` | Central frozen candidate record exists.
- commit_hash: WARN | expected=`e594c33` observed=`e594c33` | Registry/frozen candidate match tag; version.json does not.
- config_hash: PASS | expected=`sha256:72629a408893d8406d10fc64db934a8c70b722e8e6c800f7e176a481e57c6676` observed=`sha256:72629a408893d8406d10fc64db934a8c70b722e8e6c800f7e176a481e57c6676` | Stored config_hash matches current version.json file hash.
- data_ledger_hash: PASS | expected=`sha256:b76a7f0c1ae966f68cd497dc791a18f985a0a32beaaadee10fa67af78b74cf78` observed=`sha256:b76a7f0c1ae966f68cd497dc791a18f985a0a32beaaadee10fa67af78b74cf78` | Central ledger hash matches frozen candidate hash, but ledger was reconstructed after freeze.
- event_study_report_hash: PASS | expected=`sha256:81a1684eb25558fb646ee41964c0bfe2488e40245c8086f8eaff519e50ffc5a6` observed=`sha256:81a1684eb25558fb646ee41964c0bfe2488e40245c8086f8eaff519e50ffc5a6` | Hash comparison for event_study_report.
- audit_report_hash: PASS | expected=`sha256:2a9bcd672d8a54274336fdaaf5536f94121b15b56d73edba767bf4198dc1ea5b` observed=`sha256:2a9bcd672d8a54274336fdaaf5536f94121b15b56d73edba767bf4198dc1ea5b` | Hash comparison for execution_audit.
- attribution_report_hash: PASS | expected=`sha256:ec81815d23cf85a16b76fd029b91f2cf4639d72a1ce85d289f167c843b6ed43e` observed=`sha256:ec81815d23cf85a16b76fd029b91f2cf4639d72a1ce85d289f167c843b6ed43e` | Hash comparison for trade_attribution.
- frozen_report_hash: PASS | expected=`sha256:0fcdaff13537e0c751f7d8cb8a4155c116bc2e2f6a05ef4f9402f9e7f5535cb7` observed=`sha256:0fcdaff13537e0c751f7d8cb8a4155c116bc2e2f6a05ef4f9402f9e7f5535cb7` | Hash comparison for frozen_report.

Frozen candidate existence and report hashes are traceable. The commit hash audit is WARN, not PASS, because the canonical Git objects converge on `e594c33`, while freeze manifests declare `676986e`. The data ledger hash matches the centralized ledger, but the ledger was reconstructed after freeze and therefore cannot by itself upgrade legacy split claims to fully verified status.

## 4. Forward-Lineage Audit

`forward-v0.1` exists at `e594c33343268af948603ae1abb8e07592641b05`. The merge base between `v0.1-frozen^{}` and `forward-v0.1` is `e594c33343268af948603ae1abb8e07592641b05`, and Git confirms frozen tag ancestor status as `True`. In fact, the branch currently points exactly to the frozen commit. Therefore the branch lineage is verified. The operational checkout is not verified as forward lineage because the current branch is `master` at `43e8b8e0dd2aece8f73e50fa76ef4e2ca022f645`, not `forward-v0.1`.

## 5. Version Integrity Audit

The most credible canonical frozen commit is `e594c33343268af948603ae1abb8e07592641b05`, because the annotated Git tag, forward branch, central strategy registry, frozen candidate registry, and strategy identity registry all converge on it. The `676986e` value is less credible as the canonical frozen commit because it is the previous regime/temporal validation commit and `git show 676986e:version.json` fails with: `fatal: path 'version.json' exists on disk, but not in '676986e'`. This audit therefore marks canonical commit resolution as `RESOLVED_TO_TAG_COMMIT_WITH_MANIFEST_WARNINGS`, not `FULLY_CLEAN`.

## 6. Worktree Cleanliness Audit

Current branch: `master`. Current HEAD: `43e8b8e0dd2aece8f73e50fa76ef4e2ca022f645`. Untracked paths: `1.txt; analysis/paper_forward_observation_runner.py; analysis/reassessment_pipeline.py; output/reports/reassessment_20260527/`. Modified tracked files: `none`. Multiple worktrees observed: `False`. Selected core freeze files show no tracked diff from `e594c33` to current HEAD, but the current branch contains post-freeze master-only additions and untracked files. Reproducibility risk is `HIGH` for claims made from the current working tree, and `MEDIUM` for the stored canonical frozen branch/tag if used directly after checkout.

## 7. Evidence Classification

Git tag `v0.1-frozen` and branch `forward-v0.1` are `VERIFIED_EVIDENCE` for canonical lineage. Central governance files are verified for current governance state, but the data ledger is `LEGACY_EVIDENCE` for historical data-use purity because it was reconstructed after freeze. The event study, execution audit, attribution, optimization, frozen report, version manifest, and forward config are usable historical artifacts but not clean canonical proof on their own; several carry earlier commit references. Post-freeze reassessment artifacts are `UNVERIFIED_EVIDENCE` for canonical v0.1/forward identity.

The full evidence registry is in `evidence_registry.csv`.

## Final Conclusion

Final label: `PARTIALLY_REPRODUCIBLE`.

STR-003 has a usable canonical identity in the governance system and a strong Git-level frozen-to-forward lineage via `v0.1-frozen -> e594c33 -> forward-v0.1`. It does not yet have a fully clean chain of custody because the freeze manifest family declares `676986e`, the current checkout is `master` rather than `forward-v0.1`, and the current worktree contains untracked files. The frozen candidate is partially reproducible: files and hashes are traceable, but manifest commit identity is inconsistent. The forward-live identity is credible only if evaluated from `forward-v0.1` at `e594c33`, not from the current dirty master checkout.

Before STR-003 can be declared `FULLY_REPRODUCIBLE`, the branch/commit/version reconciliation must be documented: either confirm `e594c33` as the canonical frozen commit and mark `676986e` as stale pre-freeze metadata, or create a corrected governance-approved reconciliation record without altering the frozen strategy in place. Only after that should a separate Stage 2 Execution Audit be considered; entering execution audit before identity reconciliation would mix strategy execution questions with unresolved custody questions.

## Appendix: Git Context

```text
forward-v0.1 e594c33 [FREEZE] strategy_id=STR-003, version=v0.1
* master       43e8b8e [FINAL] strategy_id=STR-003, action=wrap

e594c33343268af948603ae1abb8e07592641b05 refs/heads/forward-v0.1
43e8b8e0dd2aece8f73e50fa76ef4e2ca022f645 refs/heads/master
1ab4d800f45c073862758582c124218d44467463 refs/tags/v0.1-frozen

43e8b8e (HEAD -> master) [FINAL] strategy_id=STR-003, action=wrap
c1bffc3 [PORTFOLIO] strategy_id=STR-003, action=diversification-analysis
2975cab [OVERLAY_M30] strategy_id=STR-003, action=m30-cross-market
ef604db [OVERLAY_CROSS_MARKET] strategy_id=STR-003, action=cross-market-overlay
4599510 [OVERLAY_BACKTEST] strategy_id=STR-003, action=adaptive-overlay-test
f4e985f [ARCHITECTURE] strategy_id=STR-003, action=regime-aware-architecture
4d6ac98 [REGIME_FAILURE] strategy_id=STR-003, action=regime-failure-research
e594c33 (tag: v0.1-frozen, forward-v0.1) [FREEZE] strategy_id=STR-003, version=v0.1
676986e [REGIME+TEMPORAL] strategy_id=STR-003, action=regime+temporal-validation
72575eb [OPTIM] strategy_id=STR-003, action=optimize-params
de7338b [ATTRIB] strategy_id=STR-003, action=attribution
06f7350 [EVENT] strategy_id=STR-003, action=event-analysis
d8a8e88 [AUDIT] strategy_id=STR-003, action=audit
40d68a4 [INIT] strategy_id=STR-003, hypothesis=BB_breakout_momentum
```

## Output Files

- `D:\MT5\RESEARCH_STANDARD\governance_audits\STR-003\canonical_reproducibility_20260530\identity_matrix.csv`
- `D:\MT5\RESEARCH_STANDARD\governance_audits\STR-003\canonical_reproducibility_20260530\chain_of_custody.csv`
- `D:\MT5\RESEARCH_STANDARD\governance_audits\STR-003\canonical_reproducibility_20260530\evidence_registry.csv`
- `D:\MT5\RESEARCH_STANDARD\governance_audits\STR-003\canonical_reproducibility_20260530\reproducibility_risks.csv`
