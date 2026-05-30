# 版本控制与冻结政策（Stage 11）

## 核心原则

任何进入前向交易（forward-live）的策略都必须被冻结。冻结意味着代码、参数、成交时点、SL/TP 与动态退出、头寸规模、成本模型、数据使用台账以及所有决策相关的信息都被记录和锁定，通过 Git tag 和版本号绑定，确保可追溯性和重复性。具体退出/风险清单见 `EXIT_RISK_AND_LOGIC_REFINEMENT_STANDARD.md`，IS/OOS 证据分类见 `DATA_SPLIT_AND_OOS_POLICY.md`。

---

## 第一部分：版本号规范

### 版本号格式

采用语义化版本控制（Semantic Versioning）：`v<major>.<minor>.<patch>`

- `major`：策略的重大改变（信号引擎根本改写、规则完全改变）
- `minor`：策略的功能性改进（增加新 filter、调整参数）
- `patch`：修复（bug 修复、数据清理）

### 版本号示例

```
v0.1        第一个发布版本（第一次通过 Stage 11 冻结）
v0.2        增加 ATR filter 后的版本
v0.3        调整 RSI 参数后的版本
v1.0        完整重写后的版本
v1.1        在 v1.0 基础上的改进
```

### 首个发布版本通常是 v0.1

除非策略已经有大量历史版本，否则第一次冻结应该使用 v0.1，表示"第一个生产级别的版本"。

---

## 第二部分：冻结内容详细清单

### 代码冻结

必须冻结以下文件的代码：

1. **signal_engine.py**：信号生成逻辑
   - 冻结指标：代码 hash、commit hash、代码行数
   - 示例：`sha256(signal_engine.py) = abc123...`

2. **backtest.py**：交易执行逻辑
   - 冻结指标：代码 hash、commit hash
   - 确保回测框架不会改变

3. **analysis/ 中的诊断脚本**：如果有正式使用的脚本

**禁止修改**：一旦冻结，这些文件不能修改。任何修改都必须新建版本。

### 参数冻结

必须冻结 config.yaml 中的所有参数：

```yaml
signal_config:
  rsi_period: 14          # 冻结
  atr_threshold: 0.8      # 冻结
  
risk_model:
  take_profit: 1.5        # 冻结
  stop_loss: 1.0          # 冻结
  
execution:
  commission: 0.001       # 冻结
  spread: 0.0002          # 冻结
```

任何参数修改（即使仅改 0.1）都必须新建版本。

### 规则冻结

必须冻结决策规则的英文表述：

```
Entry Rules:
  RSI(14) < 30 AND ATR > 0.8
  Signal confirmed on close of bar t; entry filled on first executable quote of bar t+1

Exit Rules:
  Take Profit: TP level = entry + 1.5R
  Stop Loss: SL level = entry - 1.0R
  Exit on first breach of either level
  Ambiguous OHLC bar touching both SL/TP: SL-first unless ordered tick data is stored

Conflict Rules:
  No concurrent long/short on same symbol
  Max 5 concurrent positions across portfolio
```

### 成本模型冻结

必须冻结交易成本的完整定义：

```
Bid-Ask Spread: 0.0002 (2 pips for EUR/USD)
Commission: 0.001 per round trip
Slippage: 0.00005 (0.5 pips assumed)
Swap cost: 0 (assumed neutral or included in spread)
```

### 数据范围冻结

冻结回测数据的范围：

```
Backtest start: 2020-01-01
Backtest end: 2025-05-31
Data source: OANDA daily OHLC
Data quality: Verified, no gaps
```

### 关键指标冻结

记录冻结时的关键性能指标：

```
Backtest Results (2020-2025):
  Total trades: 234
  Win rate: 48.3%
  Sharpe ratio: 1.20
  Calmar ratio: 1.5
  Max drawdown: -12%

Walk-Forward OOS Results:
  Average test Sharpe: 1.19 ± 0.04
  Parameter stability: Good (std 0.04)

Environment Validation:
  Best environment: London + High ATR
  Worst environment: Asia + Low ATR
  Applicable environments: All (good robustness)
```

---

## 第三部分：Git Tag 和分支管理

### Git Tag 规范

先将冻结 manifest 提交，再对该提交创建 Git tag 来标记冻结版本。`version.json` 不应尝试写入承载其自身的 commit hash；实际 frozen commit 由 tag 指向并登记于 registry：

