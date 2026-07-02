# Runtime Handoff

- strategy_id:
- version:
- frozen_commit:
- frozen_tag:
- config_hash:
- bar_by_bar_replay_report:
- runtime_mode: dry_run
- package_name:
- generated_at:

## Strategy Runtime Identity

- symbol/timeframe:
- magic_number:
- comment_prefix:
- environment_id: demo
- max_positions:
- max_orders_per_cycle:

## Required Inputs

- signal/runtime module:
- config.ini:
- static files:
- MT5 dependency:

## Safety Defaults

```ini
mode = dry_run
order_enabled = false
require_trade_allowed_for_orders = true
# allow_live_trade = false  ; legacy compatibility, optional
dry_run_enforce = true
kill_switch = false
terminal_path =
log_dir = .\logs
tmp_dir = .\tmp
```

## Verification

- [ ] run EXE directly and verify startup prints account/login/magic/status
- [ ] live mode blocked in DEMO/CONTEST and LIVE mode requires explicit `mode=live_trade`
- [ ] demo order mode disabled by default
- [ ] signal execution ledger present
- [ ] order intent journal present if demo orders are enabled
- [ ] startup reconciliation checked
- [ ] EXE hash recorded
- [ ] config hash recorded
- [ ] clean portable folder created

## Decision

```text
runtime_blocked | dry_run_ready | demo_ready | portable_package_ready
```
