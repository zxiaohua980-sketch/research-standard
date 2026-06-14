# 策略开发快速指南

## 🚀 5 分钟快速开始

### 你的目标
想要开发一个新策略，从假说到实盘。

### 快速路线图

```
Day 1: 假说 → 第一次回测
├─ 读 README.md（1 分钟）
├─ 读 CLAUDE.md 十三大禁区（3 分钟）
├─ 读 STRATEGY_DEVELOPMENT_STANDARD.md 建立目录（2 分钟）
└─ 开始写策略（30 分钟）

Week 1-2: 审计 → 归因
├─ 读 RESEARCH_WORKFLOW.md Stage 2（审计）
├─ 读 TRADE_ATTRIBUTION_STANDARD.md（最关键）
└─ 分析你的交易（3-5 天）

Week 3-4: 优化 → 验证
├─ 读 OPTIMIZATION_POLICY.md
├─ 读 REGIME_VALIDATION_STANDARD.md
└─ 跑各种诊断（3-5 天）

Week 5: 冻结 → 前向
├─ 读 VERSIONING_AND_FREEZE_POLICY.md
├─ 读 FORWARD_VALIDATION_STANDARD.md
└─ 开始前向交易（持续）
```

---

## 第一步：建立项目（30 分钟）

### 1.1 创建策略目录

按照 STRATEGY_DEVELOPMENT_STANDARD.md 的结构创建目录：

```powershell
# 创建项目目录
mkdir D:\MT5\openclaw\STRAT_RSI_001
cd D:\MT5\openclaw\STRAT_RSI_001

# 初始化 Git
git init
git config user.name "Your Name"
git config user.email "your@email.com"

# 创建 .gitignore（复制 strategy_double_bottom 的 .gitignore）
# 或从 STRATEGY_DEVELOPMENT_STANDARD.md 参考创建

# 创建目录结构
mkdir tests
mkdir analysis
mkdir output
```

### 1.2 创建基本文件

**README.md**（参考 RESEARCH_WORKFLOW.md Stage 0）
```markdown
# STRAT_RSI_001 - RSI Oversold Reversal

## 基本信息
- strategy_id: STRAT_RSI_001
- signal: RSI < 30 on H1 close
- market: EUR/USD
- timeframe: H1

## 开发阶段
- [ ] Stage 0: Registration
- [ ] Stage 1: Hypothesis
- [ ] Stage 2: Execution Audit
- ...
```

**signal_engine.py**（参考 STRATEGY_DEVELOPMENT_STANDARD.md）
```python
class SignalEngine:
    def __init__(self, config):
        self.rsi_period = config['rsi_period']
    
    def generate_signal(self, bars_data, bar_index):
        # 只生成信号，不涉及交易逻辑
        pass
```

**backtest.py**（参考 STRATEGY_DEVELOPMENT_STANDARD.md）
```python
class BacktestEngine:
    def __init__(self, config, signals):
        self.signals = signals
    
    def run_full_backtest(self, historical_data):
        # 只执行交易，不改信号定义
        pass
```

**config.yaml**
```yaml
strategy:
  id: STRAT_RSI_001
  symbol: EUR/USD
  timeframe: H1

signal_config:
  type: RSI
  rsi_period: 14
  threshold: 30

risk_model:
  stop_loss: 1.0
  take_profit: 1.5
  max_concurrent: 5
```

### 1.3 第一次 commit

```powershell
git add .
git commit -m "[INIT] strategy_id=STRAT_RSI_001, hypothesis=RSI_oversold_reversal"
```

---

## 第二步：写假说（30 分钟）

### 参考文档
- **RESEARCH_WORKFLOW.md Stage 1**（必读，5 分钟）
- **README.md**（最后回顾）

### 你需要回答的四个问题

**问题1：一句话假说是什么？**
```
例如: "RSI < 30 表示超卖，未来 5-20 bar 内反弹概率 > 50%"
```

**问题2：市场微观结构证据是什么？**
```
例如: "过度卖出导致流动性缺失，市场参与者争夺便宜筹码导致反弹"
（不能只说"历史数据显示有效"）
```

**问题3：该信号的正期望来自什么？**
```
例如: "波动率均值回归，而非趋势延续"
```

**问题4：预期交易频率**
```
例如: "EUR/USD H1 预期每月 20-30 笔"
```

### 记录在文件中

在 README.md 或新建 `hypothesis.md` 中写下这四个答案。

### Commit

