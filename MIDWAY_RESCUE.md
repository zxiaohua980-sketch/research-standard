# 🆘 已开发一半的策略救援指南

## 第一步：诊断当前进度（30 分钟）

### 快速自检清单

在你的策略目录中，看看有没有以下文件：

#### Stage 1-4 检查
```
□ hypothesis.md / README 中有假说      → Stage 1 完成?
□ execution_audit.md                   → Stage 2 完成?
□ event_study_report.md                → Stage 3 完成?
□ trades_detail.csv (完整交易明细)     → Stage 4 完成?
```

#### Stage 5-7 检查
```
□ trade_attribution_report.md           → Stage 5 完成?
□ logic_refinement.md                  → Stage 6 完成?
□ optimization_protocol.md             → Stage 7 完成?
□ optimization_results.csv             → Stage 7 完成?
```

#### Stage 8-11 检查
```
□ walk_forward_report.md               → Stage 8 完成?
□ regime_validation_report.md          → Stage 9 完成?
□ temporal_validation_report.md        → Stage 10 完成?
□ version.json + git tag               → Stage 11 完成?
```

#### Stage 12-13 检查
```
□ forward_live_trades.csv              → Stage 12 开始?
□ forward_live_config.yaml             → Stage 12 开始?
□ version.json (framework_start_time)  → Stage 12 配置?
```

---

### 根据情况判断（选一项）

**情况A: "我有回测结果，但没有做过审计"**
→ 跳到 **方案A**

**情况B: "我有回测结果，也做过一些分析，但不确定是否规范"**
→ 跳到 **方案B**

**情况C: "我有回测和分析，但还没优化"**
→ 跳到 **方案C**

**情况D: "我已经优化过，但不确定是否过拟合"**
→ 跳到 **方案D**

**情况E: "我已经准备好冻结和前向"**
→ 跳到 **方案E**

---

## 方案A：有回测，缺少审计（最常见）

### 症状
- ✓ 有 backtest.py，能跑回测
- ✓ 有 trades 数据和 CSV
- ✗ 没有 execution_audit.md
- ✗ 不确定是否有前视偏差
- ? Sharpe 看起来很好，怀疑是否真实

### 救援步骤（1 天）

#### 步骤1：读文档（30 min）
打开 **RESEARCH_WORKFLOW.md Stage 2: Execution Audit**，了解要检查什么。

#### 步骤2：逐项检查（1-2 小时）

**检查清单 1：数据前视**
```python
# 在你的 signal_engine 中检查：
def generate_signal(self, bars_data, bar_index):
    # ✅ 对：只用到 bar_index 的数据
    rsi = calculate_rsi(bars_data['close'][:bar_index+1])
    
    # ❌ 错：用了 bar_index 的 high/low（未来数据）
    if bars_data.iloc[bar_index]['high'] > xxx:  # 不能用当日 high！
```

**检查清单 2：费用模型**
```
你的 backtest 中设置了吗：
□ Spread (bid-ask): _______ (例如 0.0002)
□ Commission: _______ (例如 0.001)
□ Slippage: _______ (例如 0)

这些值合理吗：
□ EUR/USD H1 spread 0.1-0.3 pips → 0.001-0.003
□ Commission 0.1% → 0.001
□ Slippage 0.5-1 pips → 0.00005-0.0001
```

**检查清单 3：入场止损**
```python
# 你的代码中：
# 如果信号在 bars[bar_index] 收盘后才确认，最早按下一根可成交报价入场
entry_price = executable_ask(bars[bar_index + 1]['open'])  # ✅ LONG；SHORT 用 bid
stop_loss = entry_price - 100 * atr     # ✅ 基于下单时已知数据

# ❌ 不能这样：
stop_loss = entry_price - (bars[bar_index]['low'])  # 用了当日 low！
```

**检查清单 4：样本末端**
```python
# 检查是否有未平仓的交易：
open_trades = trades[trades['exit_time'].isna()]
if len(open_trades) > 0:
    print(f"警告：有 {len(open_trades)} 笔未平仓交易")
    print("需要移除或标记为 'open position'")
```

