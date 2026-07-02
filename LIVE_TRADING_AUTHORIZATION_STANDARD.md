# Live Trading Authorization Standard

Updated: 2026-06-20

## Purpose

This standard replaces the old blanket ban that said every REAL/实盘 account must be hard-rejected.
The operating principle is now:

```text
模拟能稳定运行 + 用户明确承担资金风险 = 可以进入受控实盘试运行。
```

The research system should not block user capital on extra paperwork alone. It should only block
avoidable technical mistakes: wrong account, wrong version, wrong magic number, duplicate orders,
stale signals, missing logs, unreconciled positions, or accidental oversized risk.

## Authority

For this machine/user, if the user decides to use the same strategy/runtime in real-money mode,
the technical gates are the **same as demo order path**.

A runtime may run REAL only when all of the following are true:

1. The user explicitly requested real-money mode for this specific strategy/runtime.
2. The exact EXE/config intended for live was already run successfully in dry-run or demo/order smoke.
3. `mode` is set to `demo_trade` or `live_trade`, `order_enabled = true`, `dry_run_enforce = false`, and `kill_switch = false`.
4. The runtime prints account/server/login and trade-mode before routing orders.
5. If configured, `expected_account_server` and `expected_login` match the detected MT5 account.
6. Startup reconciliation has checked current positions, pending orders, unresolved intents, and the signal
   execution ledger before scanning new signals.
7. Position sizing is cost-inclusive and obeys `risk_cash_per_order`, `max_volume_per_order`,
   `max_positions_total`, `max_positions_per_symbol`, and `max_new_orders_per_cycle`.
8. The runtime uses a unique `magic_number` and `comment_prefix` for this strategy/version/environment.

If any item fails, the runtime must enter safe mode or `runtime_blocked`.

## What is no longer allowed as a blocker

Do not block live solely because:

- a registry field still says `production_live=false`;
- a Git tag is missing in a local-only folder, if a local hash identity is recorded;
- forward-live Gate A/B has not accumulated enough trades.

These are evidence-quality labels, not automatic prohibitions. They affect what claims can be made,
not whether the user may risk his own capital.

## Evidence Labels

Use plain labels:

- `dry_run_ready`: EXE scans/reconciles/logs without sending orders.
- `demo_ready`: order-capable runtime (DEMO or REAL) passed broker-state reconciliation.
- `live_trial_active`: real-money runtime has started; results are real operational records, not backtest or OOS-Final proof.
- `runtime_blocked`: technical or config safety check failed.

`user_authorized_live_ready` is retained as historical alias only when a project wants a separate label;
in this standard it is equivalent to `demo_ready`.

## Live Trial Rules

During `live_trial_active`:

- Do not modify strategy logic, parameters, cost model, signal timing, SL/TP, trailing, or sizing in place.
- Any strategy-rule change must create a new version/config and restart live evidence from the new activation time.
- Kill switch, manual close, or emergency disable is always allowed for safety, but must be logged as intervention.
- Performance claims must separate backtest/demo/live-trial records. Do not backfill old trades into live evidence.

## Minimum Order-Capable Config Fields

```ini
[runtime]
mode = live_trade
order_enabled = true
dry_run_enforce = false
allow_demo_trade = true
# allow_live_trade = true  ; legacy compatibility (optional; no extra gating)
kill_switch = false
expected_account_server =
expected_login =
magic_number =
comment_prefix =

[risk]
risk_cash_per_order =
max_volume_per_order =
max_total_volume =
max_positions_total =
max_positions_per_symbol =
max_new_orders_per_cycle = 1
position_sizing_mode = cost_inclusive_risk_cash

[reconciliation]
reconcile_on_startup = true
reconcile_each_cycle = true
unknown_freeze_new_orders = true

[logging]
log_dir = .\logs
signal_execution_ledger_path = .\logs\signal_execution_ledger.jsonl
```

The config may be stricter, but it should not add paperwork gates unrelated to preventing wrong orders.