```bash
# 提交冻结 manifest
git add version.json frozen_report.md data_usage_ledger.yaml
git commit -m "[FREEZE] strategy_id=STRAT_RSI_001, version=v0.1"

# 创建 annotated tag（推荐；tag 指向的 HEAD 即 frozen_commit）
git tag -a v0.1-frozen \
  -m "Stage 11 freeze: RSI oversold strategy
       Commits: signal_engine + backtest finalized
       Backtest Sharpe: 1.20 (234 trades)
       Walk-Forward OOS: 1.19 ± 0.04
       Ready for forward-live deployment"

# 推送到远程
git push origin v0.1-frozen
```

### Tag 命名规范

```
v<major>.<minor>-frozen     正式冻结的版本
v<major>.<minor>-experimental  实验版本（可选）
v<major>.<minor>-deprecated  废弃的版本（可选）
```

### Frozen Branch（可选但推荐）

创建一个冻结专用的分支，标记为只读：

```bash
# 创建 frozen 分支
git checkout -b frozen-v0.1
git push origin frozen-v0.1

# 分支保护规则（在 GitHub/GitLab 上）：
- 禁止 force push
- 禁止直接 commit（仅允许通过 PR）
- 禁止 merge 回 main 分支
```

---

## 第四部分：Version.json 的完整内容

```json
{
  "strategy_info": {
    "strategy_id": "STRAT_RSI_001",
    "strategy_name": "RSI Oversold Reversal on EUR/USD H1",
    "created_date": "2025-01-15",
    "frozen_date": "2025-06-01"
  },

  "version": {
    "major": 0,
    "minor": 1,
    "patch": 0,
    "version_string": "v0.1",
    "status": "frozen"
  },

  "code_freeze": {
    "frozen_tag": "v0.1-frozen",
    "frozen_timestamp": "2025-06-01 10:30:00 UTC",
    "frozen_branch": "frozen-v0.1",
    
    "code_hashes": {
      "signal_engine.py": "sha256:signal_abc123...",
      "backtest.py": "sha256:backtest_def456...",
      "config.yaml": "sha256:config_ghi789..."
    }
  },

  "configuration_freeze": {
    "signal_config": {
      "rsi_period": 14,
      "atr_threshold": 0.8,
      "description": "RSI(14) < 30 and ATR > 0.8"
    },
    "risk_model": {
      "take_profit": 1.5,
      "stop_loss": 1.0,
      "dynamic_exit": "none",
      "max_concurrent_trades": 5
    },
    "execution": {
      "commission": 0.001,
      "spread": 0.0002,
      "slippage": 0.00005
    }
  },

  "rules_freeze": {
    "entry_rules": "RSI(14) < 30 AND ATR > 0.8 on bar t close; fill on first executable quote of bar t+1",
    "exit_rules": "TP at 1.5R from entry, SL at 1.0R from entry",
    "collision_rules": "If OHLC bar touches SL and TP and no ordered tick data exists, SL-first",
    "conflict_rules": "No concurrent long/short same symbol, max 5 positions total",
    "cost_model": "bid_ask=0.0002, commission=0.001, slippage=0.00005"
  },

  "data_freeze": {
    "backtest_start": "2020-01-01",
    "backtest_end": "2025-05-31",
    "data_source": "OANDA",
    "timeframe": "H1",
    "symbol": "EUR/USD",
    "data_quality": "Verified, no gaps"
  },

  "forward_live_freeze": {
    "framework_start_time": "2025-06-01 11:00:00 UTC",
    "forward_branch": "forward-v0.1",
    "signal_engine_version": "0.1",
    "backtest_engine_version": "v1.0",
    "frozen_commit_for_forward": "recorded in registry from git rev-parse v0.1-frozen"
  },

  "performance_snapshot": {
    "backtest": {
      "total_trades": 234,
      "win_rate": 0.483,
      "profit_factor": 1.8,
      "expectancy": 0.25,
      "sharpe": 1.20,
      "calmar": 1.50,
      "max_drawdown": -0.12,
      "recovery_factor": 9.8
    },
    "walk_forward_oos": {
      "average_sharpe": 1.19,
      "sharpe_std": 0.04,
      "average_win_rate": 0.49,
      "parameter_stability": "Good"
    },
    "environment_validation": {
      "best_environment": "London + High ATR (Sharpe 1.9)",
      "worst_environment": "Asia + Low ATR (Sharpe 0.2)",
      "regime_sensitivity": "High"
    },
    "temporal_validation": {
      "yearly_trend": "Declining (2020: 2.1 → 2025: 0.95)",
      "performance_degradation": -55,
      "warning": "Significant performance decay, monitor closely"
    }
  },

  "freeze_checklist": {
    "code_freeze": true,
    "parameter_freeze": true,
    "rule_freeze": true,
    "data_freeze": true,
    "data_usage_ledger_frozen": true,
    "git_tag_created": true,
    "version_json_updated": true,
    "registry_updated": true,
    "forward_branch_created": true,
    "complete": true
  },

  "risk_assessment": {
    "overfitting_risk": "Low (Train-HO degradation 25%)",
    "regime_sensitivity": "High (Sharpe range 0.2-1.9)",
    "performance_decay": "Concerning (55% since 2020)",
    "sample_size": "Adequate (234 trades)"
  },

  "approvals": {
    "technical_review": {
      "reviewer": "Claude Code",
      "date": "2025-06-01",
      "status": "APPROVED",
      "comments": "All stages 1-11 complete, ready for forward-live"
    }
  },

  "changelog": {
    "v0.1": {
      "date": "2025-06-01",
      "changes": "Initial frozen version",
      "stages_complete": ["Stage 1", "Stage 2", ..., "Stage 11"]
    }
  }
}
```