#### 步骤3：生成审计报告

创建 `execution_audit.md`：

```markdown
# Execution Audit for [STRAT_NAME]

## Data Leakage Check
- RSI 基于前一根 bar? ✓ YES / ✗ NO
- Entry 使用当日 high/low? ✗ NO / ✓ YES (错误!)
- 止损在 entry bar 设置? ✓ YES / ✗ NO

## Fee Model Verification
- Spread: 0.0002 (合理 for EUR/USD)
- Commission: 0.001 (合理)
- Slippage: 0 (保守估计)

## Sample Integrity
- Total trades: 150
- Open positions at end: 0
- Data range: 2020-01-01 to 2025-05-31

## Issues Found
- [ ] 无问题，通过审计 → PASS
- [ ] 发现前视偏差 → FIX
- [ ] 发现费用模型问题 → FIX
```

#### 步骤4：如果发现问题

**问题1：有前视偏差**
```python
# 修复：改为前一根 bar 的数据
rsi = calculate_rsi(bars_data['close'][:bar_index])  # 不包括当日

# 重新跑回测
trades = backtest(historical_data)

# Commit
git add execution_audit.md signal_engine.py
git commit -m "[AUDIT] strategy_id=STRAT_XXX, action=audit-fix

修复前视偏差，RSI 改为前一根 bar 计算

- 之前 Sharpe: X.X
- 现在 Sharpe: Y.Y"
```

**问题2：费用模型错误**
```python
# 修复费用模型
commission = 0.001  # 添加正确的佣金
spread = 0.0002     # 添加正确的点差

# 重新计算
pnl = (exit_price - entry_price) * size - commission
```

#### 步骤5：Commit

```powershell
git add execution_audit.md
git commit -m "[AUDIT] strategy_id=STRAT_XXX, action=audit

执行审计完成 - PASS

- 无前视偏差
- 费用模型合理
- 样本完整（150 笔交易）"
```

✅ **现在你完成了 Stage 2！继续进入方案B。**

---

## 方案B：有回测，但缺少规范的归因分析

### 症状
- ✓ 有 execution_audit.md (或审计通过)
- ✓ 有交易数据
- ✗ 没有 trade_attribution_report.md
- ✗ 想加某些 filter 但不确定是否合理
- ? 胜率不稳定，不知道原因

### 救援步骤（2-3 天）

#### 步骤1：读文档（1 小时）
打开 **TRADE_ATTRIBUTION_STANDARD.md**，重点看：
- "每笔交易必须记录的属性"
- "七层检验"

#### 步骤2：丰富交易数据（2-3 小时）

你的 `trades_detail.csv` 现在有什么列：

```
❓ 现有列（常见）：
entry_time, entry_price, exit_time, exit_price, pnl, pnl_percent

✅ 应该添加的列：
pnl_R (以 R 为单位)
MFE_R (最大有利)
MAE_R (最大不利)
atr_at_entry (波动率)
trend_at_entry (趋势)
session_at_entry (时段)
```

**补充数据的代码**：

```python
import pandas as pd
from datetime import datetime

trades = pd.read_csv('trades_detail.csv')
historical_data = pd.read_csv('historical_ohlc.csv')

# 添加 pnl_R
risk_per_trade = 100  # 你的 SL 距离，单位 pips
trades['pnl_R'] = trades['pnl'] / (risk_per_trade * pip_value)

# 添加 MFE/MAE
for idx, trade in trades.iterrows():
    entry_time = trade['entry_time']
    exit_time = trade['exit_time']
    entry_price = trade['entry_price']
    
    # 从 historical_data 中找这段时间的高/低
    period_data = historical_data[
        (historical_data['timestamp'] >= entry_time) & 
        (historical_data['timestamp'] <= exit_time)
    ]
    
    max_high = period_data['high'].max()
    max_low = period_data['low'].min()
    
    trades.at[idx, 'MFE_R'] = (max_high - entry_price) / (risk_per_trade * pip_value)
    trades.at[idx, 'MAE_R'] = (max_low - entry_price) / (risk_per_trade * pip_value)

# 添加环境特征
def get_atr_at_time(timestamp):
    # 从 historical_data 中查询对应时间的 ATR
    pass

trades['atr_at_entry'] = trades['entry_time'].apply(get_atr_at_time)
trades['session_at_entry'] = trades['entry_time'].dt.hour.apply(lambda h: 
    'London' if 8 <= h < 10 else 
    'NY' if 13 <= h < 16 else 
    'Asia'
)

trades.to_csv('trades_detail_enhanced.csv')
```