```powershell
git add hypothesis.md README.md
git commit -m "[STAGE] strategy_id=STRAT_RSI_001, action=hypothesis

一句话假说：RSI oversold reversal
市场基础：过度卖出导致反弹
期望频率：EUR/USD H1 每月 20-30 笔"
```

---

## 第三步：回测与审计（1-2 天）

### 参考文档
- **RESEARCH_WORKFLOW.md Stage 2**（必读，10 分钟）
- **RESEARCH_WORKFLOW.md Stage 4**（参考）
- **STRATEGY_DEVELOPMENT_STANDARD.md**（参考）
- **EXIT_RISK_AND_LOGIC_REFINEMENT_STANDARD.md**（涉及成交或 SL/TP 时必读）

### 关键约束（在开始前务必读 CLAUDE.md）

❌ **禁止**：
1. 用全样本 (2020-2025) 调参
2. 看结果后改规则
3. 使用未来数据（入场后用当日 high/low 止损）
4. 把策略逻辑混在回测脚本里

✅ **必须做**：
1. 检查前视偏差（data leakage）
2. 验证费用模型（spread、commission）
3. 确认没有无限持仓
4. 保存完整的交易明细

### 执行步骤

```python
# signal_engine.py：信号在 bar_index 收盘完成后才已知
def generate_signal(self, bars_data, bar_index):
    # 关键：生成信号不能用 bar_index+1 的数据
    rsi = calculate_rsi(bars_data['close'][:bar_index+1])  # 对
    if rsi[-1] < 30:
        return {'type': 'LONG', 'signal_bar': bar_index}
    return None

# backtest.py
def run_backtest(self, historical_data, signals):
    trades = []
    for bar_index, bar in enumerate(historical_data):
        signal = signals[bar_index]
        if signal and bar_index + 1 < len(historical_data):
            # bar-close 信号最早在下一根 bar 的首个可成交报价成交
            next_bar = historical_data[bar_index + 1]
            entry_price = executable_ask(next_bar['open'])  # LONG 用 ask；SHORT 用 bid
            sl = entry_price - 100 * self.atr  # 必须由订单提交时已知信息计算
            tp = entry_price + 150 * self.atr
            trade = execute_trade(entry_price, sl, tp, bar_index + 1, collision_policy='sl_first')
            trades.append(trade)
    return trades
```

### 审计检查清单

完成回测后，生成 `execution_audit.md`：

```markdown
# Execution Audit for STRAT_RSI_001

## Data Leakage and Execution Check
- [ ] 信号使用的信息在订单提交时已经可见
- [ ] bar-close 信号按下一根 bar 的首个可成交 bid/ask 入场
- [ ] SL/TP 在成交时即可计算，同 bar 冲突使用预声明的保守或有序数据规则

## Fee Model
- Bid-ask: 0.0002 (验证合理)
- Commission: 0.001 per round trip
- Slippage: 0 (保守)

## Sample
- Total trades: 150
- Open positions at end: 0
- Data range: 2020-01-01 to 2025-05-31

## Conclusion: PASS / FAIL
```

### Commit

```powershell
git add backtest.py execution_audit.md trades_detail.csv
git commit -m "[AUDIT] strategy_id=STRAT_RSI_001, action=audit-fix

执行审计通过

- 总交易数：150
- Sharpe: 1.2
- 无前视偏差"
```

---

## 第四步：交易赢亏归因（2-3 天）✨ 最重要

### 参考文档
- **TRADE_ATTRIBUTION_STANDARD.md**（必读，20 分钟）
- **DATA_SPLIT_AND_OOS_POLICY.md**（必读，明确数据是否已消费）
- **EXIT_RISK_AND_LOGIC_REFINEMENT_STANDARD.md**（涉及出场或风险规则时必读）
- **RESEARCH_WORKFLOW.md Stage 5**（参考）

### 为什么这么关键？

归因是决定"是否加新 filter"的唯一根据。如果你看到亏损交易并想加 filter，**必须先做归因**。

### 具体步骤

#### 步骤1：计算每笔交易的属性

```python
# analysis/trade_attribution.py
import pandas as pd

trades = pd.read_csv('trades_detail.csv')

# 添加特征列
trades['pnl_R'] = (trades['pnl'] / trades['risk_amount'])
trades['MFE_R'] = (trades['max_favorable'] / trades['risk_amount'])
trades['MAE_R'] = (trades['max_adverse'] / trades['risk_amount'])
trades['atr_at_entry'] = ...  # 从 historical_data 查询
trades['trend_at_entry'] = ...  # 计算过去 20 bar 方向
trades['session_at_entry'] = ...  # 根据时间判断

trades.to_csv('trades_with_features.csv')
```

