# 交易赢亏归因标准（Stage 5）

## 核心思想

Trade Attribution 是整套研究流程的转折点。在这个阶段，我们停止问"策略有没有赚钱"，转而问"**为什么**赚钱或亏钱"。通过对比盈利单和亏损单的统计特征，识别成功的共同因素和失败的共同陷阱，为后续的逻辑优化提供数据支撑。没有归因，就没有根据做新增 filter，也没有根据改 SL、TP、trailing、breakeven、timeout 或 position sizing。退出与风险规则的专门字段和变更流程见 `EXIT_RISK_AND_LOGIC_REFINEMENT_STANDARD.md`。

---

## 第一部分：每笔交易必须记录的属性

### 时间和价格
- `entry_time`：进场时间（精确到秒或 bar）
- `entry_price`：进场价格
- `exit_time`：出场时间
- `exit_price`：出场价格
- `exit_reason`：出场原因（take_profit, stop_loss, signal_reversal, ...）

### 风险和回报
- `pnl`：绝对盈亏（USD）
- `pnl_R`：以 risk 为单位的盈亏（Risk units）
  - 定义：`pnl_R = pnl / (entry_price - stop_loss_price)`
  - 例如，entry 1.0850，SL 1.0750，risk = 100 pips = 0.01。
  - 如果 exit 1.0950，pnl = 100 pips，则 pnl_R = 1.0R
- `pnl_percent`：百分比回报
- `holding_time`：持仓时长（bars 或分钟）

### 极值和偏差
- `MFE_R`（Maximum Favorable Excursion）：从进场到出场期间，市场朝有利方向最多走了多少 R
  - 例如 entry 1.0850，最高 1.0900（50 pips），MFE_R = 0.5R
- `MAE_R`（Maximum Adverse Excursion）：从进场到出场期间，市场朝不利方向最多走了多少 R
  - 例如 entry 1.0850，最低 1.0750（100 pips），MAE_R = -1.0R
- `bars_to_mfe`：达到最大有利点数用了多少 bars
- `bars_to_mae`：达到最大不利点数用了多少 bars
- `time_to_1R`：达到 1R 盈利用了多少时间（如果达到）
- `time_to_2R`：达到 2R 盈利用了多少时间（如果达到）

### 入场前可见特征（Ante-Entry Features）
这些特征必须在进场前就已知，可以用于构造 filter。

- `atr_at_entry`：进场时的 ATR（波动率）
- `trend_at_entry`：进场时的趋势（上升/下降/范围）
  - 定义：比较 close 与 20/50 MA，或计算过去 20 bar 的平均方向
- `price_level_at_entry`：价格在日高/日低的位置
  - 例如：(close - day_low) / (day_high - day_low)，范围 0-1
- `rsi_value_at_entry`：RSI 的绝对值（如果使用 RSI）
- `distance_to_ma20`：距离 20 日均线多远
- `session_at_entry`：交易时段（伦敦、纽约、亚洲、重叠等）
- `day_of_week`：星期几
- `news_event_flag`：是否接近重大经济数据发布
- `volatility_regime`：波动率状态（低/中/高）
- `trend_regime`：趋势状态（上升/下降/范围）
- `entry_bar_structure`：进场 bar 的形态
  - 例如：大实体/小实体、上影线/下影线、吞没/纺锤体等

### 入场后观察特征（Post-Entry Features）
这些特征在交易结束后才知道，不能用于构造 filter（这会导致过拟合），但可以解释为什么交易成功或失败。

- `actual_exit_bar_structure`：出场 bar 的形态
- `exit_bar_close_position`：出场 bar 的 close 在高/低的位置
- `subsequent_price_movement`：出场后价格如何运动（是否验证了交易决策）
- `winning_after_long_underwater`：是否在长期水下后才扭亏为盈
- `false_breakout_flag`：是否属于虚假突破（进场后立即反向）

---

## 第二部分：核心对比分析

### 对比 1：Winners vs Losers（胜者 vs 败者）