#### 步骤3：生成归因报告（1-2 小时）

创建 `trade_attribution_analysis.py`：

```python
import pandas as pd

trades = pd.read_csv('trades_detail_enhanced.csv')

# 对比 Winners vs Losers
winners = trades[trades['pnl_R'] > 0]
losers = trades[trades['pnl_R'] <= 0]

print(f"胜率: {len(winners) / len(trades) * 100:.1f}%")
print(f"平均赢: {winners['pnl_R'].mean():.2f}R")
print(f"平均亏: {losers['pnl_R'].mean():.2f}R")

print(f"\nATR 对比:")
print(f"Winners 平均 ATR: {winners['atr_at_entry'].mean():.3f}")
print(f"Losers 平均 ATR: {losers['atr_at_entry'].mean():.3f}")

print(f"\nSession 对比:")
for session in ['London', 'NY', 'Asia']:
    session_trades = trades[trades['session_at_entry'] == session]
    wr = (session_trades['pnl_R'] > 0).mean()
    print(f"{session}: 胜率 {wr:.1%} ({len(session_trades)} 笔)")
```

运行后，你会发现：
```
胜率: 48.3%
平均赢: +1.8R
平均亏: -0.9R

ATR 对比:
Winners 平均 ATR: 0.85
Losers 平均 ATR: 1.20

Session 对比:
London: 胜率 62.0% (80 笔)
NY: 胜率 48.0% (90 笔)
Asia: 胜率 40.0% (64 笔)
```

#### 步骤4：写归因报告

创建 `trade_attribution_report.md`：

```markdown
# Trade Attribution Report for [STRAT_NAME]

## 整体统计
- 总交易数: 234
- 胜率: 48.3%
- 平均赢: +1.8R
- 平均亏: -0.9R
- 期望值: +0.25R per trade

## Winners vs Losers

### ATR 特征
| Group | Avg ATR | Win% | Trades |
|-------|---------|------|--------|
| Low ATR (<0.5) | 0.35 | 35% | 50 |
| Mid ATR (0.5-1.0) | 0.75 | 52% | 120 |
| High ATR (>1.0) | 1.20 | 62% | 64 |

**发现**: 低 ATR 环境胜率仅 35%，高 ATR 环境 62% → **ATR filter 候选**

### Session 特征
| Session | Win% | Trades |
|---------|------|--------|
| London | 62% | 80 |
| NY | 48% | 90 |
| Asia | 40% | 64 |

**发现**: 伦敦时段显著更好 → **Session filter 候选**

## 候选 Filter 评估

### 候选1: ATR > 0.8
通过七层检验:
- [✓] 入场前可见
- [✓] 样本数 >= 30 (64 笔)
- [✓] 减少亏损 (60笔 → 25笔)
- [✓] 误杀赢利 < 30% (18%)
- [✓] 年份稳定 (所有年份 +5-8pp)
- [✓] Regime 稳健 (高低波动都改善)
- [ ] OOS-Dev 验证（用于筛选候选；locked final holdout 保持封存）

**结论: ACCEPT - 进入 Stage 6 开发**

### 候选2: Session = London
通过七层检验:
- [✓] 入场前可见
- [✗] 样本数 >= 30 (80 笔 OK，但移除 154 笔)
- [✓] 减少亏损
- [✗] 误杀赢利 > 30% (35% - 太多)
- [ ] 年份稳定 (待检验)

**结论: REJECT - 代价太高（失去 65% 交易）**
```

#### 步骤5：Commit

