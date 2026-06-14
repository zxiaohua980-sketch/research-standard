# 🚀 今天就能开始开发策略

## ⏱️ 30 分钟快速准备

### 第1步：阅读必读文件（10 分钟）

打开以下文件，按顺序快速浏览：

1. **README.md** (2 min)
   - 了解整套规范是什么
   - 核心原则："先审计，后研究；先归因，后优化；先冻结，后前向"

2. **CLAUDE.md 十三大禁区** (3 min)
   - 记住 13 条规则，避免踩坑
   - 这些禁区涵盖了 95% 的常见错误

3. **CHEATSHEET.md** (5 min)
   - 快速参考卡片
   - 遇到问题时查这个

---

### 第2步：建立你的第一个策略项目（15 分钟）

打开 PowerShell，复制粘贴以下命令：

```powershell
# 创建策略目录（用你的策略名替换 MYNAME）
$strategyName = "STRAT_MYNAME_001"
$path = "D:\MT5\openclaw\$strategyName"

mkdir $path
cd $path

# 初始化 Git
git init
git config user.name "Your Name"
git config user.email "your@email.com"

# 创建基本目录结构
mkdir tests, analysis, output

# 创建关键文件（使用下面的模板）
```

创建 **`.gitignore`**（复制 strategy_double_bottom 的）：
```
__pycache__/
*.pyc
*.csv
*.log
output/
optimization_output/
```

创建 **`README.md`**：
```markdown
# STRAT_MYNAME_001 - 我的第一个策略

## 基本信息
- strategy_id: STRAT_MYNAME_001
- signal: [你的信号假说]
- market: [目标市场]
- timeframe: [时间框架]

## 开发进度
- [ ] Stage 0: Registration
- [ ] Stage 1: Hypothesis
- [ ] Stage 2: Execution Audit
- [ ] ... (更多阶段)
```

创建 **`config.yaml`**：
```yaml
strategy:
  id: STRAT_MYNAME_001
  market: EUR/USD
  timeframe: H1

signal_config:
  type: [你的信号类型，如 RSI, MACD, etc]
  
risk_model:
  stop_loss: 1.0
  take_profit: 1.5
  max_concurrent: 5
```

创建 **`signal_engine.py`**（复制 TEMPLATE_signal_engine.py）
创建 **`backtest.py`**（简单框架）
创建 **`version.json`**

```json
{
  "strategy_id": "STRAT_MYNAME_001",
  "version": "v0.0",
  "current_stage": "stage_0_registration",
  "hypothesis": "你的假说一句话版本"
}
```

第一个 commit：

```powershell
git add .
git commit -m "[INIT] strategy_id=STRAT_MYNAME_001, hypothesis=你的假说"
```

✅ **完成！你已经完成了 Stage 0（Project Registration）**

---

## 📖 接下来的 3 个小时：第一个完整假说

### 打开 STRATEGY_DEVELOPMENT_QUICKSTART.md

找到 **"第二步：写假说（30 分钟）"** 一节，回答这四个问题：

1. **一句话假说**
   ```
   例如："RSI < 30 表示超卖，未来反弹概率 > 50%"
   ```

2. **市场微观结构证据**
   ```
   例如："过度卖出导致流动性缺失，参与者争夺便宜筹码"
   ```

3. **正期望来自什么**
   ```
   例如："波动率均值回归"
   ```

4. **预期交易频率**
   ```
   例如："EUR/USD H1 每月 20-30 笔"
   ```

写在 `README.md` 或新建 `hypothesis.md` 中，然后 commit：

```powershell
git add hypothesis.md
git commit -m "[STAGE] strategy_id=STRAT_MYNAME_001, action=hypothesis

一句话：[你的假说]
市场基础：[为什么有效]
预期频率：[多少笔交易]"
```

✅ **完成！你已经完成了 Stage 1（Strategy Hypothesis）**

---

## 🔨 今晚的任务：第一个回测

### 打开 STRATEGY_DEVELOPMENT_QUICKSTART.md

找到 **"第三步：回测与审计"** 一节，你需要：

1. **写 signal_engine.py**（参考 TEMPLATE_signal_engine.py）
   ```python
   class SignalEngine:
       def generate_signal(self, bars_data, bar_index):
           # 只生成信号
           if rsi < 30:
               return {'type': 'LONG'}
           return None
   ```

2. **写 backtest.py**（执行交易）
   ```python
   class BacktestEngine:
       def run_backtest(self, historical_data, signals):
           # 只执行交易，不改信号
           trades = []
           # ... 回测逻辑
           return trades
   ```

3. **运行回测**并保存结果到 `trades_detail.csv`

4. **生成审计报告** `execution_audit.md`：
   ```markdown
   # Execution Audit

   ## Data Leakage Check
   - [ ] 没用未来数据
   - [ ] SL/TP 在 entry bar 之前设置

   ## Fee Model
   - Spread: 0.0002
   - Commission: 0.001

   ## Result
   - Total trades: XXX
   - Sharpe: X.XX

   ## Conclusion: PASS or FAIL
   ```

5. **Commit 结果**

```powershell
git add signal_engine.py backtest.py execution_audit.md trades_detail.csv
git commit -m "[AUDIT] strategy_id=STRAT_MYNAME_001, action=audit-fix

审计通过 / 修复完成

- 总交易数：150
- Sharpe：1.2
- 无前视偏差"
```

