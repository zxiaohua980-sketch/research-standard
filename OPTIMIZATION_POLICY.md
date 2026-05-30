# 参数优化政策（Stage 7）

## 核心原则

参数优化不是找最高夏普，而是检验逻辑假说在参数空间上的稳健性。禁止盲目扫参、禁止全样本优化、禁止只报告最优结果。目标是找到一个"平台"而非一个"峰值"——即参数在一个合理的范围内都能保持一致的性能。所有数据命名与使用还必须服从 `DATA_SPLIT_AND_OOS_POLICY.md`；本文中的 `Validation` 指 `development_validation`，`Holdout` 指未曾用于接受 filter 或挑选参数的 `locked_final_holdout`。

---

## 第一部分：优化前的协议编写

在开始任何参数搜索之前，必须编写 `optimization_protocol.md`，明确说明搜索范围、评分函数、数据分割等。这不仅约束优化过程，也为后续的审计留下记录。

### 必须包含的内容

```markdown
# Optimization Protocol for STRAT_RSI_001

## 目标
检验 ATR filter 对不同参数的鲁棒性，找到使 Sharpe 稳定且高效的参数组合

## 搜索空间
- ATR_threshold: [0.6, 0.7, 0.8, 0.9, 1.0]
- RSI_period: [12, 14, 16, 18]
- TP_ratio: [1.3, 1.5, 1.7, 2.0]
- SL_ratio: [0.8, 1.0, 1.2]

总组合数：5 * 4 * 3 * 3 = 180

## 评分函数
Primary: Sharpe ratio (risk-adjusted return)
Secondary: Calmar ratio (recovery speed)
Tertiary: Sortino ratio (downside volatility)
Constraints: Must have >= 30 trades per parameter set

## 数据分割（Time-Series Split）
- discovery_train: 2020-01-01 to 2023-12-31 (~140 trades)
- development_validation: 2024-01-01 to 2024-12-31 (~50 trades)
- locked_final_holdout: 2025-01-01 to 2025-05-31 (~40 trades, sealed)

时间上严格不重叠，避免过拟合。

## 流程
1. 在 discovery_train 上尝试所有 180 个参数组合
2. 记录每个组合的 IS 指标
3. 在 development_validation 上评估性能并选择最终候选；查看后将该集合登记为 consumed development data
4. 固定所有规则、SL/TP、成本模型与参数
5. 若 Stage 8-10 仍将作为候选门槛，保持 locked_final_holdout sealed；开发诊断全部完成后才评价一次（不能调参或补规则）

## 禁止操作
- 不允许在 development_validation 上搜索新参数，也不允许在 locked_final_holdout 上做任何选择（这会污染最终 OOS）
- 不允许反复运行，每次看 OOS 结果后调参
- 不允许只报告最优参数，必须报告全部 180 个结果
- 不允许删除某些参数组合的结果（即使很差）

## 预期输出
1. 所有 180 个参数组合的 Sharpe、Calmar、样本数
2. Parameter plateau 分析（参数周围是否平稳）
3. IS / OOS-Dev / OOS-Final 的一致性检验和数据消费台账
4. 最终建议的参数和风险评估
```

---

## 第二部分：禁止的优化方式

### 禁止1：全样本优化

```python
# ❌ 错误做法
all_sharpe = []
for atr in [0.6, 0.7, 0.8, 0.9, 1.0]:
    for rsi in [12, 14, 16, 18]:
        # 在全部数据 2020-2025 上优化
        backtest_result = run_backtest(all_data, atr, rsi)
        all_sharpe.append((atr, rsi, backtest_result.sharpe))

best_params = max(all_sharpe, key=lambda x: x[2])  # 最高 Sharpe

# 这会导致：
# 1. 参数被优化到整个数据的特殊特征
# 2. 无法评估样本外表现
# 3. 无法测试过拟合程度
```

### 禁止2：看着 OOS 结果反复调参

```python
# ❌ 错误做法
for iteration in range(10):
    # 训练集优化
    best_params = optimize_on_train()
    
    # 测试集评估
    oos_result = evaluate_on_oos()
    
    if oos_result.sharpe < 1.0:
        # 看到 OOS 结果不好，就调整参数
        adjust_search_space()
        # 重新优化，这会导致 OOS 污染
    
    print(f"Iteration {iteration}: OOS Sharpe = {oos_result.sharpe}")
```

### 禁止3：搜索空间无限扩大

```python
# ❌ 错误做法
# 第一轮：ATR [0.6, 1.0], Sharpe 最好的是 0.8
# 看到 0.8 附近效果好，就扩大搜索空间：

for atr in [0.70, 0.72, 0.74, 0.76, 0.78, 0.80, 0.82, 0.84, 0.86]:
    # 微调参数，寻求更优结果
    # 但这实际上是在反复优化同一个数据集
    # 参数会越来越 over-fitted
```

### 禁止4：只报告最优结果

