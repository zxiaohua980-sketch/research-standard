# Frozen Baseline Registry Standard

Frozen baseline registry prevents version drift. It answers: which exact hypothesis, code, config, data snapshot, and result was frozen?

## Required registries

A mature research repository should maintain:

```text
registry/
├── strategy_registry.yaml
├── frozen_candidates.yaml
└── archived_hypotheses.yaml
```

The central strategy registry remains the top-level index. `frozen_candidates.yaml` records strategy candidates that are eligible for OOS or forward gates. `archived_hypotheses.yaml` records rejected or superseded research ideas so they are not rediscovered and retuned silently.

## Frozen candidate fields

Each frozen candidate must record:

- `candidate_id`
- `strategy_id`
- `hypothesis_id`
- `version`
- `status`
- `frozen_tag`
- `frozen_commit`
- `config_hash`
- `data_ledger_hash`
- `event_study_report`
- `audit_report`
- `attribution_report`
- `fixed_parameters`
- `execution_model`
- `cost_model`
- `allowed_evidence_after_freeze`
- `blocked_actions`
- `created_at`
- `notes`

## Archived hypothesis fields

Each archived hypothesis must record:

- `hypothesis_id`
- `strategy_id`
- `title`
- `status`
- `rejection_reason`
- `evidence_files`
- `data_used`
- `archived_at`
- `may_revisit`
- `revisit_conditions`
- `prohibited_reuse`

## Required checks

Before modifying or evaluating a strategy:

- verify the strategy exists in the central registry;
- if current stage is frozen or forward-live, verify frozen candidate record;
- verify `frozen_commit`, `config_hash`, and data ledger hash are present;
- verify the requested action is not in `blocked_actions`;
- if the task revives an old idea, check archived hypotheses first.

## Blocking conditions

Block formal claims when:

- the frozen candidate is missing;
- the frozen candidate lacks commit or config hash;
- the requested version differs from the frozen candidate;
- an archived hypothesis is being reused without a new hypothesis id and new data plan;
- a forward-live result cannot be traced to a frozen candidate.
