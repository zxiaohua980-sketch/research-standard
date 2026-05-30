# 前向验证规范（Stage 12）

## 核心定义

**Forward-Live 的严格定义**：仅有 `framework_start_time` 之后新产生的信号和交易才算 forward-live。所有在此时刻之前的回测数据、历史回填、固定规则回测、walk-forward 验证都属于历史分析，不可混淆。历史样本内/外的分类还必须遵循 `DATA_SPLIT_AND_OOS_POLICY.md`；冻结的执行、SL/TP 与安全干预记录必须遵循 `EXIT_RISK_AND_LOGIC_REFINEMENT_STANDARD.md`。

---

## 第一部分：四种验证形式的区别

### 1. Historical Backfill（历史回填）

**定义**：对历史数据的完整回测，例如 2020-2025 所有数据。

**特点**：
- 知道所有市场结果（完全的 hindsight）
- 参数可能已经过度优化到这个特定数据集
- 结果包含前视偏差风险
- 不能用于证明策略有效

**用途**：
- 开发阶段的 hypothesis 验证（Stage 1-6）
- 参数优化的基础（Stage 7）

---

### 2. Fixed-Rule Backtest（固定规则回测）

**定义**：在已冻结规则和参数的前提下，对协议允许读取的历史数据进行回测，不再优化。若覆盖原先封存的 `locked_final_holdout`，该运行就是一次 OOS-Final 打开并必须记入数据消费台账，不能再重复用于调规则。

**特点**：
- 规则完全冻结，不看结果后再改
- 覆盖整个历史样本，但仍是历史数据
- 是 Stage 4 的产出

**用途**：
- 建立性能基线
- 与后续 walk-forward 和 forward-live 对比

---

### 3. Walk-Forward / Out-of-Sample（回溯时间序列）

**定义**：用滚动窗口，在训练段上选参数，在后续 test 段上评估。严格的时间顺序。

**特点**：
- 虽然是历史数据，但有部分 "out-of-sample" 的评估
- 模拟真实交易的时间顺序：看过去、决定参数、对未来测试
- 是 Stage 8 的产出

**用途**：
- 测试参数的时间稳定性
- 量化过拟合程度
- 模拟接近真实的交易条件

---

### 4. Forward-Live（前向交易）

**定义**：`framework_start_time` 之后新产生的信号和交易。完全未知未来，基于当时已知的信息做决策。

**特点**：
- 真实市场数据，但时间点在 framework_start_time 之后
- 回测时完全不知道这段数据的结果
- 最接近真实交易的条件
- 唯一能真正验证策略有效性的方式

**用途**：
- 验证策略在真实未知市场中的表现
- 检验 backtest 结果是否真实可信
- 决定是否可以扩展到实盘交易

---

## 第二部分：Framework Start Time 的定义

### 什么是 Framework Start Time？

Framework start time 是一个固定的时刻，标志着"历史分析"和"前向验证"的分界线。这个时刻之前的所有数据用于开发（backtest、optimization、environment validation），这个时刻之后的数据用于前向验证。

### 如何设置 Framework Start Time？

1. **选择合理的时刻**：通常在完成 Stage 11（冻结）时设置。例如：
   ```
   Strategy frozen on 2025-06-01 10:30:00 UTC
   Framework start time set to 2025-06-01 11:00:00 UTC
   (30 minutes later, to ensure no data leakage)
   ```

2. **固定后不改**：一旦设置，framework_start_time 不能改变。改变它意味着前向数据的污染。

3. **记录在 version.json**：
   ```json
   {
     "framework_start_time": "2025-06-01 11:00:00 UTC",
     "frozen_commit": "a1b2c3d4",
     "strategy_id": "STRAT_RSI_001"
   }
   ```

---

## 第三部分：Forward-Live 的严格约束

### 约束1：无回填

```
错误：
"我在 2025-06 进入 forward-live，但我想补上 2025-05 的交易。"

这是回填，违反了 framework_start_time 的原则。
2025-05 的数据应该已经在 Stage 4 的固定规则回测中了。

正确：
forward-live 数据从 2025-06-01 11:00:00 开始，之前的都不算。
```

### 约束2：信号来自冻结代码

```
正确的做法：
1. Stage 11 冻结：commit a1b2c3d4，tag v0.1-frozen
2. Stage 12 前向：
   - git checkout v0.1-frozen (checkout 到冻结的代码)
   - 运行 signal_engine.py，该代码来自 commit a1b2c3d4
   - 记录新信号和新交易
   - 定期 commit 新数据到 forward-v0.1 分支

错误的做法：
在 develop 分支上直接添加 forward 数据（develop 中代码可能已修改）
```

### 约束3：没有参数调整