```python
def analyze_winners_vs_losers(trades):
    winners = [t for t in trades if t.pnl_R > 0]
    losers = [t for t in trades if t.pnl_R <= 0]
    
    print(f"样本数：Winners {len(winners)}, Losers {len(losers)}")
    print(f"胜率：{len(winners) / len(trades) * 100:.1f}%")
    
    # 比较入场前特征
    print(f"\n入场时 ATR：")
    print(f"  Winners: 平均 {mean([t.atr_at_entry for t in winners]):.3f}")
    print(f"  Losers:  平均 {mean([t.atr_at_entry for t in losers]):.3f}")
    print(f"  差异: {'** 显著 **' if p_value < 0.05 else 'not significant'}")
    
    print(f"\nSession：")
    print(f"  Winners: London {count_london(winners)}, NY {count_ny(winners)}, Asia {count_asia(winners)}")
    print(f"  Losers:  London {count_london(losers)}, NY {count_ny(losers)}, Asia {count_asia(losers)}")
    
    # 关键发现
    print(f"\nMFE/MAE 分布：")
    print(f"  Winners: 平均 MFE {mean([t.mfe_r for t in winners]):.2f}R, MAE {mean([t.mae_r for t in winners]):.2f}R")
    print(f"  Losers:  平均 MFE {mean([t.mfe_r for t in losers]):.2f}R, MAE {mean([t.mae_r for t in losers]):.2f}R")
```

**关键观察**：
- 如果 winners 的 ATR 平均 0.85，losers 平均 1.20，这表明低波动环境胜率更高
- 如果 winners 集中在伦敦时段（70%），losers 分散，这表明 session filter 可能有价值
- 如果 winners 的 MAE 平均 -0.3R，losers 平均 -1.5R，这表明失败的交易在错误的方向上走得太远

### 对比 2：TP Winners vs SL Losers（获利了结 vs 止损出场）

```python
tp_winners = [t for t in trades if t.exit_reason == 'take_profit' and t.pnl_R > 0]
sl_losers = [t for t in trades if t.exit_reason == 'stop_loss' and t.pnl_R < 0]

print(f"TP Winners: {len(tp_winners)}, SL Losers: {len(sl_losers)}")
print(f"TP Winners 平均 ATR: {mean([t.atr_at_entry for t in tp_winners]):.3f}")
print(f"SL Losers 平均 ATR: {mean([t.atr_at_entry for t in sl_losers]):.3f}")
```

**意义**：
- TP winners 代表"计划按照预期执行"的情况，其特征最能代表策略的本质
- SL losers 代表"市场反向，立即止损"的情况，分析其特征有助于理解何时信号失效

### 对比 3：Fast Losers vs Slow Losers（快速止损 vs 缓慢止损）

```python
fast_losers = [t for t in losers if t.holding_time < 5]  # 少于 5 bar
slow_losers = [t for t in losers if t.holding_time >= 20]  # 至少 20 bar

print(f"Fast Losers (< 5 bars): {len(fast_losers)}")
print(f"  平均 MAE: {mean([t.mae_r for t in fast_losers]):.2f}R")
print(f"  意义：信号立即被市场打脸，SL 设置合理")

print(f"\nSlow Losers (>= 20 bars): {len(slow_losers)}")
print(f"  平均 MAE: {mean([t.mae_r for t in slow_losers]):.2f}R")
print(f"  意义：进场后长期水下，要么 SL 设置太远，要么市场长期反向")
```

**诊断意义**：
- Fast losers 的 MAE 通常较小（-0.5R）：说明 SL 设置合理，市场只是短期反向
- Slow losers 的 MAE 通常较大（-2.0R）：说明信号完全失效，市场长期反向
- 区分这两者帮助判断是"随机坏运气"还是"系统性错误"

### 对比 4：Top 10% Winners vs Typical Winners（超级赢家 vs 普通赢家）

