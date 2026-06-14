# MT5 Runtime Packager v1.1.0 Governance Change Audit

Date: 2026-06-14

## Scope

This audit covers a governance/skill update for MT5 runtime packaging. It does not change any
strategy source code, strategy parameters, backtest data, forward-live logs, or registry strategy
state.

Affected files:

- `D:\MT5\RESEARCH_STANDARD\MT5_RUNTIME_PACKAGING_STANDARD.md`
- `D:\MT5\RESEARCH_STANDARD\.codex\skills\mt5-runtime-packager\SKILL.md`
- `D:\MT5\RESEARCH_STANDARD\.codex\skills\mt5-runtime-packager\templates\config_cost_inclusive_pending_orders.ini`
- `D:\MT5\RESEARCH_STANDARD\.codex\skills\mt5-runtime-packager\scripts\audit_mt5_runtime_package.py`
- `D:\MT5\RESEARCH_STANDARD\.codex\skills\mt5-runtime-packager\agents\openai.yaml`
- `D:\MT5\RESEARCH_STANDARD\bootstrap\install_on_new_pc.ps1`

## User Requirements Captured

1. Position sizing must calculate lots as configured stop-loss cash divided by total per-lot risk.
2. Total per-lot risk must include:
   - entry-to-SL price loss;
   - commission;
   - fixed or configured spread;
   - slippage estimate.
3. Default non-exempt commission is USD 7 per lot per closed trade.
4. XAUUSD and BTCUSD may be commission-free, but only through explicit config/override.
5. Pending orders must declare how spread changes entry, SL, and TP.
6. The preferred conservative policy is:
   - BUY entry = raw entry + spread;
   - BUY SL = raw SL - spread;
   - BUY TP = raw TP;
   - SELL entry = raw entry - spread;
   - SELL SL = raw SL + spread;
   - SELL TP = raw TP.
7. The runtime must prevent duplicate orders from the same signal K-line.
8. `config.ini` design itself must be auditable before packaging.

## Design Decision

The skill now supports two named pending-order price policies:

### `conservative_full_spread`

This is the default policy and matches the user's requested conservative spread expansion.
It is intentionally symmetric and easier to audit across runtime variants.

### `broker_bidask_exact`

This is reserved for runtimes that explicitly model MT5 bid/ask trigger mechanics. It requires
logging which side triggers entry, SL, and TP, and must be audited against `symbol_info_tick().bid`
and `symbol_info_tick().ask`.

## Required Config Contract

The package skill now requires order-capable runtimes to expose at least:

```ini
[risk]
position_sizing_mode = cost_inclusive_risk_cash
risk_cash_per_order = 100
include_commission_in_risk = true
commission_per_lot_round_turn_usd = 7.0
commission_free_symbols = XAUUSD,BTCUSD
include_spread_in_risk = true
spread_source = fixed_points
fixed_spread_points_default =
include_slippage_in_risk = true
slippage_points_entry = 0
slippage_points_exit = 0
volume_rounding = floor_to_step
max_risk_overshoot_pct = 0

[orders]
pending_price_policy = conservative_full_spread
signal_price_basis = bid_chart
spread_price_source = same_as_risk
adjust_pending_entry_for_spread = true
adjust_sl_for_spread = true
adjust_tp_for_spread = false
reject_if_adjusted_sl_invalid = true
min_pending_distance_points_buffer = 0

[duplicate_signal_guard]
signal_execution_ledger_path = .\logs\signal_execution_ledger.jsonl
signal_key_fields = strategy_id,symbol,timeframe,signal_bar_time,side,setup_id
consume_signal_before_order_send = true
block_duplicate_signal_bar = true
duplicate_scope = symbol_timeframe_side_magic
```

## Audit Requirements Added

Order-capable package audits must now verify:

1. the sizing function uses `lots = risk_cash_per_order / total_risk_cash_per_lot`;
2. `total_risk_cash_per_lot` includes price loss, commission, spread, and slippage;
3. commission-free symbols are config-driven and logged;
4. adjusted pending entry/SL/TP levels are logged with raw levels;
5. adjusted SL validity, broker stops-level, minimum distance, and tick-size rounding are checked;
6. one completed signal bar cannot place more than one order after same-bar close or runtime restart.

## Validation Performed

- `py_compile` passed for the repo and local `audit_mt5_runtime_package.py`.
- PowerShell parser passed for `D:\MT5\RESEARCH_STANDARD\bootstrap\install_on_new_pc.ps1`.
- Skill validation passed for both:
  - `C:\Users\86640\.codex\skills\mt5-runtime-packager`
  - `D:\MT5\RESEARCH_STANDARD\.codex\skills\mt5-runtime-packager`
- `configparser` parsed `config_cost_inclusive_pending_orders.ini` and confirmed required
  `[risk]`, `[orders]`, and `[duplicate_signal_guard]` fields.
- `git diff --check` passed.

## Residual Risks

This update defines packaging and config audit requirements. It does not by itself prove an
individual strategy runtime implements the formulas correctly. Each runtime still needs a
source-level execution audit before packaging and a final EXE smoke test from the portable folder.
