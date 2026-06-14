# MT5 Runtime Packager v1.1.1 Governance Change Audit

Date: 2026-06-14

## Scope

This change refines the v1.1.0 runtime packaging governance. It does not change any strategy
logic, parameters, backtest data, forward-live evidence, or registry strategy state.

Affected files:

- `D:\MT5\RESEARCH_STANDARD\MT5_RUNTIME_PACKAGING_STANDARD.md`
- `D:\MT5\RESEARCH_STANDARD\.codex\skills\mt5-runtime-packager\SKILL.md`
- `D:\MT5\RESEARCH_STANDARD\.codex\skills\mt5-runtime-packager\scripts\mt5_runtime_common.py`
- `D:\MT5\RESEARCH_STANDARD\.codex\skills\mt5-runtime-packager\scripts\audit_mt5_runtime_package.py`
- `D:\MT5\RESEARCH_STANDARD\.codex\skills\mt5-runtime-packager\templates\config_cost_inclusive_pending_orders.ini`
- `D:\MT5\RESEARCH_STANDARD\.codex\skills\mt5-runtime-packager\references\mt5-runtime-common-code.md`
- `D:\MT5\RESEARCH_STANDARD\.codex\skills\mt5-runtime-packager\agents\openai.yaml`

## User Correction Captured

The user clarified that packaging must not open MT5 every time. The account state block:

```text
当前账户：ICMarketsSC-Demo
trade_allowed=True
magic 24068 持仓：0
magic 24068 挂单：0
```

is already a tested runtime behavior. It should be specified as concrete trading/runtime code and
used during intentional runtime smoke or order-enabled startup, not as a mandatory live check for
every static package build.

## Design Decision

Verification is now split into two levels:

1. **Offline/static package audit**: no `mt5.initialize()`, no terminal opening, no account query.
   It checks syntax, import safety, config fields, path portability, risk formula paths, pending
   order formula paths, signal ledger paths, build script hygiene, and portable folder hygiene.
2. **Runtime MT5 smoke**: connects to the configured/available MT5 terminal only when the user
   intentionally runs the source/EXE, authorizes DEMO order testing, or verifies the deliverable
   on the target machine.

## Concrete Trading Code Contract

`mt5_runtime_common.py` now includes reusable account/magic helpers:

- `mt5_account_state_snapshot(mt5, magic, symbol=None, include_details=True)`
- `format_mt5_account_state_lines(snapshot)`
- `mt5_account_state_blockers(snapshot, ...)`
- `write_mt5_account_state_snapshot(log_dir, snapshot)`

These helpers do not initialize MT5 and do not send/modify/close orders. The caller must initialize
MT5 only inside an explicit runtime command.

Runtime usage pattern:

```python
snapshot = mt5_account_state_snapshot(mt5, magic=config.magic_number)
for line in format_mt5_account_state_lines(snapshot):
    print(line)
write_mt5_account_state_snapshot(Path(config.log_dir), snapshot)
blockers = mt5_account_state_blockers(
    snapshot,
    expected_account_server=config.expected_account_server or None,
    expected_login=config.expected_login or None,
    require_trade_allowed=config.order_enabled,
    require_zero_magic_positions=config.require_zero_magic_positions_before_smoke,
    require_zero_magic_orders=config.require_zero_magic_orders_before_smoke,
)
if blockers:
    enter_safe_mode(blockers)
```

Account server, login, magic number and zero-state requirements must come from config/runtime
command, not hardcoded into shared helpers.

## Config Additions

`config_cost_inclusive_pending_orders.ini` now includes:

```ini
[runtime_smoke]
run_mt5_smoke_on_build = false
expected_account_server =
expected_login =
print_account_magic_snapshot = true
write_account_magic_snapshot = true
require_trade_allowed_for_orders = true
require_zero_magic_positions_before_smoke = false
require_zero_magic_orders_before_smoke = false
```

## Audit Additions

The package audit now checks:

- build/static preflight does not initialize/open MT5;
- `run_mt5_smoke_on_build` is not enabled by default;
- runtime smoke/account snapshot controls are config-visible;
- order-capable runtime has an account/magic snapshot path.

## Validation

Validation must include:

- skill validation;
- Python compile of `mt5_runtime_common.py` and `audit_mt5_runtime_package.py`;
- config template parse;
- fake-MT5 helper test confirming the short account/magic block formats as expected without
  opening a real MT5 terminal;
- PowerShell/bootstrap parse if bootstrap changes;
- `git diff --check`.

## Residual Risk

This governance defines the helper contract. Each actual strategy runtime still needs a source-level
execution audit to prove it copied/adapted the helpers correctly and does not hide MT5 side effects
in build scripts or imports.