```python
# ❌ 错误做法
"根据优化结果，最优参数是 ATR=0.8, RSI=14, TP=1.5, SL=1.0，Sharpe=1.45"

# 隐瞒了：
# - 其他 179 个参数组合的结果
# - 参数周围是否有平台（鲁棒性）
# - Train/Validation/Holdout 的一致性
# - 是否过拟合了
```

### 禁止5：忽视参数平台

```python
# ❌ 错误做法
# 参数 ATR 的 Sharpe 结果：
ATR = 0.6:  Sharpe = 1.10
ATR = 0.7:  Sharpe = 1.25
ATR = 0.8:  Sharpe = 1.45  ← 选这个（最高）
ATR = 0.9:  Sharpe = 1.20
ATR = 1.0:  Sharpe = 0.95

# 问题：0.8 处有一个峰值，但周围都比较低
# 这意味着参数非常敏感，小改动就会差很多
# 在实盘中，市场条件变化会导致 ATR 漂移，性能急剧下降

# ✓ 正确做法
# 应该选择 ATR=0.7 或 0.8，这两个都稳定在 1.25+
# 或者选择一个"平台"，比如接受 ATR 在 0.7-0.9 之间都可以
```

---

## 第三部分：正确的优化流程

### 步骤1：编写优化协议与数据消费台账

在 `optimization_protocol.md` 中明确搜索空间和数据分割，并创建或更新 `data_usage_ledger.yaml`。如果 `development_validation` 已在 Stage 5 用于筛选 filter，必须记录它已消费，不得称为 final holdout。

### 步骤2：在训练集上网格搜索

```python
def optimize_on_train():
    results = []
    
    for atr in [0.6, 0.7, 0.8, 0.9, 1.0]:
        for rsi in [12, 14, 16, 18]:
            for tp in [1.3, 1.5, 1.7, 2.0]:
                for sl in [0.8, 1.0, 1.2]:
                    # 仅在训练集上运行回测
                    backtest = run_backtest(
                        data=train_set,  # 2020-2023
                        params={'ATR': atr, 'RSI': rsi, 'TP': tp, 'SL': sl}
                    )
                    results.append({
                        'atr': atr, 'rsi': rsi, 'tp': tp, 'sl': sl,
                        'train_sharpe': backtest.sharpe,
                        'train_trades': backtest.num_trades,
                        'train_calmar': backtest.calmar
                    })
    
    return results  # 返回全部 180 个结果
```

### 步骤3：过滤无效结果

```python
# 移除样本数太少的参数组合
valid_results = [r for r in results if r['train_trades'] >= 30]

# 例如：
# - ATR=1.0 + TP=2.0：只有 15 笔交易 → 移除
# - ATR=0.6 + RSI=18：只有 25 笔交易 → 移除
# - 剩余 160 个有效组合
```

### 步骤4：评估验证集性能

```python
# 对训练集上有效的每个参数，在验证集上评估
for result in valid_results:
    params = {
        'ATR': result['atr'],
        'RSI': result['rsi'],
        'TP': result['tp'],
        'SL': result['sl']
    }
    
    validation = run_backtest(
        data=validation_set,  # 2024 only
        params=params
    )
    
    result['val_sharpe'] = validation.sharpe
    result['val_trades'] = validation.num_trades
    result['val_calmar'] = validation.calmar
```

### 步骤5：选择最优参数

```python
# 基于 train + validation 的综合表现
# （注意：还不能看 locked_final_holdout！）

# 方法1：两个集合 Sharpe 都最高的参数
best_by_sharpe = max(
    valid_results,
    key=lambda r: r['train_sharpe'] + r['val_sharpe']
)

# 方法2：Calmar 最高（恢复速度更好）
best_by_calmar = max(
    valid_results,
    key=lambda r: r['train_calmar'] + r['val_calmar']
)

# 选择综合最好的（通常是 Sharpe 最高的）
selected_params = best_by_sharpe
print(f"Selected: ATR={selected_params['atr']}, RSI={selected_params['rsi']}")
print(f"Train Sharpe: {selected_params['train_sharpe']:.2f}")
print(f"Validation Sharpe: {selected_params['val_sharpe']:.2f}")
```

### 步骤6：所有开发诊断完成后，最终在 Locked Final Holdout 上评价

```python
# 这是第一次也是唯一一次看 locked_final_holdout！
# 前提：全部 entry/exit/risk/cost/parameter 已固定，且 Stage 8-10 的开发诊断已完成
holdout = run_backtest(
    data=locked_final_holdout,  # sealed until this line
    params=selected_params
)

print(f"Holdout Sharpe: {holdout.sharpe:.2f}")
print(f"Holdout Trades: {holdout.num_trades}")

# 比较：
# Train: 1.45 → Validation: 1.25 → Holdout: 1.10
# 这个衰减模式是正常的（每一步都减少但合理）

# 如果 OOS-Final 接近 OOS-Dev（例如 1.20），说明历史证据较一致
# 如果 OOS-Final 远低于 OOS-Dev（例如 0.80），当前版本失败；不能在该数据上修补
```

---

## 第四部分：Parameter Plateau 和 Local Robustness