#### 步骤2：对比 Winners vs Losers

```python
winners = trades[trades['pnl_R'] > 0]
losers = trades[trades['pnl_R'] <= 0]

print(f"胜率: {len(winners) / len(trades) * 100:.1f}%")
print(f"\nWinners 平均 ATR: {winners['atr_at_entry'].mean():.3f}")
print(f"Losers 平均 ATR: {losers['atr_at_entry'].mean():.3f}")
print(f"\nWinners 平均 MFE: {winners['MFE_R'].mean():.2f}R")
print(f"Losers 平均 MFE: {losers['MFE_R'].mean():.2f}R")
```

#### 步骤3：评估候选 filter

假设你发现：
- **发现**: winners 的 ATR 平均 0.85，losers 的 ATR 平均 1.20
- **假设**: 低 ATR 环境胜率低

**评估七层检验**（参考 TRADE_ATTRIBUTION_STANDARD.md）：

| 检验 | 标准 | 你的结果 | 通过？ |
|------|------|---------|-------|
| 1. 入场前可见 | ATR 在 entry bar 时已知 | ✓ | ✅ |
| 2. 样本数 | >= 30 笔 | 低 ATR 50 笔 | ✅ |
| 3. 减少亏损 | 亏损笔数下降 | 58 笔 → 25 笔 | ✅ |
| 4. 误杀赢利 | < 30% | 误杀 18% | ✅ |
| 5. 年份稳定 | 所有年份都有效 | 2020-2024 都是 +5pp | ✅ |
| 6. Regime 稳健 | 不同市场条件都有效 | 高/低 ATR 都改善 | ✅ |
| 7. OOS-Dev 验证 | development_validation 上也有效 | +4pp (vs +5pp discovery_train) | ✅ |

**通过七层检验 → 可以作为 Stage 6 候选；locked final holdout 仍不可查看**

### 生成报告

创建 `trade_attribution_report.md`，包含：
- Winners vs Losers 对比表格
- 候选 filter 的七层评估
- 最终建议（接受/拒绝）

### Commit

```powershell
git add analysis/trade_attribution.py trade_attribution_report.md
git commit -m "[ATTRIB] strategy_id=STRAT_RSI_001, action=attribution

交易赢亏归因完成，发现 ATR filter 有效

- 低 ATR (< 0.5): 胜率 35%
- 高 ATR (> 1.0): 胜率 62%
- 差异显著，建议加 ATR > 0.8 filter"
```

---

## 第五步：逻辑优化与参数优化（3-5 天）

### 参考文档
- **OPTIMIZATION_POLICY.md**（必读，15 分钟）
- **DATA_SPLIT_AND_OOS_POLICY.md**（必读，10 分钟）
- **RESEARCH_WORKFLOW.md Stage 6 & 7**（参考）

### 关键约束

❌ **禁止**：
1. 全样本优化（2020-2025 一起）
2. 看结果后反复调参
3. 搜索空间无限扩大
4. 只报告最优结果

✅ **必须做**：
1. 分成 discovery_train / development_validation / locked_final_holdout，并写入 `data_usage_ledger.yaml`
2. 在 discovery_train 上搜参，development_validation 筛选后记为 consumed；完成后续环境与时间开发诊断且候选不变后，才打开 locked final holdout 一次
3. 输出全部候选参数，不只最优
4. 检查参数鲁棒性（周围参数是否也好）

### 执行步骤

#### 步骤1：编写优化协议

```markdown
# optimization_protocol.md

## 搜索空间
- ATR_threshold: [0.6, 0.8, 1.0]
- RSI_period: [12, 14, 16]
- TP_ratio: [1.5, 2.0]
- SL_ratio: [0.8, 1.0]

总组合数: 3 * 3 * 2 * 2 = 36

## 数据分割
- discovery_train (IS): 2020-2023
- development_validation (OOS-Dev): 2024
- locked_final_holdout (OOS-Final, sealed): 2025
```

#### 步骤2：网格搜索