```powershell
git add trade_attribution_analysis.py trade_attribution_report.md trades_detail_enhanced.csv
git commit -m "[ATTRIB] strategy_id=STRAT_XXX, action=attribution

交易赢亏归因完成

- 发现 ATR filter 有效（胜率 35% → 62%）
- 发现 Session 差异（London 62%, Asia 40%）
- 评估候选 filter，ATR > 0.8 通过七层检验，推荐加入"
```

✅ **现在你完成了 Stage 5！如果有候选 filter，继续方案C。**

---

## 方案C：已做归因，想要优化

### 症状
- ✓ 有 execution_audit.md + trade_attribution_report.md
- ✓ 有候选 filter
- ✗ 还没正式优化
- ? 不确定怎么优化才不会过拟合

### 救援步骤（2-3 天）

#### 步骤1：读文档（30 min）
打开 **OPTIMIZATION_POLICY.md**，重点看"禁止的优化方式"和"正确流程"。

#### 步骤2：准备数据（30 min）

**数据分割**（时间顺序，绝对不能乱）：

```python
import pandas as pd

trades = pd.read_csv('trades_detail_enhanced.csv')
trades['date'] = pd.to_datetime(trades['entry_time']).dt.date

# 分割数据
train_end = '2023-12-31'
val_end = '2024-12-31'

train = trades[trades['date'] <= train_end]  # 60% (2020-2023)
val = trades[(trades['date'] > train_end) & (trades['date'] <= val_end)]  # 20% (2024)
locked_final_holdout = trades[trades['date'] > val_end]  # OOS-Final (2025)，保持 sealed

print(f"IS discovery_train: {len(train)} ({len(train)/len(trades)*100:.0f}%)")
print(f"OOS-Dev development_validation: {len(val)} ({len(val)/len(trades)*100:.0f}%)")
print(f"OOS-Final locked_final_holdout: {len(locked_final_holdout)} ({len(locked_final_holdout)/len(trades)*100:.0f}%)")
```

#### 步骤3：写优化协议

创建 `optimization_protocol.md`：

```markdown
# Optimization Protocol for [STRAT_NAME]

## 目标
检验候选 filter (ATR > 0.8) 的有效性

## 搜索空间（仅用于当前候选）
- ATR_threshold: [0.6, 0.7, 0.8, 0.9, 1.0]
- RSI_period: [12, 14, 16]

总组合数: 5 * 3 = 15

## 评分函数
Primary: Sharpe ratio
Secondary: Calmar ratio
Constraint: Trades >= 20

## 数据分割
- discovery_train (IS): 2020-2023 (只在这上面搜参!)
- development_validation (OOS-Dev): 2024 (筛选后即 consumed)
- locked_final_holdout (OOS-Final): 2025 (完整候选固定后才打开一次!)
```

#### 步骤4：网格搜索

```python
results = []

for atr_threshold in [0.6, 0.7, 0.8, 0.9, 1.0]:
    for rsi_period in [12, 14, 16]:
        # ← 只在 TRAIN 上搜参!
        train_trades = apply_params(
            train, 
            atr_threshold=atr_threshold, 
            rsi_period=rsi_period
        )
        train_sharpe = calculate_sharpe(train_trades['pnl_R'])
        
        # → 在 VAL 上评估（不搜参，只评估!)
        val_trades = apply_params(
            val, 
            atr_threshold=atr_threshold, 
            rsi_period=rsi_period
        )
        val_sharpe = calculate_sharpe(val_trades['pnl_R'])
        
        results.append({
            'atr': atr_threshold,
            'rsi': rsi_period,
            'train_sharpe': train_sharpe,
            'val_sharpe': val_sharpe,
            'train_trades': len(train_trades),
            'val_trades': len(val_trades)
        })

results_df = pd.DataFrame(results)
results_df.to_csv('optimization_results.csv')

# 选择最优
best = results_df.loc[results_df['train_sharpe'].idxmax()]
print(f"Best params: ATR={best['atr']}, RSI={best['rsi']}")
print(f"Train Sharpe: {best['train_sharpe']:.2f}")
print(f"Val Sharpe: {best['val_sharpe']:.2f}")
```