✅ **完成！你已经完成了 Stage 2（Execution Audit）和 Stage 4（Fixed-Rule Backtest）**

---

## 📊 周末的重头：交易赢亏归因

### 打开 TRADE_ATTRIBUTION_STANDARD.md

这是最重要的一步。你需要：

1. **计算每笔交易的属性**（参考文档的"每笔交易必须记录的属性"）
   ```python
   trades['pnl_R'] = pnl / risk
   trades['MFE_R'] = max_favorable / risk
   trades['MAE_R'] = max_adverse / risk
   trades['atr_at_entry'] = ...
   trades['trend_at_entry'] = ...
   # ... 更多特征
   ```

2. **对比 Winners vs Losers**
   ```python
   winners = trades[trades['pnl_R'] > 0]
   losers = trades[trades['pnl_R'] <= 0]
   
   print(f"胜率: {len(winners) / len(trades):.1%}")
   print(f"Winners 平均 ATR: {winners['atr'].mean():.3f}")
   print(f"Losers 平均 ATR: {losers['atr'].mean():.3f}")
   ```

3. **发现模式**
   ```
   例如：低 ATR 环境胜率仅 35%，高 ATR 环境 62%
   ```

4. **评估候选 filter**（通过七层检验）
   ```markdown
   # Candidate Filter: ATR > 0.8
   
   1. 入场前可见? ✓ YES
   2. 样本数 >= 30? ✓ YES (50 笔)
   3. 减少亏损? ✓ YES (从 60 笔降到 25 笔)
   4. 误杀赢利 < 30%? ✓ YES (18%)
   5. 年份稳定? ✓ YES (2020-2024 都 +5pp)
   6. Regime 稳健? ✓ YES (高低 ATR 都改善)
   7. OOS-Dev 验证? ✓ YES (development_validation +4pp；locked final holdout 仍封存)
   
   结论: ACCEPT - 可以加这个 filter
   ```

5. **生成报告** `trade_attribution_report.md`

6. **Commit**

```powershell
git add analysis/trade_attribution.py trade_attribution_report.md
git commit -m "[ATTRIB] strategy_id=STRAT_MYNAME_001, action=attribution

交易赢亏归因完成

- 发现 ATR filter 有效
- 低 ATR 胜率：35%
- 高 ATR 胜率：62%
- 建议加 ATR > 0.8 filter"
```

✅ **完成！你已经完成了 Stage 5（Trade Attribution）**

---

## 🎯 下周的计划

继续按照流程走：

- **第6周**: Stage 6 逻辑优化 + Stage 7 参数优化（参考 OPTIMIZATION_POLICY.md）
- **第7周**: Stage 8 回溯验证 + Stage 9 环境诊断（参考相关 MD）
- **第8周**: Stage 10 时间诊断 + Stage 11 版本冻结（参考 VERSIONING_AND_FREEZE_POLICY.md）
- **第9周+**: Stage 12 前向交易（参考 FORWARD_VALIDATION_STANDARD.md）

---

## 📝 每天的 Commit 模板

```powershell
git add <files>
git commit -m "[STAGE] strategy_id=STRAT_MYNAME_001, action=<action>

<一句话总结>

- 第一项发现
- 第二项改进
- 第三项决定"
```

---

## 🆘 遇到问题？

### 问题1：我的回测 Sharpe > 2.0，太好了！
**答**: 可能有前视偏差。打开 RESEARCH_WORKFLOW.md Stage 2，逐项检查。

### 问题2：我想加一个 filter
**答**: 打开 TRADE_ATTRIBUTION_STANDARD.md，通过七层检验。不通过就不能加。

### 问题3：我的参数优化结果看起来很好
**答**: 打开 `DATA_SPLIT_AND_OOS_POLICY.md` 和 `OPTIMIZATION_POLICY.md`，确保你区分 IS、OOS-Dev、一次性的 OOS-Final 与 Forward-Live。

### 问题4：我不知道下一步该做什么
**答**: 打开 CHEATSHEET.md 的"文档速查地图"，找到你的问题。

### 问题5：我改了规则，现在怎么办？
**答**: 打开 VERSIONING_AND_FREEZE_POLICY.md，创建新版本（v0.2）。

---

## ✨ 你现在拥有的

✅ **11 个核心规范文档**（告诉你做什么不做什么）  
✅ **实战指南** STRATEGY_DEVELOPMENT_QUICKSTART.md（告诉你怎么做）  
✅ **代码模板** TEMPLATE_signal_engine.py（告诉你代码怎么写）  
✅ **快速参考** CHEATSHEET.md（遇到问题快速查）  
✅ **13 阶段流程** RESEARCH_WORKFLOW.md（告诉你完整步骤）

---

## 🎯 现在就开始！

1. 打开 PowerShell
2. 创建你的策略目录
3. 运行 `git init`
4. 写 README.md 和 hypothesis.md
5. `git commit` 第一个 commit
6. 开始写 signal_engine.py

**Done！你已经迈出第一步。** 🚀

---

**下一个里程碑**: Stage 2 Execution Audit 完成（明天下午）  
**再下一个里程碑**: Stage 5 Trade Attribution 完成（周末）  
**最终里程碑**: Stage 11 Freeze Version（3 周后）

祝你开发顺利！如有问题，查文档。文档就是你的律师。