```python
# analysis/optimize_params.py
results = []
for atr in [0.6, 0.8, 1.0]:
    for rsi in [12, 14, 16]:
        for tp in [1.5, 2.0]:
            for sl in [0.8, 1.0]:
                # 在 TRAIN 集上跑
                train_result = backtest(train_data, params)
                # 在 VALIDATION 集上评估
                val_result = backtest(val_data, params)
                
                results.append({
                    'atr': atr, 'rsi': rsi, 'tp': tp, 'sl': sl,
                    'train_sharpe': train_result.sharpe,
                    'val_sharpe': val_result.sharpe,
                    'trades': train_result.num_trades
                })

results_df = pd.DataFrame(results)
results_df.to_csv('optimization_results.csv')
```

#### 步骤3：保留最终门槛，待环境与时间诊断完成后执行

```python
# 下方只能在第六步开发诊断完成、且候选没有变化后运行一次！
best_params = select_one_fixed_candidate(results_df, protocol='predeclared_is_oos_dev_score')
holdout_result = backtest(locked_final_holdout, best_params)

print(f"IS Sharpe: {best_params['train_sharpe']:.2f}")
print(f"OOS-Dev Sharpe: {best_params['val_sharpe']:.2f}")
print(f"OOS-Final Sharpe: {holdout_result.sharpe:.2f}")
```

### Commit

```powershell
git add analysis/optimize_params.py optimization_results.csv
git commit -m "[OPTIM] strategy_id=STRAT_RSI_001, action=optimize-params

参数优化完成

- 搜索空间：36 个组合
- 最优参数：ATR=0.8, RSI=14, TP=1.5, SL=1.0
- IS Sharpe: 1.45 → OOS-Dev: 1.25
- OOS-Final: sealed，待 Stage 8-10 开发诊断完成后一次性评价
- 参数鲁棒性：好（周围参数也 1.3+）"
```

---

## 第六步：环境与时间诊断（2-3 天）

本步仅使用已消费的开发历史，排除 `locked_final_holdout`。诊断完成且候选规则、参数、SL/TP、成本均未改变后，才执行上一步所示的一次性 OOS-Final 评价。

### 参考文档
- **REGIME_VALIDATION_STANDARD.md**（必读，10 分钟）
- **RESEARCH_WORKFLOW.md Stage 9 & 10**（参考）

### 快速检查清单

```python
# 按 ATR regime 分层
low_atr = trades[trades['atr_at_entry'] < 0.5]
high_atr = trades[trades['atr_at_entry'] > 1.0]
print(f"Low ATR 胜率: {(low_atr['pnl_R'] > 0).mean():.1%}")
print(f"High ATR 胜率: {(high_atr['pnl_R'] > 0).mean():.1%}")

# 按年份分层
for year in [2020, 2021, 2022, 2023, 2024, 2025]:
    year_trades = trades[trades['year'] == year]
    sharpe = calculate_sharpe(year_trades['pnl_R'])
    print(f"{year}: Sharpe {sharpe:.2f} ({len(year_trades)} trades)")

# 按 session 分层
for session in ['London', 'NY', 'Asia']:
    session_trades = trades[trades['session'] == session]
    print(f"{session}: 胜率 {(session_trades['pnl_R'] > 0).mean():.1%}")
```

### 重要：不要删除亏损环境！

❌ 错误：
```
"发现下降趋势中胜率只有 42%，所以我加个 filter skip downtrend
现在 Sharpe 提升到 1.8 了！"
```

✅ 正确：
```
"环境诊断显示：
- 上升趋势中 Sharpe 1.5
- 下降趋势中 Sharpe 0.7
这说明策略有趋势方向性，在下降趋势中期望要调低。
不删除下降趋势，只是知道这个限制。"
```

### Commit

```powershell
git add analysis/regime_validation.py regime_validation_report.md
git commit -m "[REGIME] strategy_id=STRAT_RSI_001, action=regime-validation

环境诊断完成

- 高 ATR: Sharpe 1.8
- 低 ATR: Sharpe 0.8
- 伦敦时段: Sharpe 1.9
- 亚洲时段: Sharpe 0.6
- 结论: 在高波动、伦敦时段最强"
```

---

## 第七步：冻结版本（1 天）

### 参考文档
- **VERSIONING_AND_FREEZE_POLICY.md**（必读，15 分钟）
- **RESEARCH_WORKFLOW.md Stage 11**（参考）

### 执行步骤

#### 步骤1：生成 version.json

```json
{
  "strategy_id": "STRAT_RSI_001",
  "version": "v0.1",
  "frozen_tag": "v0.1-frozen",
  "frozen_timestamp": "2025-06-01 10:30:00",
  "parameters": {
    "atr_threshold": 0.8,
    "rsi_period": 14,
    "tp_ratio": 1.5,
    "sl_ratio": 1.0
  },
  "backtest_sharpe": 1.2,
  "oos_final_sharpe": 1.1,
  "framework_start_time": "2025-06-01 11:00:00"
}
```