#### 步骤5：Stage 8-10 开发诊断完成后，最后在 Locked Final Holdout 上评价

```python
# 仅在 walk-forward/regime/temporal 的开发诊断完成、候选不变后运行一次
best_params = best.to_dict()

holdout_trades = apply_params(
    locked_final_holdout,
    atr_threshold=best_params['atr'],
    rsi_period=best_params['rsi']
)
holdout_sharpe = calculate_sharpe(holdout_trades['pnl_R'])

print(f"Train Sharpe: {best['train_sharpe']:.2f}")
print(f"Val Sharpe: {best['val_sharpe']:.2f}")
print(f"OOS-Final Sharpe: {holdout_sharpe:.2f}")

# 评价
if abs(holdout_sharpe - best['val_sharpe']) < 0.2:
    print("✓ OOS-Final 结果接近 OOS-Dev，历史证据一致")
else:
    print("⚠️ OOS-Final 大幅下降，当前版本失败；不能在该集合上补丁")
```

#### 步骤6：写优化报告和 Commit

```markdown
# Optimization Report for [STRAT_NAME]

## 最优参数
- ATR_threshold: 0.8
- RSI_period: 14

## 性能对比
| 集合 | Sharpe | Trades | Win% |
|------|--------|--------|------|
| Train | 1.45 | 154 | 58% |
| Val | 1.25 | 98 | 56% |
| OOS-Final | 1.10 | 52 | 54% |

## 解释
- Train → Val: 下降 0.2 (14%) → 轻微过拟合
- OOS-Dev → OOS-Final: 下降 0.15 (12%) → 作为最终一次评价记录
- 参数鲁棒性: 中等（周围参数也 1.3+）

## 结论: PASS - 参数合理；若本报告已包含 OOS-Final，则 Stage 8-10 只能排除 holdout 做只读诊断，不得修改当前版本
```

```powershell
git add optimization_protocol.md optimization_results.csv optimization_report.md
git commit -m "[OPTIM] strategy_id=STRAT_XXX, action=optimize-params

参数优化完成

- 搜索空间: 15 个组合
- 最优参数: ATR=0.8, RSI=14
- IS Sharpe: 1.45 → OOS-Final: 1.10 (最终一次评价已消费)
- 参数鲁棒性: 好"
```

✅ **现在你完成了 Stage 7！继续方案D。**

---

## 方案D：已优化，但需要充分验证

### 症状
- ✓ 有优化结果
- ✗ 没做过 walk-forward 或环境诊断
- ? 不确定优化结果是否真实可用
- ! Sharpe 看起来很好，怀疑过拟合

### 救援步骤（3-5 天）

#### 步骤1：回溯时间序列验证（1-2 天）

打开 **RESEARCH_WORKFLOW.md Stage 8**

```python
# Walk-Forward 验证
import pandas as pd

trades = pd.read_csv('trades_detail_enhanced.csv')

# 定义滚动窗口 (12个月训练 + 3个月测试)
windows = [
    ('2020-01-01', '2020-12-31', '2021-01-01', '2021-03-31'),
    ('2020-04-01', '2021-03-31', '2021-04-01', '2021-06-30'),
    # ... 继续
]

results = []
for train_start, train_end, test_start, test_end in windows:
    # 在 train 窗口上优化参数
    train_data = trades[(trades['date'] >= train_start) & (trades['date'] <= train_end)]
    best_params = optimize_on(train_data)  # 自动找最优参数
    
    # 在 test 窗口上评估
    test_data = trades[(trades['date'] >= test_start) & (trades['date'] <= test_end)]
    test_result = evaluate_with(test_data, best_params)
    
    results.append({
        'window': window_num,
        'best_atr': best_params['atr'],
        'best_rsi': best_params['rsi'],
        'train_sharpe': train_result['sharpe'],
        'test_sharpe': test_result['sharpe'],
        'test_trades': len(test_data)
    })

results_df = pd.DataFrame(results)
print(results_df)

# 检查参数稳定性
print(f"\nParameter Stability:")
print(f"ATR std: {results_df['best_atr'].std():.3f}")
print(f"RSI std: {results_df['best_rsi'].std():.2f}")

# 检查 OOS 性能
print(f"\nOOS Performance:")
print(f"Test Sharpe 均值: {results_df['test_sharpe'].mean():.2f}")
print(f"Test Sharpe 标准差: {results_df['test_sharpe'].std():.2f}")
```