### Parameter Plateau 检查

完整的结果应该看起来像这样：

```
ATR影响分析（固定其他参数为最优）：

ATR | Train Sharpe | Val Sharpe | HO Sharpe | Trades
----|------|---------|---------|--------
0.6 | 1.10 | 0.95    | 0.88    | 180
0.7 | 1.25 | 1.15    | 1.05    | 160
0.8 | 1.45 | 1.25    | 1.10    | 154 ← 最高
0.9 | 1.20 | 1.10    | 1.00    | 120
1.0 | 0.95 | 0.85    | 0.78    | 80

观察：
✓ 0.7-0.8 形成一个"平台"，Sharpe 都在 1.2 以上
✓ 最高值在 0.8，但 0.7 也只低 0.2
✓ 超过 0.9 就开始下降，说明 ATR 上限应该在 0.8-0.9
✓ 这表明参数有一定的鲁棒性，不是孤立的峰值
```

### Local Robustness 检查

```python
selected_atr = 0.8
selected_rsi = 14

# 检查周围参数是否也有好表现
neighbors = [
    (0.7, 14), (0.8, 14), (0.9, 14),  # ATR 邻域
    (0.8, 12), (0.8, 14), (0.8, 16),  # RSI 邻域
]

for atr, rsi in neighbors:
    result = find_result(results, atr, rsi)
    print(f"ATR={atr}, RSI={rsi}: Sharpe {result['train_sharpe']:.2f}")

# 如果邻域内都是 1.4+，说明参数很稳健
# 如果邻域内有 0.8，说明参数很敏感，容易过拟合
```

---

## 第五部分：优化报告的输出

完整的优化报告应该包含以下部分：

```markdown
# Parameter Optimization Report for STRAT_RSI_001

## 搜索协议
- 搜索空间：ATR [0.6-1.0], RSI [12-18], TP [1.3-2.0], SL [0.8-1.2]
- 总组合数：180
- 有效组合数（>= 30 trades）：160

## 最优参数
ATR_threshold = 0.8
RSI_period = 14
TP_ratio = 1.5
SL_ratio = 1.0

## 性能对比
| Metric | IS / discovery_train | OOS-Dev / development_validation | OOS-Final / locked_final_holdout | 解读 |
|--------|-------|------------|---------|------|
| Sharpe | 1.45 | 1.25 | 1.10 | 正常衰减，无过拟合迹象 |
| Calmar | 1.88 | 1.52 | 1.35 | 一致 |
| Trades | 154 | 98 | 52 | 样本充足 |
| Win% | 58.0 | 55.0 | 54.0 | 一致 |

## Parameter Plateau 分析
ATR 参数在 0.7-0.9 范围内都有 1.2+ 的 Sharpe，显示良好的鲁棒性。
0.8 是最优，但 0.7 和 0.9 也可接受（差异 < 0.15）

## Local Robustness
邻域内 8 个参数组合的 Sharpe 都在 1.3+ (train)，最坏的也有 1.15 (val)
结论：参数鲁棒性好，不是孤立峰值

## 风险评估
- 参数敏感性：中等（ATR 变化 ±0.1 导致 Sharpe ±0.15）
- 过拟合风险：低（Train-HO 衰减仅 25%）
- 样本充足性：充足（locked final holdout 有 52 笔交易）
- 数据台账：development_validation 已消费；locked_final_holdout 仅评价一次

## 建议
Stage 8-10 的开发诊断若尚未完成，保持 locked_final_holdout sealed；诊断完成且候选不变后，再把这组参数提交一次性 OOS-Final 门槛
```

---

## 第六部分：常见优化错误及改正

| 错误 | 现象 | 改正 |
|------|------|------|
| 全样本优化 | OOS-Final 与开发结果异常不一致 | 使用 time-series split，不让 locked final holdout 参与选择 |
| 搜索空间过小 | 最优参数在搜索空间边界 | 扩大搜索空间，直到最优参数在中间 |
| 参数敏感过高 | 最优参数周围都比较差 | 考虑选择"平台"参数而非峰值 |
| 样本太少 | 某些参数组合只有 <30 笔交易 | 在优化前过滤掉低交易数的参数 |
| 反复看 OOS 调参 | OOS 结果越来越好，训练集越来越差 | 明确约定：OOS 只评估，不参与搜索 |

---

## 总结：优化的目的

参数优化的目的不是为了找到 Sharpe = 2.0 的参数，而是为了：
1. **验证逻辑假说的稳健性**：参数在合理范围内都有效
2. **减少参数的随意性**：参数不是凭直觉选的，而是数据驱动
3. **量化过拟合风险**：通过 IS/OOS-Dev/OOS-Final 对比，明确看到过拟合程度
4. **建立信心基础**：前向验证时，参数已经过充分测试

如果优化后的参数性能只比固定规则好 5-10%，这不意味着优化"失败"——反而说明原始规则已经相当鲁棒。如果优化导致 Sharpe 翻倍，反而需要警惕过拟合的可能性。