#### 步骤2：创建 Git tag

```powershell
git add version.json frozen_report.md data_usage_ledger.yaml
git commit -m "[FREEZE] strategy_id=STRAT_RSI_001, version=v0.1

冻结版本 v0.1 - RSI oversold strategy

- Backtest Sharpe: 1.2 (150 trades)
- OOS-Final Sharpe: 1.1 (30 trades)
- 所有验证通过
- 准备进入 forward-live"

git tag -a v0.1-frozen -m "Frozen version v0.1: ready for forward-live"
# git rev-parse HEAD 的 frozen_commit 记录到 registry/tag 注释，而非回填修改 frozen commit
```

#### 步骤3：创建 forward-live 分支

```powershell
git switch --detach v0.1-frozen
git switch -c forward-v0.1
# 创建 forward_live_config.yaml 和 forward_live_state.json（参考 FORWARD_VALIDATION_STANDARD.md）
git add forward_live_config.yaml forward_live_state.json
git commit -m "[FORWARD] strategy_id=STRAT_RSI_001, action=forward-live-init"
```

---

## 第八步：前向交易（持续）

### 参考文档
- **FORWARD_VALIDATION_STANDARD.md**（必读，15 分钟）
- **RESEARCH_WORKFLOW.md Stage 12**（参考）

### 核心约束

🚨 **一旦进入 forward-live，禁止**：
- 修改 signal_engine.py
- 改参数
- 改规则
- 混入历史回填
- 把 kill switch、人工平仓或安全暂停混写为冻结策略的自然表现

✅ **只能做**：
- 追加新信号（新数据）
- 追加新交易（新执行）
- 记录性能
- 评估 Gate 进度

### 监控流程

```python
# forward_live_runner.py
while True:
    # 每小时或每天运行一次
    new_signal = signal_engine.generate_signal(latest_data)
    if new_signal:
        log_signal(new_signal)
    
    # 检查已平仓交易
    closed_trades = check_closed_positions()
    for trade in closed_trades:
        log_trade(trade)
    
    # 评估 Gate 进度
    if len(all_trades) >= 30 and time_elapsed >= 3_months:
        print("✓ Gate A pass - 3 months + 30 trades")
    if len(all_trades) >= 50:
        print("✓ Gate B pass - 50 trades")
    
    # 对比回测
    forward_sharpe = calculate_sharpe(all_forward_trades)
    backtest_sharpe = 1.2
    if abs(forward_sharpe - backtest_sharpe) > 0.3:
        print("⚠️ Warning: forward performance deviates > 30%")
```

### 定期 Commit

```powershell
# 每周或每 10 笔交易
git add forward_live_trades.csv forward_live_signals.csv forward_live_state.json
git commit -m "[FORWARD] strategy_id=STRAT_RSI_001, action=forward-live

新增 10 笔信号，3 笔交易

- Gate A 进度: 25/30
- 当月收益: +1.2%
- Forward Sharpe: 1.1 (vs backtest 1.2)"
```

---

## 📚 各个阶段的推荐阅读顺序

| 阶段 | 优先文档 | 次要文档 | 预计时间 |
|------|----------|----------|---------|
| **初始化** | README.md, CLAUDE.md 十三大禁区 | GIT_AND_REPRODUCIBILITY_STANDARD.md | 30 min |
| **开发环境** | STRATEGY_DEVELOPMENT_STANDARD.md | GIT_AND_REPRODUCIBILITY_STANDARD.md | 1 day |
| **假说** | RESEARCH_WORKFLOW.md Stage 1 | README.md | 30 min |
| **审计** | RESEARCH_WORKFLOW.md Stage 2 | STRATEGY_DEVELOPMENT_STANDARD.md | 1 day |
| **事件研究** | RESEARCH_WORKFLOW.md Stage 3 | - | 1 day |
| **固定规则** | RESEARCH_WORKFLOW.md Stage 4 | - | 1 day |
| **赢亏归因** ⭐ | TRADE_ATTRIBUTION_STANDARD.md | RESEARCH_WORKFLOW.md Stage 5 | 2-3 days |
| **逻辑优化** | RESEARCH_WORKFLOW.md Stage 6 | - | 1 day |
| **参数优化** | OPTIMIZATION_POLICY.md | RESEARCH_WORKFLOW.md Stage 7 | 1-2 days |
| **回溯验证** | RESEARCH_WORKFLOW.md Stage 8 | - | 1 day |
| **环境诊断** | REGIME_VALIDATION_STANDARD.md | RESEARCH_WORKFLOW.md Stage 9 | 1-2 days |
| **时间诊断** | RESEARCH_WORKFLOW.md Stage 10 | - | 1 day |
| **冻结版本** | VERSIONING_AND_FREEZE_POLICY.md | RESEARCH_WORKFLOW.md Stage 11 | 1 day |
| **前向交易** | FORWARD_VALIDATION_STANDARD.md | RESEARCH_WORKFLOW.md Stage 12 | 持续 |
| **部署** | RESEARCH_WORKFLOW.md Stage 13 | PROJECT_REGISTRY_STANDARD.md | 1 day |