```python
top_winners = sorted(winners, key=lambda t: t.pnl_r, reverse=True)[:len(winners) // 10]
typical_winners = winners[len(winners) // 10:]

print(f"Top 10%: 平均 MFE {mean([t.mfe_r for t in top_winners]):.2f}R")
print(f"Typical: 平均 MFE {mean([t.mfe_r for t in typical_winners]):.2f}R")

print(f"\nTop 10% 的 ATR: {mean([t.atr_at_entry for t in top_winners]):.3f}")
print(f"Typical 的 ATR: {mean([t.atr_at_entry for t in typical_winners]):.3f}")

print(f"\nTop 10% 的 trend: {mode([t.trend_at_entry for t in top_winners])}")
print(f"Typical 的 trend: {mode([t.trend_at_entry for t in typical_winners])}")
```

**意义**：
- Top 10% 往往发生在高波动、大趋势的环境
- 这表明"最好的信号"和"普通信号"可能对环境的依赖性不同
- 不意味着要删除低质量信号，但提醒我们：当环境不利时，期望要调低

### 对比 5：Deep-MAE Winners vs Clean Winners（水下反弹赢 vs 一帆风顺赢）

```python
deep_mae_winners = [t for t in winners if t.mae_r < -0.8]  # MAE 深于 -0.8R
clean_winners = [t for t in winners if t.mae_r > -0.3]    # MAE 浅于 -0.3R

print(f"Deep-MAE: {len(deep_mae_winners)}, 平均 pnl_r: {mean([t.pnl_r for t in deep_mae_winners]):.2f}R")
print(f"  这些交易先下水，后上浮，常见吗？是否只在特定环境？")

print(f"\nClean: {len(clean_winners)}, 平均 pnl_r: {mean([t.pnl_r for t in clean_winners]):.2f}R")
print(f"  这些交易进场就直奔 TP，更稳定吗？")
```

**诊断**：
- 如果 deep-MAE winners 很多，说明策略对"进场后的反向"容忍度高，可能 SL 太宽
- 如果 clean winners 占多数，说明信号非常精准，进场即有利

---

## 第三部分：关键区分 - 可见特征 vs Hindsight 特征

### 禁止使用的 Hindsight 特征

任何基于以下特征构造的 filter 都是过拟合，因为这些特征只有在交易结束后才知道：

- `actual_mfe_r`：实际达到的最大有利点数（这是在 exit bar 之后才知道的）
- `actual_mae_r`：实际达到的最大不利点数
- `final_pnl_r`：最终的盈亏（这是结果，不是原因）
- `bars_to_exit`：持仓多久才出场（取决于市场运动，不可预测）
- `exit_bar_structure`：出场 bar 的形态（未来数据）
- `subsequent_move_direction`：出场后价格的运动方向

**例子**：
- 错误：`if actual_mfe > 1.5: take_profit`（这等于看结果后下单）
- 正确：`if atr > 1.0: increase_position_size`（这基于入场前的波动率）

### 允许使用的可见特征

这些特征在 entry bar 或 entry bar 之前就已知，可以用于构造 filter：

- `atr_at_entry`：当前的波动率
- `trend_at_entry`：过去 20 bar 的平均方向（计算完成）
- `rsi_value_at_entry`：当前的 RSI
- `session_at_entry`：当前是哪个时段
- `day_of_week`：今天是星期几
- `distance_to_ma`：价格与均线的距离
- `news_event_flag`：是否接近重大数据

**例子**：
- 正确：`if atr_at_entry < 0.5: skip_trade`（低波动环境胜率不好，基于统计）
- 正确：`if trend == 'downtrend': reduce_position_size`（下降趋势中表现不佳，基于统计）

---

## 第四部分：候选 Filter 的七层检验

任何提议的新 filter 都必须通过以下七层检验。通过全部才能进入 Stage 6 逻辑优化。

### 第1层：入场前可见性检验

```
问题：这个特征在 entry bar 时是否已知？
例如："仅在 ATR > 0.8 时入场"
检验：ATR 在 entry bar close 时已知吗？是。✓ PASS
```

