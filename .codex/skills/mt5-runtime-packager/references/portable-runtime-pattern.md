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

## Dist Verification

Minimum `dist` contents:

```text
runtime.exe
config.ini
run_status.bat
run_dry_run.bat
run_demo.bat
README_RUNTIME.md
logs\
tmp\
```

Recommended docs:

```text
PACKAGING_RUNTIME_EXE_GUIDE.md
MT5_DEMO_TRADE_API.md
```

## Safety Review Questions

Answer before declaring the package ready:

1. Does default config prevent orders?
2. Does demo mode require both CLI `--mode demo_trade` and `allow_demo_trade=true`?
3. Is REAL account hard rejected regardless of config?
4. Are generated files written under the EXE directory, not PyInstaller temp and not MT5 source folders?
5. Is the terminal/data path auto-discovered or externally configured?
6. Does `run_demo.bat` reject when the demo gate is closed?
7. Does order sending reconcile retcode against account state?
8. Are monitor rows marked not forward-live and not performance evidence?
9. Does startup reconcile existing positions before new signal handling?
10. Does startup scan pending orders with `orders_get()`?
11. Does startup scan recent order/deal history with `history_orders_get()` or `history_deals_get()`?
12. Does the runtime persist order intents and quarantine unknown state instead of blindly retrying?
13. Are order intents persisted atomically with SQLite transaction or temp-file + fsync + `os.replace()`?
14. Is the history query window configurable, for example `recovery_lookback_days`?
15. Does reconciliation treat MT5 broker state as authoritative and local intents as context?
16. Does matching use ticket/order/deal id as the primary key, with magic/symbol/comment only as validation?
17. Does SL/TP confirmation use tick/point tolerance instead of exact float equality?
18. Does close confirmation distinguish full close from partial close?
19. Does startup distinguish process-crash recovery from MT5 unavailable/network-disconnected recovery?
20. Are `magic_number`, `comment_prefix`, `strategy_id`, and environment/runtime identity external config values?
21. Is the MT5 comment short enough for broker truncation limits while still carrying a unique short intent id?
22. Is the post-send confirmation polling window explicitly configured?
23. Are quarantine release conditions explicit and auditable?
24. Does `logs/startup_report.csv` append one row per startup before signal scanning?
25. Does the monitor persist a signal execution ledger so the same completed signal bar cannot reopen after SL/TP closes the first position or after a runtime restart?