#### 步骤2：环境诊断（1-2 天）

打开 **REGIME_VALIDATION_STANDARD.md**

```python
# 五维度分析
trades = pd.read_csv('trades_detail_enhanced.csv')

print("1. ATR Regime:")
for atr_range, label in [
    ((0, 0.5), 'Low'),
    ((0.5, 1.0), 'Med'),
    ((1.0, 999), 'High')
]:
    subset = trades[
        (trades['atr_at_entry'] >= atr_range[0]) & 
        (trades['atr_at_entry'] < atr_range[1])
    ]
    wr = (subset['pnl_R'] > 0).mean()
    sharpe = calculate_sharpe(subset['pnl_R'])
    print(f"  {label}: {len(subset)} trades, WR {wr:.1%}, Sharpe {sharpe:.2f}")

print("\n2. Trend Regime:")
for trend in ['up', 'down', 'range']:
    subset = trades[trades['trend_at_entry'] == trend]
    wr = (subset['pnl_R'] > 0).mean()
    sharpe = calculate_sharpe(subset['pnl_R'])
    print(f"  {trend}: {len(subset)} trades, WR {wr:.1%}, Sharpe {sharpe:.2f}")

print("\n3. Session:")
for session in ['London', 'NY', 'Asia']:
    subset = trades[trades['session_at_entry'] == session]
    wr = (subset['pnl_R'] > 0).mean()
    sharpe = calculate_sharpe(subset['pnl_R'])
    print(f"  {session}: {len(subset)} trades, WR {wr:.1%}, Sharpe {sharpe:.2f}")

print("\n4. Year/Month:")
for year in trades['year'].unique():
    subset = trades[trades['year'] == year]
    sharpe = calculate_sharpe(subset['pnl_R'])
    print(f"  {year}: Sharpe {sharpe:.2f}")

print("\n5. Rolling 50-Trade Window:")
for i in range(0, len(trades) - 50, 50):
    window = trades.iloc[i:i+50]
    sharpe = calculate_sharpe(window['pnl_R'])
    wr = (window['pnl_R'] > 0).mean()
    print(f"  Trades {i}-{i+50}: Sharpe {sharpe:.2f}, WR {wr:.1%}")
```

#### 步骤3：生成完整报告

创建 `walk_forward_report.md` 和 `regime_validation_report.md`

#### 步骤4：Commit

```powershell
git add walk_forward_report.md regime_validation_report.md
git commit -m "[WF+REGIME] strategy_id=STRAT_XXX, action=validation

回溯验证 + 环境诊断完成

- WF OOS Sharpe: 1.19 ± 0.04 (一致性好)
- 参数稳定性: ATR std 0.04 (稳定)
- 最优环境: London + High ATR (Sharpe 1.9)
- 弱点环境: Asia + Low ATR (Sharpe 0.3)
- 性能衰减: 2020 (2.1) → 2025 (0.95) 需要警惕"
```

✅ **现在你完成了 Stage 8-10！继续方案E。**

---

## 方案E：已充分验证，准备冻结和前向

### 症状
- ✓ 所有验证都完成了
- ✓ 对性能满意
- ✗ 还没冻结版本
- ✗ 没有开始 forward-live

### 救援步骤（1 天）

#### 步骤1：生成 version.json

打开 **VERSIONING_AND_FREEZE_POLICY.md**，创建 `version.json`：