```
冻结版本的 config.yaml：
ATR_threshold = 0.8
RSI_period = 14
TP_ratio = 1.5
SL_ratio = 1.0

前向运行时，这些参数固定不变。
不允许看到前向结果不好就改参数。
任何参数调整都要新建版本。
```

### 约束4：没有规则调整

```
冻结版本的规则：
Entry: RSI < 30 and ATR > 0.8
Exit: TP at 1.5R or SL at 1.0R

前向运行时，规则固定。
不允许看到太多亏损就加 filter。
任何规则调整都要新建版本。
```

此处的规则包括成交时点、SL、TP、breakeven、trailing、timeout、partial exit、position sizing、成本模型和 exposure cap。因安全需要触发 kill switch、暂停新单或紧急减仓时，必须单独追加 `operational_interventions` 日志；被干预的表现不得静默混写成 frozen strategy 的无干预 forward 结果。

---

## 第四部分：Forward-Live 数据结构

### forward_live_config.yaml

```yaml
strategy_id: STRAT_RSI_001
version: v0.1
frozen_commit_hash: a1b2c3d4e5f6g7h8
frozen_tag: v0.1-frozen
frozen_timestamp: 2025-06-01 10:30:00 UTC

framework_start_time: 2025-06-01 11:00:00 UTC

signal_engine_version: 0.1
backtest_engine_version: v1.0

parameters:
  ATR_threshold: 0.8
  RSI_period: 14
  TP_ratio: 1.5
  SL_ratio: 1.0

entry_rules: RSI(14) < 30 and ATR > 0.8
exit_rules: TP at 1.5R or SL at 1.0R
cost_model: bid_ask=0.0002, commission=0.001

data_source: oanda
base_currency: EUR
quote_currency: USD
timeframe: H1
```

### forward_live_signals.csv

```csv
signal_time, symbol, timeframe, signal_type, signal_price, atr, rsi, trend
2025-06-01 15:30:00, EUR/USD, H1, LONG, 1.0850, 0.85, 28.5, UP
2025-06-03 09:00:00, EUR/USD, H1, LONG, 1.0820, 0.92, 27.2, UP
2025-06-05 14:15:00, EUR/USD, H1, LONG, 1.0880, 0.78, 29.1, UP
...
(仅包含 2025-06-01 11:00:00 之后的信号)
```

### forward_live_trades.csv

```csv
entry_time, entry_price, exit_time, exit_price, pnl, pnl_R, exit_reason, mfe_r, mae_r, holding_bars
2025-06-01 15:30:00, 1.0850, 2025-06-02 11:00:00, 1.0875, 25, 0.5R, take_profit, 0.6R, -0.2R, 20
2025-06-03 09:00:00, 1.0820, 2025-06-03 16:30:00, 1.0810, -10, -0.2R, stop_loss, 0.1R, -1.0R, 7
2025-06-05 14:15:00, 1.0880, 2025-06-06 08:00:00, 1.0920, 40, 0.8R, take_profit, 0.8R, -0.1R, 18
...
(仅包含 2025-06-01 11:00:00 之后的交易)
```

### forward_live_state.json

```json
{
  "current_status": "forward_live_active",
  "strategy_id": "STRAT_RSI_001",
  "version": "v0.1",
  "framework_start_time": "2025-06-01 11:00:00 UTC",
  "current_timestamp": "2025-09-15 14:30:00 UTC",
  
  "gate_status": {
    "gate_a": {
      "requirement": "3 months + 30 trades",
      "start_time": "2025-06-01",
      "current_time": "2025-09-15",
      "months_elapsed": 3.5,
      "trades_count": 35,
      "status": "PASS"
    },
    "gate_b": {
      "requirement": "50 trades",
      "trades_count": 35,
      "status": "70% (35/50)"
    }
  },
  
  "current_metrics": {
    "total_trades": 35,
    "win_rate": 0.486,
    "profit_factor": 1.8,
    "expectancy": 0.18,
    "sharpe": 0.95,
    "max_drawdown": -0.06
  },
  
  "backtest_comparison": {
    "backtest_sharpe": 1.20,
    "forward_sharpe": 0.95,
    "difference": -0.25,
    "status": "in_line_with_expectations"
  },
  
  "last_updated": "2025-09-15 14:30:00 UTC"
}
```

### operational_interventions.csv

若发生人工或安全系统干预，必须追加记录：

```csv
timestamp,intervention_type,reason,affected_positions,authorization,notes
2025-06-10 09:00:00 UTC,kill_switch,daily_loss_limit,2,human_review_required,trading_paused
```

---

## 第五部分：Gate 检查

### Gate A：3 个月 + 30 笔交易

**要求**：
- 自 framework_start_time 至少已过 3 个自然月
- 至少产生 30 笔完整交易

**检查点**：
```
Start: 2025-06-01 11:00:00
Gate A due: 2025-09-01（3 个月后）
Actual pass: 2025-09-15
Status: PASS

交易数：35
Gate A requirement: 30
Status: PASS
```

