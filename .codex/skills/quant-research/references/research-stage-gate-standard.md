# Research Stage Gate Standard

Stage Gate turns research workflow into explicit allowed and blocked actions. The agent should behave like a research supervisor: correct actions at the wrong stage are still blocked.

## Required state

Each active strategy or study should have a machine-readable state file with:

- `strategy_id`
- `hypothesis_id`
- `current_stage`
- `stage_status`
- `allowed_actions`
- `blocked_actions`
- `required_inputs`
- `required_outputs`
- `next_gate`
- `decision_grade_allowed`
- `frozen_candidate_required`
- `ledger_required`
- `updated_at`

## Canonical stages

Use repository AGENTS.md as the authority. This Skill uses these normalized stage names:

- `registration`
- `hypothesis`
- `event_study`
- `execution_audit`
- `baseline_backtest`
- `trade_attribution`
- `logic_refinement`
- `parameter_robustness`
- `walk_forward_diagnostic`
- `regime_temporal_diagnostic`
- `locked_final_evaluation`
- `frozen`
- `forward_live`
- `production`
- `archived`

## Example gate rules

### event_study

Allowed:

- define events;
- compute MFE/MAE and final return distributions;
- run counterfactual comparison;
- produce event study report.

Blocked:

- tune SL/TP;
- add filters;
- run walk-forward;
- claim strategy profitability;
- open locked final holdout.

### trade_attribution

Allowed:

- compare winners and losers;
- identify entry, exit, risk, and tail dependencies;
- propose bounded logic changes.

Blocked:

- implement changes without a logic change proposal;
- tune parameters;
- evaluate locked final holdout.

### frozen

Allowed:

- read-only OOS/final reports if not consumed;
- prepare forward-live branch/config;
- integrity checks.

Blocked:

- modify parameters;
- add filters;
- change SL/TP or sizing;
- alter cost model;
- rewrite frozen report.

### forward_live

Allowed:

- append new post-framework signals/trades;
- run integrity checks;
- evaluate Gate A/B when due;
- log operational interventions.

Blocked:

- backfill historical trades;
- change frozen logic;
- retune based on early losses;
- merge forward branch back into frozen branch.

## Gate output

Every gate check should return:

- requested action;
- current stage;
- status: `ALLOW`, `BLOCK`, or `WARN`;
- matched rule;
- missing prerequisites;
- next allowed action.