```json
{
  "strategy_id": "STRAT_XXX",
  "version": "v0.1",
  "frozen_tag": "v0.1-frozen",
  "frozen_timestamp": "2025-06-01 10:30:00",
  
  "configuration": {
    "atr_threshold": 0.8,
    "rsi_period": 14,
    "stop_loss": 1.0,
    "take_profit": 1.5
  },
  
  "performance_snapshot": {
    "backtest_sharpe": 1.2,
    "backtest_trades": 234,
    "oos_sharpe": 1.1,
    "oos_trades": 52
  },
  
  "framework_start_time": "2025-06-01 11:00:00"
}
```

#### 步骤2：创建 Git tag

```powershell
git add version.json
git commit -m "[FREEZE] strategy_id=STRAT_XXX, version=v0.1

冻结版本 v0.1

- Backtest Sharpe: 1.2 (234 trades)
- OOS Sharpe: 1.1 (52 trades)
- 所有验证通过
- 准备进入 forward-live"

git tag -a v0.1-frozen -m "Frozen v0.1: ready for forward-live"
```

#### 步骤3：创建 forward-live 分支和配置

```powershell
git switch --detach v0.1-frozen
git switch -c forward-v0.1

# 创建 forward_live_config.yaml
# 创建 forward_live_state.json (根据 FORWARD_VALIDATION_STANDARD.md)

git add forward_live_config.yaml forward_live_state.json
git commit -m "[FORWARD] strategy_id=STRAT_XXX, action=forward-live-init

初始化 forward-live

- 基于 v0.1-frozen
- Framework start time: 2025-06-01 11:00:00
- Gate A 目标: 3 months + 30 trades
- Gate B 目标: 50 trades"
```

#### 步骤4：开始前向交易

```python
# forward_live_runner.py
while True:
    new_signal = signal_engine.generate_signal(latest_data)
    if new_signal:
        log_signal(new_signal)
        log('forward_live_signals.csv')
    
    # 检查已平仓交易
    closed = check_closed_positions()
    for trade in closed:
        log_trade(trade)
        log('forward_live_trades.csv')
    
    # 定期 commit
    if trades_count % 10 == 0:
        git_commit(f"[FORWARD] {trades_count} trades")
```

#### 步骤5：每月监控

```python
# 每月运行一次
forward_trades = pd.read_csv('forward_live_trades.csv')

print(f"Gate A 进度: {len(forward_trades)}/30 trades")
print(f"Gate B 进度: {len(forward_trades)}/50 trades")
print(f"Forward Sharpe: {calculate_sharpe(forward_trades['pnl_R']):.2f}")
print(f"Forward Win%: {(forward_trades['pnl_R'] > 0).mean():.1%}")
print(f"Forward Monthly Return: {forward_trades['pnl'].sum():.2f}")

# 对比回测
print(f"\n对比回测:")
print(f"Backtest Sharpe: 1.2")
print(f"Forward Sharpe: {calculate_sharpe(forward_trades['pnl_R']):.2f}")
```

✅ **现在你已经完成了所有 13 个 Stage！**

---

## 总结：您现在的路线图

| 当前状态 | 阶段 | 文档 | 时间 |
|----------|------|------|------|
| 有回测，缺审计 | Stage 2 | RESEARCH_WORKFLOW.md S2 | 1 day |
| 缺审计+归因 | Stage 2+5 | + TRADE_ATTRIBUTION | 2-3 days |
| 缺优化 | Stage 6+7 | + OPTIMIZATION_POLICY | 2-3 days |
| 缺验证 | Stage 8-10 | + WF/REGIME/TEMPORAL | 3-5 days |
| 缺冻结 | Stage 11-12 | + VERSIONING/FORWARD | 1 day |

---

## 🆘 立刻采取行动

1. **快速自检**（上面的清单）→ 找出你在哪个阶段
2. **选择对应方案**（A/B/C/D/E）
3. **按顺序执行**
4. **每完成一个阶段就 commit**

---

## ✅ 最重要的三条原则

```
1. 先审计，后研究 (Stage 2 必须做)
2. 先归因，后优化 (Stage 5 必须做)
3. 先冻结，后前向 (Stage 11 必须做)
```

**现在就打开你的策略目录，开始救援吧！** 🚀