---

## 🎯 常见问题与规范文档的对应

| 问题 | 答案文档 | 位置 |
|------|----------|------|
| 我想新建策略，怎么开始? | STRATEGY_DEVELOPMENT_STANDARD.md | 必需的目录结构 |
| signal engine 和 backtest engine 怎么分离? | STRATEGY_DEVELOPMENT_STANDARD.md | 核心模块职责 |
| 回测数据可不可信? | RESEARCH_WORKFLOW.md Stage 2 | Execution Audit |
| 我发现了一个好的 filter，能加吗? | TRADE_ATTRIBUTION_STANDARD.md | 七层检验 |
| 怎么优化参数? | OPTIMIZATION_POLICY.md | 禁止操作 + 正确流程 |
| 环境诊断发现坏的市场条件，要删除吗? | REGIME_VALIDATION_STANDARD.md | 禁止的做法 |
| forward 数据怎么记录? | FORWARD_VALIDATION_STANDARD.md | forward_live 数据结构 |
| 如何定版本号? | VERSIONING_AND_FREEZE_POLICY.md | 版本号格式 |
| 改了策略怎么办? | VERSIONING_AND_FREEZE_POLICY.md | 修改冻结策略的流程 |
| 怎么在 GitHub 上同步? | GIT_AND_REPRODUCIBILITY_STANDARD.md | Git 工作流 |

---

## ✅ 开发检查清单

### 每天开始前
- [ ] 了解今天的任务（属于哪个 Stage）
- [ ] 读相关的规范文档（5-10 分钟）
- [ ] 检查 git status（确保 working tree clean）

### 完成每个 Stage 后
- [ ] 生成该阶段的报告 (audit.md, attribution.md 等)
- [ ] 通过该阶段的检查清单
- [ ] 提交 git commit（带明确的 [STAGE] 标签）
- [ ] 更新 version.json（记录最新状态）
- [ ] 更新 PROJECT_DISCOVERY_REPORT.md（如有）

### 进入 forward-live 前
- [ ] 所有 Stage 1-11 完成
- [ ] 所有 commit 已推送（如用 GitHub）
- [ ] 冻结的代码版本清晰（git tag）
- [ ] framework_start_time 已记录
- [ ] 团队审核通过

### 进入 forward-live 后
- [ ] 每周更新 forward_live_trades.csv
- [ ] 每月检查 Gate 进度
- [ ] 不修改 frozen 代码
- [ ] 定期 commit forward 新数据

---

## 🚀 快速模板命令

```powershell
# 新建策略快速初始化
mkdir D:\MT5\openclaw\STRAT_<NAME>_<ID>
cd D:\MT5\openclaw\STRAT_<NAME>_<ID>
git init
mkdir tests analysis output

# 创建框架文件
touch signal_engine.py backtest.py config.yaml README.md .gitignore version.json data_usage_ledger.yaml

# 第一个 commit
git add .
git commit -m "[INIT] strategy_id=STRAT_<NAME>_<ID>, hypothesis=<one_line>"

# 进入 Stage N 时
git add <modified_files>
git commit -m "[STAGE_<N>] strategy_id=STRAT_<NAME>_<ID>, action=<action>

<description>"

# 冻结版本
git tag -a v0.1-frozen -m "Frozen v0.1: <description>"

# 前向交易分支（明确从 frozen tag 派生）
git switch --detach v0.1-frozen
git switch -c forward-v0.1
```

---

**总结**：这套规范的核心是**先审计，后研究；先归因，后优化；先冻结，后前向**。文档的使用顺序就是策略开发的自然顺序。不要跳过任何环节。

祝你开发顺利！🎉
