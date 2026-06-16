# Portable MT5 Runtime Pattern

Use this reference when implementing or repairing an MT5 Python runtime package that must survive moving to another Windows machine.

## Auto-Discover MT5 Paths

Preferred connection pattern:

```python
from pathlib import Path


def initialize_mt5(mt5, terminal_path: str = ""):
    if terminal_path:
        ok = mt5.initialize(path=terminal_path)
    else:
        ok = mt5.initialize()
    if not ok:
        raise RuntimeError(f"mt5.initialize() failed: {mt5.last_error()}")

    info = mt5.terminal_info()
    if info is None:
        raise RuntimeError("mt5.terminal_info() returned None")

    return {
        "terminal_path": Path(info.path),
        "data_path": Path(info.data_path),
        "mql5_files": Path(info.data_path) / "MQL5" / "Files",
        "commondata_path": Path(info.commondata_path) if getattr(info, "commondata_path", None) else None,
    }
```

Fallback file discovery when not connected:

```python
import os
from pathlib import Path


def discover_mql5_files(required_names=()):
    appdata = Path(os.environ.get("APPDATA", ""))
    root = appdata / "MetaQuotes" / "Terminal"
    matches = []
    if root.exists():
        for files_dir in root.glob("*/MQL5/Files"):
            if not required_names or all((files_dir / name).exists() for name in required_names):
                matches.append(files_dir)
    matches.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return matches[0] if matches else None
```

Rules:

- Keep `terminal_path` as an optional external config value.
- Derive `MQL5\Files` from `terminal_info().data_path` after connecting.
- Log the selected terminal path and data path.
- Do not hardcode Terminal hash folders.
- Use runtime-local `tmp` for generated files.

## Frozen EXE Path Pattern

Use this at the top of a PyInstaller-compatible entrypoint:

```python
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", SCRIPT_DIR))
RUNTIME_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else SCRIPT_DIR
```

Resolve config like this:

```python
def resolve_config_path(config_path: str) -> Path:
    path = Path(config_path)
    if path.is_absolute():
        return path
    cwd_path = Path.cwd() / path
    if cwd_path.exists():
        return cwd_path
    return RUNTIME_DIR / path
```

Resolve relative logs/temp from the config file directory:

```python
def resolve_runtime_path(config_path: Path, raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path
    return config_path.parent / path
```

## Onefile vs Onedir Runtime Tradeoff

For continuous MT5 monitors, prefer a single-process `onedir/standalone` package unless the user
explicitly prioritizes one-file transport.

- `onefile` often shows a bootloader parent process plus the child runtime process during execution.
- `onedir` usually runs as one long-lived runtime process with one primary EXE plus a dependency
  directory such as `_internal\`.
- A visible two-PID pattern from `onefile` alone is not enough to declare duplicate-instance risk.

Default concurrency profile for continuous MT5 monitors:

```ini
[runtime]
package_profile = onedir_single_process
runtime_concurrency = single_thread
tick_monitor_execution = inline_main_loop
background_worker_threads = 0
```

- Keep signal scan, tick-level pending watch, reconciliation, logging, and order routing in one main loop by default.
- Do not make tick monitoring imply a second background thread by default.
- Extra threads/processes are an exception profile, not the default operator package.

## Operator Deliverable Verification

`dist` may contain developer/build artifacts. The final user-facing operator folder must be a
separate clean portable/release folder.

Minimum operator contents:

```text
onefile_minimal\
  runtime.exe
  config.ini
  logs\
  data_cache\   # optional; only if config uses it
```

```text
onedir_single_process\
  runtime.exe
  _internal\    # or runtime_libs\
  config.ini
  logs\
  data_cache\   # optional; only if config uses it
```

Forbidden in the operator folder:

```text
*.bat
*.cmd
*.ps1
*.py
*.spec
build\
dist\
__pycache__\
historical logs/caches
local test configs
```

Recommended docs and hash evidence may be kept in a build/audit folder outside the operator
deliverable unless the user explicitly asks to include them.

## Immediate EXE Smoke And Log Check

After creating the operator folder, run the EXE immediately from that folder or an exact temporary
copy. Then inspect logs before handoff:

```powershell
.\package\runtime.exe
python .\scripts\check_runtime_logs_for_errors.py .\package --report .\post_package_log_check_report.json
```

If the log checker reports any fatal/error/traceback/exception evidence, do not ship the package.
Keep `post_package_log_check_report.json` outside the operator folder. After smoke passes, clean
delivery `logs\` and optional `data_cache\` back to empty.

## Safety Review Questions

Answer before declaring the package ready:

1. Does default config prevent orders?
2. Does demo mode require both CLI `--mode demo_trade` and `allow_demo_trade=true`?
3. Is REAL account hard rejected regardless of config?
4. Are generated files written under the EXE directory, not PyInstaller temp and not MT5 source folders?
5. Is the terminal/data path auto-discovered or externally configured?
6. Does the final operator folder contain exactly one runnable EXE, beside-EXE `config.ini`, and
   empty `logs\`?
7. Was the final EXE run immediately after packaging?
8. Did `check_runtime_logs_for_errors.py` or an equivalent scanner confirm no fatal/error logs?
9. Is smoke/log-check evidence stored outside the operator folder?
10. Were delivery `logs\` and optional `data_cache\` reset to empty after smoke?
11. Does order sending reconcile retcode against account state?
12. Are monitor rows marked not forward-live and not performance evidence?
13. Does startup reconcile existing positions before new signal handling?
14. Does startup scan pending orders with `orders_get()`?
15. Does startup scan recent order/deal history with `history_orders_get()` or `history_deals_get()`?
16. Does the runtime persist order intents and quarantine unknown state instead of blindly retrying?
17. Are order intents persisted atomically with SQLite transaction or temp-file + fsync + `os.replace()`?
18. Is the history query window configurable, for example `recovery_lookback_days`?
19. Does reconciliation treat MT5 broker state as authoritative and local intents as context?
20. Does matching use ticket/order/deal id as the primary key, with magic/symbol/comment only as validation?
21. Does SL/TP confirmation use tick/point tolerance instead of exact float equality?
22. Does close confirmation distinguish full close from partial close?
23. Does startup distinguish process-crash recovery from MT5 unavailable/network-disconnected recovery?
24. Are `magic_number`, `comment_prefix`, `strategy_id`, and environment/runtime identity external config values?
25. Is the MT5 comment short enough for broker truncation limits while still carrying a unique short intent id?
26. Is the post-send confirmation polling window explicitly configured?
27. Are quarantine release conditions explicit and auditable?
28. Does `logs/startup_report.csv` append one row per startup before signal scanning?
29. Does the monitor persist a signal execution ledger so the same completed signal bar cannot reopen after SL/TP closes the first position or after a runtime restart?
