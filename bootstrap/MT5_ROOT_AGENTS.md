# MT5 Strategy Research Entry Gate

Installed workspace root: `{{MT5_ROOT}}`

Any task under `{{MT5_ROOT}}` that concerns a trading strategy, EA, signal, backtest,
optimization, risk rule, forward validation, or deployment must follow:

- `{{RESEARCH_STANDARD_ROOT}}\AGENTS.md`
- `{{RESEARCH_STANDARD_ROOT}}\RESEARCH_WORKFLOW.md`
- `{{RESEARCH_STANDARD_ROOT}}\DATA_SPLIT_AND_OOS_POLICY.md` when any result is described as
  in-sample, OOS, holdout, walk-forward or forward-live
- `{{RESEARCH_STANDARD_ROOT}}\EXIT_RISK_AND_LOGIC_REFINEMENT_STANDARD.md` when execution,
  stops, targets, sizing, exits, or live safeguards are involved

Before strategy work, query `{{REGISTRY_FILE}}`, identify the research stage and
freeze/forward status, and enforce all gates from the canonical policy. This file is an
entry pointer; the canonical policy remains authoritative.

If the canonical documents mention the original `D:\MT5` path, interpret that as this
installed workspace root on this machine unless a task explicitly concerns the original
computer's filesystem.

If the project root contains `PROJECT_STATE.md`, read it after the global research standard
and registry lookup. Treat it as the current handoff/context file for that project. It may
summarize local status, frozen candidates, runtime state, blocked actions, and next steps,
but it must not weaken the canonical policy or the registry.
