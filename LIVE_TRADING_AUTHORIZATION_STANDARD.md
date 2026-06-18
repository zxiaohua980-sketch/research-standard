# Live Trading Authorization Standard

Updated: 2026-06-19

## Purpose

This standard replaces the old blanket ban that said every REAL/实盘 account must be hard-rejected.
The operating principle is now:

```text
模拟能稳定运行 + 用户明确承担资金风险 = 可以进入受控实盘试运行。
```

The job of the research system is not to stop the trader from using his own capital. Its job is to
prevent preventable technical mistakes: wrong account, wrong version, wrong magic number, duplicate
orders, broken sizing, stale signals, missing logs, unreconciled positions, or accidental oversized
risk.

## Authority

For this machine/user, the user may explicitly authorize real-money trading. When that authorization
exists, Codex must not block live deployment merely because the account is REAL.

A runtime may trade REAL only when all of the following are true:

1. The user explicitly requested live/实盘 use for this specific strategy/runtime.
2. The exact EXE/config intended for live was already run successfully in dry-run or demo/order-smoke.
3. `config.ini` uses `mode = live_trade` and `allow_live_trade = true`.
4. `config.ini` contains `live_trade_ack = I_ACCEPT_REAL_MONEY_RISK`.
5. The runtime prints the detected account server/login/trade mode before order routing.
6. If configured, `expected_account_server` and `expected_login` match the detected MT5 account.
7. `kill_switch = false`, MT5 `trade_allowed=True`, and terminal trading is enabled.
8. Position sizing is cost-inclusive and obeys `risk_cash_per_order`, `max_volume_per_order`,
   `max_positions_total`, `max_positions_per_symbol`, and `max_new_orders_per_cycle`.
9. Startup reconciliation has checked current positions, pending orders, recent history, unresolved
   intents, and the signal execution ledger before scanning new signals.
10. The runtime uses a unique `magic_number` and `comment_prefix` for this strategy/version/environment.

If any item fails, the runtime must enter safe mode or `runtime_blocked`.

## What is no longer allowed as a blocker

Do not block live solely because:

- the account is REAL;
- Stage 13 paperwork is not complete;
- a registry field still says `production_live=false` while the user has explicitly chosen a live trial;
- a Git tag is missing in a local-only folder, if a local hash identity is recorded;
- forward-live Gate A/B has not accumulated enough trades.

These are evidence-quality labels, not automatic prohibitions. They affect what claims can be made,
not whether the user may risk his own capital.

## Evidence Labels

Use plain labels:

- `dry_run_ready`: EXE scans/reconciles/logs without sending orders.
- `demo_ready`: DEMO order path passed broker-state reconciliation.
- `user_authorized_live_ready`: exact EXE/config passed static audit and runtime smoke and is configured for live by user choice.
- `live_trial_active`: real-money runtime has started; results are real operational records, not backtest or OOS-Final proof.
- `runtime_blocked`: technical or config safety check failed.

## Live Trial Rules

During `live_trial_active`:

- Do not modify strategy logic, parameters, cost model, signal timing, SL/TP, trailing, or sizing in place.
- Any strategy-rule change must create a new version/config and restart live evidence from the new activation time.
- Kill switch, manual close, or emergency disable is always allowed for safety, but must be logged as intervention.
- Performance claims must separate backtest/demo/live-trial records. Do not backfill old trades into live evidence.

## Minimum Live Config Fields

```ini
[runtime]
mode = live_trade
allow_live_trade = true
allow_demo_trade = false
live_trade_ack = I_ACCEPT_REAL_MONEY_RISK
kill_switch = false
order_enabled = true
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