### 第2层：样本数检验

```
问题：使用这个 filter 后剩余多少样本？
例如：原始 234 笔，使用 ATR > 0.8 filter 后 154 笔
检验：剩余 154 笔，足以进行统计推断吗？
      > 30 笔：可以，✓ PASS
      10-30 笔：勉强可以，但要谨慎
      < 10 笔：样本太小，❌ FAIL，不能加这个 filter
```

### 第3层：减少亏损能力检验

```
问题：这个 filter 能减少亏损吗？
例如：所有亏损交易中，有多少被 ATR > 0.8 filter 排除掉了？
检验：
  使用前：234 笔，121 笔亏损，胜率 48.3%
  使用后：154 笔，63 笔亏损，胜率 59.1% (+10.8pp)
  
  这个 filter 排除掉了 58 笔亏损交易
  剩余亏损 63 笔
  
  ✓ PASS：显著减少了亏损，同时没有大量误杀赢利
```

### 第4层：不过度误杀赢利检验

```
问题：这个 filter 误杀了多少赢利交易？
检验：
  使用前：113 笔赢利
  使用后：91 笔赢利
  误杀率：(113 - 91) / 113 = 19.5%
  
  问题：误杀 22 笔赢利，值得吗？
  权衡：减少 58 笔亏损 vs 误杀 22 笔赢利
  净效果：58 - 22 = 36 笔净减亏损 ✓ PASS
  
  如果误杀 > 30%：❌ FAIL，代价太高
```

### 第5层：跨年份稳定性检验

```
问题：这个 filter 在不同年份是否都有效？
检验：
  2020：ATR filter 胜率 62% (with) vs 54% (without)，+8pp ✓
  2021：胜率 60% vs 52%，+8pp ✓
  2022：胜率 55% vs 48%，+7pp ✓
  2023：胜率 58% vs 51%，+7pp ✓
  2024：胜率 56% vs 49%，+7pp ✓
  2025：胜率 54% vs 47%，+7pp ✓
  
  一致性：6 个年份都显示 +7-8pp 提升 ✓ PASS
  
  如果某年没有效果或反向：❌ FAIL，不稳定
```

### 第6层：跨 Regime 鲁棒性检验

```
问题：这个 filter 在不同市场条件下都有效吗？
检验：
  高 ATR 环境：ATR > 0.8 filter 胜率 62% (with) vs 58% (without)，+4pp ✓
  低 ATR 环境：胜率 48% vs 45%，+3pp ✓
  上升趋势：胜率 60% vs 56%，+4pp ✓
  下降趋势：胜率 50% vs 46%，+4pp ✓
  
  所有 regime 都有正面效果 ✓ PASS
  
  如果在某个 regime 反向或无效：❌ FAIL，不鲁棒
```

### 第7层：Development Validation 验证

```
问题：这个 filter 在没有参与发现它的开发验证数据上是否仍然有效？
检验：
  在 discovery_train 数据上发现：ATR > 0.8 filter 胜率 +7pp
  在 development_validation 数据上：胜率 +6pp
  
  一致性很好 ✓ PASS
  
  如果 development_validation 上的效果消失或反向：❌ FAIL，不能进入 Stage 6
```

`development_validation` 一旦用于接受 filter，就已经被消耗，不得在 Stage 7 或冻结报告中称为最终 holdout。`locked_final_holdout` 必须保持不可见，直到入场、出场、风险、成本和参数全部固定后只评价一次。

---

## 第五部分：候选 Filter 的终极通过标准

一个 filter 只有同时满足以下条件才能进入 Stage 6：

1. ✓ 入场前可见（第1层）
2. ✓ 样本数 >= 30（第2层）
3. ✓ 能减少亏损，净效果 > 0（第3层）
4. ✓ 误杀赢利率 < 30%（第4层）
5. ✓ 在所有 5+ 个年份都有效（第5层）
6. ✓ 在所有主要 regime 都有效（第6层）
7. ✓ 在 development_validation 集上效果不消失（第7层）

