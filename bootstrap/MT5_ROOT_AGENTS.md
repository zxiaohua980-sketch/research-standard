# MT5 Strategy Research Entry Gate

Any task under `D:\MT5` that concerns a trading strategy, EA, signal, backtest,
optimization, risk rule, forward validation, or deployment must follow:

- `D:\MT5\RESEARCH_STANDARD\AGENTS.md`
- `D:\MT5\RESEARCH_STANDARD\RESEARCH_WORKFLOW.md`
- `D:\MT5\RESEARCH_STANDARD\DATA_SPLIT_AND_OOS_POLICY.md` when any result is described as
  in-sample, OOS, holdout, walk-forward or forward-live
- `D:\MT5\RESEARCH_STANDARD\EXIT_RISK_AND_LOGIC_REFINEMENT_STANDARD.md` when execution,
  stops, targets, sizing, exits, or live safeguards are involved

Before strategy work, query `D:\MT5\research_registry\strategy_registry.yaml`, identify the
research stage and freeze/forward status, and enforce all gates from the canonical policy.
This file is an entry pointer; the canonical policy remains authoritative.

If the project root contains `PROJECT_STATE.md`, read it after the global research standard
and registry lookup. Treat it as the current handoff/context file for that project. It may
summarize local status, frozen candidates, runtime state, blocked actions, and next steps,
but it must not weaken the canonical policy or the registry.

