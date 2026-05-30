# 环境验证规范（Stage 9）

## 核心原则

环境验证的作用是**诊断**，不是**美化结果**。目标是理解策略在不同市场条件下的表现，找出策略擅长和不擅长的环境。禁止删除亏损环境后宣布"策略改进"。用于发现或选择 regime 规则的数据属于已消费开发数据；最终 OOS 的使用服从 `DATA_SPLIT_AND_OOS_POLICY.md`。

---

## 第一部分：必须分析的五个维度

### 维度1：ATR Regime（波动率体制）

将交易按进场时的 ATR 分组：

```python
low_atr = [t for t in trades if t.atr_at_entry < 0.5]
med_atr = [t for t in trades if 0.5 <= t.atr_at_entry < 1.0]
high_atr = [t for t in trades if t.atr_at_entry >= 1.0]

for regime, trades_group in [('low', low_atr), ('med', med_atr), ('high', high_atr)]:
    print(f"{regime} ATR: {len(trades_group)} trades")
    print(f"  Win rate: {win_rate(trades_group):.1%}")
    print(f"  Sharpe: {sharpe(trades_group):.2f}")
    print(f"  Avg R: {avg_r(trades_group):.2f}")
    print(f"  Max DD: {max_dd(trades_group):.1%}")
```

**输出示例**：
```
Low ATR (<0.5): 50 trades, win rate 35%, Sharpe 0.8, avg R +0.1
Med ATR (0.5-1.0): 120 trades, win rate 52%, Sharpe 1.4, avg R +0.3
High ATR (>1.0): 64 trades, win rate 62%, Sharpe 1.8, avg R +0.4

诊断：策略在高波动环境中表现最强，低波动环境中失效
原因：RSI 信号在波动率高的环境中更容易反弹（多空双向）
```

### 维度2：Trend Regime（趋势体制）

按趋势分组，例如用 20/50/200 日均线或简单的价格方向：

```python
uptrend = [t for t in trades if t.trend_at_entry == 'UP']
downtrend = [t for t in trades if t.trend_at_entry == 'DOWN']
ranging = [t for t in trades if t.trend_at_entry == 'RANGE']

# 分析每个趋势下的表现
```

**输出示例**：
```
Uptrend: 100 trades, win rate 55%, Sharpe 1.5, avg R +0.3
Downtrend: 95 trades, win rate 42%, Sharpe 0.7, avg R +0.1
Ranging: 39 trades, win rate 48%, Sharpe 1.0, avg R +0.2

诊断：策略有明显的趋势方向性，在下降趋势中失效
原因：可能是因为 RSI oversold 在向下的市场中容易进一步下跌
```

### 维度3：Session（交易时段）

按伦敦、纽约、亚洲会话分组：

```python
london = [t for t in trades if t.session_at_entry == 'LONDON']
ny = [t for t in trades if t.session_at_entry == 'NY']
asia = [t for t in trades if t.session_at_entry == 'ASIA']
```

**输出示例**：
```
London (08:00-10:00 UTC): 80 trades, win rate 62%, Sharpe 1.9
NY (13:00-16:00 UTC): 90 trades, win rate 48%, Sharpe 1.1
Asia (22:00-06:00 UTC): 64 trades, win rate 40%, Sharpe 0.6

诊断：伦敦时段流动性最好，信号最有效
原因：伦敦早盘常见的亚洲夜盘止损被突破导致反弹
```

### 维度4：Volatility Transition（波动率切换）

识别市场从低波动率切换到高波动率的时刻，或反之：

```python
def detect_volatility_transition(atr_series):
    transitions = []
    for i in range(1, len(atr_series)):
        if atr_series[i] / atr_series[i-1] > 1.2:  # 波动率跳升 20%+
            transitions.append(i)
    return transitions

# 收集所有在 transition 附近进场的交易
transition_trades = []
for t in trades:
    if is_near_volatility_transition(t.entry_time):
        transition_trades.append(t)

print(f"Transition period: {len(transition_trades)} trades")
print(f"  Win rate: {win_rate(transition_trades):.1%}")  # 通常较低
print(f"  Sharpe: {sharpe(transition_trades):.2f}")      # 通常较差
```