**反面例子**：
```
Filter: "Only trade on Mondays and Tuesdays"
检验：
  第1层：✓ (day of week is known)
  第2层：✓ (78 trades remain, > 30)
  第3层：✓ (胜率 52% vs 48%, +4pp)
  第4层：✓ (误杀率 18%)
  第5层：✗ (只在 2021-2022 有效，2023-2024 无效)
  
  失败：不稳定，不能加这个 filter
```

---

## 第六部分：当失败者和成功者特征差异极小时

如果经过全面分析，发现 winners 和 losers 在入场前的特征几乎没有区别，应该：

1. **接受策略存在随机亏损**：不是所有信号都有效，这是正常的。
2. **不要强行加 filter**：强行加 filter 最终导致过拟合。
3. **改变预期，而不是改变规则**：承认这个策略的胜率就是 48-52%，而不是 60%。
4. **考虑退出该策略**：如果信号本身就没有统计意义，再多的 filter 也拯救不了它。

**例子**：
```
Analysis shows:
- Winners 平均 ATR 0.95，Losers 平均 ATR 0.93：差异仅 0.02，无统计意义
- Winners 平均 RSI 28，Losers 平均 RSI 29：差异仅 1，无统计意义
- Winners 胜率各 session 都是 48-50%，无显著差异

结论：信号本身缺乏有效的可见特征区分成功和失败
决策：放弃这个策略的后续优化，转向其他想法
```

---

## 归因分析的输出示例

一个完整的 attribution report 应该像这样：

```markdown
# Trade Attribution Report for STRAT_RSI_001

## 整体对比
- 总交易数：234
- 胜利单：113（48.3%）
- 亏损单：121（51.7%）
- 平均赢：+1.8R
- 平均亏：-0.9R
- 期望值：+0.25R

## Winners vs Losers

### 入场时特征
| 特征 | Winners | Losers | 差异 | 显著性 |
|------|---------|--------|------|-------|
| 平均 ATR | 0.85 | 1.20 | -0.35 | p<0.001 ✓✓ |
| 平均 RSI | 28 | 26 | +2 | p=0.15 |
| 伦敦 session % | 70% | 35% | +35pp | p<0.001 ✓✓ |
| 上升趋势 % | 62% | 38% | +24pp | p<0.001 ✓✓ |

### MFE / MAE
- Winners: 平均 MFE 1.5R, MAE -0.3R
- Losers: 平均 MFE 0.4R, MAE -1.5R

## 候选 Filter 评估

### Candidate 1: ATR > 0.8
| 指标 | 结果 | 通过 |
|------|------|------|
| 样本数 | 154（65% retain） | ✓ |
| 胜率提升 | 48% → 58% (+10pp) | ✓ |
| 误杀赢利 | 22/113 (19%) | ✓ |
| 年份稳定性 | 所有年份 +7-8pp | ✓ |
| Regime 鲁棒性 | 所有 regime +3-4pp | ✓ |
| Development Validation | +6pp (vs +7pp discovery_train) | ✓ |

**结论：ACCEPT - 进入 Stage 6**

### Candidate 2: Session = London Only
| 指标 | 结果 | 通过 |
|------|------|------|
| 样本数 | 82（35% retain） | ✗ |
| 胜率提升 | 48% → 62% (+14pp) | ✓ |
| 年份稳定性 | 2020-2022 有效，2023+ 衰减 | ✗ |

**结论：REJECT - 样本太小，年份不稳定**

## 最终建议
1. 接受 ATR > 0.8 filter 作为 Stage 6 候选，保留 locked final holdout，进入逻辑优化
2. 继续监控 session 差异，2025+ 年份能否恢复
3. 不接受 pure London filter（过度过滤）
```

这就是 Stage 5 的完整工作流程。通过严格的七层检验，确保任何新增 filter 都是数据驱动而非直觉驱动。