**通过标准**：
- 月份数 >= 3
- 交易数 >= 30
- forward-live 性能与 backtest 不悖离（Sharpe 下降 < 50%）

### Gate B：50 笔交易

**要求**：
- 至少产生 50 笔完整交易（不限时间）

**检查点**：
```
交易数：35 / 50 (70%)
当前速度：约 12 笔/月
预计达成：2025-12 左右
```

**通过标准**：
- 交易数 >= 50
- forward-live 性能与 backtest 保持一致

---

## 第六部分：完整性检查脚本

每次添加新数据到 forward-live，运行完整性检查：

```python
def forward_live_integrity_check(trades, signals, config):
    """验证 forward-live 数据的完整性和纯度"""
    
    # 1. 时间范围检查
    framework_start = parse_datetime(config['framework_start_time'])
    for signal in signals:
        assert signal['time'] >= framework_start, f"Signal before framework start: {signal['time']}"
    for trade in trades:
        assert trade['entry_time'] >= framework_start, f"Trade before framework start: {trade['entry_time']}"
    
    # 2. 规则一致性检查
    frozen_rules = load_frozen_rules(config['frozen_commit_hash'])
    for signal in signals:
        # 验证信号是否遵循冻结的规则
        assert is_consistent_with_rules(signal, frozen_rules)
    
    # 3. 参数一致性检查
    frozen_params = load_frozen_params(config['frozen_commit_hash'])
    for signal in signals:
        # 验证信号使用的参数是否与冻结参数一致
        assert signal['atr_threshold'] == frozen_params['atr_threshold']
        assert signal['rsi_period'] == frozen_params['rsi_period']
    
    # 4. 成本模型一致性检查
    frozen_costs = config['cost_model']
    for trade in trades:
        expected_pnl = calculate_pnl(trade, frozen_costs)
        assert abs(trade['pnl'] - expected_pnl) < 0.01, f"PnL mismatch: {trade['pnl']} vs {expected_pnl}"
    
    # 5. 数据连续性检查
    last_entry_time = max(t['entry_time'] for t in trades)
    assert last_entry_time <= current_time(), "Trade entry in future"
    
    # 6. 未来数据污染检查
    for trade in trades:
        exit_bar = get_bar(trade['exit_time'])
        # 验证 exit 不使用 exit_bar 之后的数据
        assert not uses_lookahead_data(trade, exit_bar)
    
    print("✓ All integrity checks passed")
```

---

## 第七部分：Forward-Live 监控规范

### 每日检查清单

```
每交易日结束后：
☐ 检查是否有新信号（forward_live_signals.csv）
☐ 检查是否有新交易结束（forward_live_trades.csv）
☐ 运行完整性检查脚本
☐ 更新 forward_live_state.json（当前指标）
☐ 如果有新完整交易，commit 到 forward-v0.1 分支

每周：
☐ 计算滚动 Sharpe（最近 10 笔交易）
☐ 计算滚动胜率（最近 20 笔交易）
☐ 对比与 backtest 期望
☐ 生成周报告

每月：
☐ 计算月度 Sharpe、胜率、最大回撤
☐ 检查是否达到 Gate A（3 个月后）
☐ 检查 forward 性能与 backtest 的偏离程度
☐ 生成月报告
☐ 评估是否需要调整头寸大小（基于回撤）

每季度：
☐ 完整评估 forward 性能
☐ 检查是否达到 Gate B（50 笔交易）
☐ 对比与 environment validation 的预期
☐ 对比与 temporal validation 的预期
☐ 生成季报告
☐ 决定是否继续、扩展还是退役策略
```

---

## 第八部分：Forward-Live 终止条件

Forward-live 可能因以下原因终止：

1. **目标达成**：
   - 通过 Gate A 或 Gate B，并通过正式评审
   - 转入实盘交易或扩展组合

2. **性能崩坏**：
   - Sharpe 跌至 < 0.3
   - 连续 20 笔亏损
   - 单月回撤 > 25%

3. **规则违反**：
   - 发现 forward 数据污染（包含 framework_start_time 前的数据）
   - 发现代码版本不匹配（使用的代码不是冻结版本）
   - 发现参数被调整

4. **策略失效**：
   - 市场结构改变，信号失效
   - 监管变化，无法继续交易
   - 成本模型改变（经纪商费用上升）

---

## 总结

Forward-live 是检验策略是否真实有效的唯一方式。它基于完全真实的、从未见过的市场数据，回测时无法预知结果，最接近真实交易条件。通过严格的时间分割和完整性检查，forward-live 数据的纯度得到保证。只有通过 Gate A 或 Gate B，并且性能与 backtest 一致的策略，才能有信心转入实盘交易。