**输出示例**：
```
Normal periods: 220 trades, Sharpe 1.2
Volatility transition (≤5 bars of jump): 14 trades, Sharpe -0.5

诊断：策略在波动率切换时刻表现不佳
原因：高波动率突发时，止损容易被打，信号模型失效
建议：考虑在波动率 surge 后等待 10 bars 再入场
```

### 维度5：Compression / Expansion（压缩/扩张）

用 Bollinger Bands 或 ATR 变化率识别市场的压缩和扩张：

```python
compression = [t for t in trades if t.bollinger_width_at_entry < 20]  # pips
expansion = [t for t in trades if t.bollinger_width_at_entry > 80]

print(f"Compression (<20 pips BB): {len(compression)} trades, Sharpe {sharpe(compression):.2f}")
print(f"Expansion (>80 pips BB): {len(expansion)} trades, Sharpe {sharpe(expansion):.2f}")
```

**输出示例**：
```
Compression: 35 trades, win rate 38%, Sharpe 0.5
Expansion: 85 trades, win rate 58%, Sharpe 1.6

诊断：策略在扩张时期有效，压缩时期失效
原因：压缩时 RSI 反弹幅度小，无法达到 TP
建议：仅在 BB 宽度 > 50 pips 时入场
```

---

## 第二部分：时间维度分析

### Year / Month 分解

```python
yearly_results = {}
for year in range(2020, 2026):
    year_trades = [t for t in trades if t.year == year]
    yearly_results[year] = {
        'trades': len(year_trades),
        'sharpe': sharpe(year_trades),
        'winrate': win_rate(year_trades),
        'max_dd': max_dd(year_trades)
    }

# 输出趋势
for year, result in yearly_results.items():
    print(f"{year}: Sharpe {result['sharpe']:.2f}, {result['trades']} trades")
```

**输出示例**：
```
2020: Sharpe 2.1 (35 trades) - COVID boom, high volatility
2021: Sharpe 1.3 (42 trades) - Recovery, normal conditions
2022: Sharpe 0.8 (38 trades) - Fed hiking, declining effectiveness
2023: Sharpe 1.2 (45 trades) - Stabilization
2024: Sharpe 1.1 (48 trades) - Continued decline
2025: Sharpe 0.95 (26 trades YTD) - Lowest performance

诊断：性能从 2020 开始持续下降，-55%
原因：市场可能已经适应了这个信号，或者市场结构发生变化
```

---

## 第三部分：Interaction Matrix（交互矩阵）

构建多维表格，分析不同 regime 的组合效应：

```
                   | London | NY | Asia |
                   |--------|--------|--------|
High ATR Uptrend   | 1.9S   | 1.2    | 0.8    |
High ATR Downtrend | 1.2    | 0.6    | -0.2   |
Low ATR Uptrend    | 1.0    | 0.8    | 0.5    |
Low ATR Downtrend  | 0.5    | 0.3    | 0.2    |

注：S = significant sample (>= 30)，空白 = low sample (< 30)
```

**解读**：
- 最好的环境：London + High ATR + Uptrend（Sharpe 1.9）
- 最差的环境：Asia + Low ATR + Downtrend（Sharpe 0.2）
- 推荐的过滤：仅在 London + High ATR 时入场，回避 Downtrend + Asia

---

## 第四部分：Low Sample 处理

### 定义

任何 regime 样本数 < 30，都标记为 `low_sample`。这些样本的统计结论不可靠：

```python
def mark_low_sample(results):
    for regime, stats in results.items():
        if stats['num_trades'] < 30:
            stats['low_sample'] = True
            stats['conclusion'] = 'NOT RELIABLE'
```

### 禁止用 Low Sample 构造 Filter