---

## 第五部分：修改冻结策略的流程

### 如果需要修改冻结策略

1. **不能直接修改**：frozen-v0.1 分支上的代码不能改

2. **创建新分支**：
   ```bash
   git checkout main  # 从 main 开始
   git checkout -b feature/STRAT_RSI_001_v0.2_add_session_filter
   ```

3. **进行修改**：开发新版本，完成必要的 Stage。filter、SL/TP、动态退出或 sizing 变化必须先有 Stage 5 attribution 证据并重新执行 Stage 2 audit；若旧 final holdout 已经查看，它只能作为新版本的已知开发数据。

4. **新版本号**：
   ```json
   {
     "version": {
       "major": 0,
       "minor": 2,
       "patch": 0
     },
     "changelog": {
       "v0.2": {
         "changes": "Added session filter to improve performance",
         "parent_version": "v0.1"
       }
     }
   }
   ```

5. **新 frozen tag**：
   ```bash
   git tag -a v0.2-frozen -m "Stage 11 freeze: Added session filter"
   ```

6. **新 forward 分支**：
   ```bash
   git switch --detach v0.2-frozen
   git switch -c forward-v0.2
   ```

### 禁止做法

- ❌ 在 frozen-v0.1 分支上直接修改代码
- ❌ 改变既有的 frozen tag（tags 是不可变的）
- ❌ 混合 v0.1 和 v0.2 的 forward 数据
- ❌ 在 forward-v0.1 上改参数或规则

---

## 第六部分：策略版本的生命周期

```
      Stage 1-6
         ↓
    [Hypothesis]
         ↓
      Stage 7-8
         ↓
    [Optimization & Walk-Forward]
         ↓
      Stage 9-10
         ↓
    [Environment & Temporal Validation]
         ↓
     Stage 11
         ↓
[FROZEN] ← v0.1-frozen (Git tag created)
         ↓
     Stage 12
         ↓
[FORWARD-LIVE] ← forward-v0.1 (New branch created)
         ↓
(Pass Gate A or B)
         ↓
    [DEPLOYED]
         ↓
(Performance monitoring)
         ↓
(If degradation or improvement needed)
         ↓
Create v0.2 branch → [Repeat from Stage 6+]
```

---

## 第七部分：Forward-Live 中的版本约束

一旦策略进入 forward-live（Stage 12）：

1. **冻结版本不变**：forward-v0.1 永远基于 v0.1-frozen
2. **新信号来自冻结代码**：运行 commit a1b2c3d4 的 signal_engine.py
3. **新交易遵循冻结规则**：使用 config.yaml v0.1 的参数
4. **新数据只追加**：不修改历史交易数据
5. **通过 Gate 后评估**：如果要改进，创建 v0.2

---

## 总结

版本冻结的目的是确保可追溯性和重复性。通过 Git tag、version.json 和分支管理，每个策略版本都能被精确定位和重现。这是防止"不知道哪个版本赚钱"这类问题的唯一方式。