```
错误：
"Asia session 的胜率仅 40%，所以我加一个 filter：skip Asia"

但 Asia session 只有 12 笔交易（< 30），这个结论不可靠。
正确的做法是标记这个 regime 为 low sample，提示需要更多数据。
```

### 禁止在同一批数据上既发现 Filter 又验证 Filter

```
错误工作流：
1. 分析 2020-2024 数据，发现 "London + High ATR" 效果好
2. 立即加这个 filter 到策略中
3. 重新回测 2020-2024 数据，验证 filter 有效

这是在同一个数据集上既发现又验证，导致 look-ahead bias。

正确工作流：
1. 在 discovery_train 分析并提出 "London + High ATR" 候选
2. 在 development_validation 上筛选该候选，查看后将其记为 consumed
3. 将通过筛选的完整候选连同参数、SL/TP 和成本模型固定
4. 与 walk-forward / temporal 开发诊断都完成且候选保持不变后，才在 locked_final_holdout 上仅评价一次；失败则当前版本失败
```

---

## 第五部分：禁止的做法

### 禁止1：删除亏损 Regime 后宣布成功

```
错误：
"下降趋势中我的策略亏损，所以我加一个 filter：skip downtrend。
现在回测结果是 Sharpe 2.0！"

这是选择偏差。下降趋势本来就应该有亏损的交易。
正确的做法是接受在下降趋势中性能较差，但不删除它。

正确结论：
"我的策略在上升趋势中 Sharpe 1.5，下降趋势中 Sharpe 0.7。
这是一项已记录的风险限制。若要降低头寸或跳过下降趋势，
必须作为新版本候选经过归因、审计和未消费数据验证，不能在当前冻结/forward 版本中临时执行。"
```

### 禁止2：用很小样本构造 Filter

```
错误：
"我发现一个罕见的 regime（仅 8 笔交易）胜率 75%。
我要加一个 filter 来复制这个环境。"

这是极端过拟合。8 笔交易无法得出统计结论。

正确做法：
标记为 low sample，继续收集数据。
只有样本 >= 30，才能考虑该 regime 的特征。
```

### 禁止3：在诊断中混合不同版本的策略

```
错误：
"我用 v0.1 分析了 2020-2023 的 ATR regime，
然后用 v0.2（带 ATR filter）分析了 2024-2025 的表现。
两个版本的表现无法直接对比。"

正确做法：
用同一个版本的策略做环境诊断。
不同版本的诊断必须分开报告。
```

---

## 第六部分：环境诊断报告模板

```markdown
# Environment Validation Report for STRAT_RSI_001

## 样本总体
- 总交易数：234
- 时间跨度：2020-01-01 to 2025-05-31
- 平均每月：4.6 笔交易

## 维度1：ATR Regime
| Regime | Trades | Win% | Sharpe | MaxDD | Sample Check |
|--------|--------|------|--------|-------|--------------|
| <0.5 | 50 | 35% | 0.8 | -8% | ✓ |
| 0.5-1.0 | 120 | 52% | 1.4 | -7% | ✓ |
| >1.0 | 64 | 62% | 1.8 | -6% | ✓ |

**结论**：策略在高 ATR 环境中表现最强，低 ATR 环境中失效。

## 维度2：Trend Regime
| Regime | Trades | Win% | Sharpe | MaxDD | Sample Check |
|--------|--------|------|--------|-------|--------------|
| Uptrend | 100 | 55% | 1.5 | -8% | ✓ |
| Downtrend | 95 | 42% | 0.7 | -10% | ✓ |
| Ranging | 39 | 48% | 1.0 | -6% | ✓ |

**结论**：下降趋势中表现明显较差，但样本充足，这是真实特性。

## 维度3：Session
| Session | Trades | Win% | Sharpe | MaxDD | Sample Check |
|---------|--------|------|--------|-------|--------------|
| London | 80 | 62% | 1.9 | -5% | ✓ |
| NY | 90 | 48% | 1.1 | -8% | ✓ |
| Asia | 64 | 40% | 0.6 | -12% | ✗ LOW |

**结论**：London 和 NY 时段可信（样本 >= 30），Asia 样本略少但仍有 64 笔，可信度中等。

## 维度4：Volatility Transition
| Regime | Trades | Win% | Sharpe | Sample Check |
|--------|--------|------|--------|--------------|
| Normal periods | 220 | 49% | 1.2 | ✓ |
| 波动率跳升后 5 bars | 14 | 21% | -0.5 | ✗ LOW |

**结论**：波动率突发时表现不佳，但样本太小（14），需要更多观察。

## 维度5：Compression/Expansion
| Regime | Trades | Win% | Sharpe | Sample Check |
|--------|--------|------|--------|--------------|
| Compression | 35 | 38% | 0.5 | ✓ |
| Expansion | 85 | 58% | 1.6 | ✓ |

**结论**：压缩时期失效，扩张时期有效。

## Interaction Matrix (Sharpe)
```
                   | London | NY | Asia |
High ATR Uptrend   | 1.9 ✓  | 1.2 ✓ | 0.8 ✓ |
High ATR Downtrend | 1.2 ✓  | 0.6 ✓ | -0.2 (low) |
Low ATR Uptrend    | 1.0 ✓  | 0.8 ✓ | 0.5 (low) |
Low ATR Downtrend  | 0.5 (low) | 0.3 (low) | 0.2 (low) |
```

## Year/Month 性能衰减
| Year | Sharpe | Trades | Trend |
|------|--------|--------|-------|
| 2020 | 2.1 | 35 | 📈 Strong |
| 2021 | 1.3 | 42 | 📉 Decline |
| 2022 | 0.8 | 38 | 📉 Weak |
| 2023 | 1.2 | 45 | 📈 Recover |
| 2024 | 1.1 | 48 | 📉 Decline |
| 2025 | 0.95 | 26 (YTD) | 📉 Lowest |

**重要警告**：2023-2025 性能衰减，可能的原因：
1. 市场适应了这个信号
2. 市场结构发生了根本变化（流动性、参与者、策略改变）
3. 随机波动（需要更多样本确认）

## 关键发现
1. **最优环境**：London + High ATR + Uptrend （Sharpe 1.9）
2. **最差环境**：Asia + Low ATR + Downtrend （Sharpe 0.2）
3. **性能衰减警告**：2020 (2.1) → 2025 (0.95)，-55% 下降
4. **环境敏感性**：高度依赖环境，Sharpe 范围 0.2-1.9

## 建议与限制
1. ✓ **不建议删除任何 regime**。下降趋势和低 ATR 虽然表现差，但删除它会导致选择偏差。
2. ✓ **建议监控 2025+ 的性能**。如果衰减继续，可能表示市场结构变化。
3. ✓ **建议在高 ATR + London 时段重点关注**。这是最强的环境。
4. ✗ **不建议加"skip downtrend" filter**。虽然下降趋势表现差，但这是真实市场特性，不是 bug。
5. ✗ **不建议加"skip Asia session" filter**。样本足够（64），性能差是真实的，不是噪音。

## 诊断结论
策略对市场环境的敏感性较高。在最优环境中非常有效（1.9），在最差环境中基本失效（0.2）。
这表明策略捕捉的是特定市场条件下的模式（高波动率反弹），而不是普遍规律。
前向运行中应该监控当前市场环境，并与冻结时的风险预期对比；除预先冻结的规则或单独记录的安全暂停外，不得临时调整头寸或决定跳过原本应执行的信号。
如果整体性能衰减趋势加速，应暂停/退役当前版本或创建新版本研究，而非污染当前 forward 记录。
```

---

## 总结

环境验证的核心是**理解**而非**优化**。通过对不同市场条件的系统分析，我们能够：
1. 确定策略的最优运作环境
2. 发现策略的风险点（如下降趋势、低波动环境）
3. 为新版本的风险管理假说或已冻结的监控阈值提供依据
4. 检测长期性能衰减的迹象

禁止通过删除亏损环境来美化结果，这是科学研究和过拟合的分界线。
