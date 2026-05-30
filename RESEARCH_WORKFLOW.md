# 完整量化策略研究流程（Stage 0-13）

## 总体思想

量化研究不是"跑回测"，而是从假说出发，经历假说验证、审计、事件研究、固定规则回测、赢亏归因、逻辑优化、样本外验证、环境与时间验证、冻结版本、最后前向验证的完整闭环。任何跳过的阶段都会留下过拟合或执行偏差的隐患。每个阶段都是必经的，每个阶段都必须有明确的产出和通过标准。

贯穿所有阶段的两项横向政策：

- `DATA_SPLIT_AND_OOS_POLICY.md`：定义 IS、OOS-Dev、OOS-Final、WF-OOS、Forward-Live 与数据消费台账。
- `EXIT_RISK_AND_LOGIC_REFINEMENT_STANDARD.md`：定义成交时点、SL/TP、动态退出、头寸规模和逻辑调整门槛。

---

## Stage 0：Project Registration（项目注册）

### 目标
建立策略的唯一身份标识和项目记录，确保跨团队、跨电脑、跨时间段的协调。没有注册，就没有正式研究。

### 必做项

1. **分配唯一 strategy_id**：格式 `STRAT_<SIGNAL_NAME>_<SERIAL>`，例如 `STRAT_RSI_001`、`STRAT_MACD_BREAKOUT_002`。strategy_id 在整个研究生涯中固定，不能重复或改名。

2. **初始化 Git 仓库**：
   ```
   cd /path/to/strategy_root
   git init
   git config user.name "Your Name"
   git config user.email "your@email.com"
   ```

3. **编写 .gitignore**：
   ```
   *.pyc
   __pycache__/
   .DS_Store
   venv/
   output/*.csv
   output/*.png
   output/temp_*
   backtest_cache/
   ```
   原则：源代码和配置入库，运行输出和临时缓存不入库。

4. **建立项目目录结构**：
   ```
   strategy_root/
   ├── signal_engine.py
   ├── backtest.py
   ├── config.yaml
   ├── version.json
   ├── README.md
   ├── tests/
   ├── output/
   └── .git/
   ```

5. **编写初始 README.md**：包含 strategy_id、信号假说一句话版、预期交易频率、目标市场。

6. **登记到 strategy_registry.yaml**：
   ```yaml
   - strategy_id: STRAT_RSI_001
     root_path: D:\MT5\strategies\STRAT_RSI_001
     git_repo: https://github.com/user/STRAT_RSI_001
     git_branch: develop
     current_stage: stage_1_hypothesis
     current_status: active
     key_files:
       - signal_engine.py
       - config.yaml
     last_result: null
     next_action: write hypothesis
     owner_machine: machine_001
     last_updated: 2025-06-01
   ```

7. **初始 commit**：
   ```
   git add .
   git commit -m "[INIT] strategy_id=STRAT_RSI_001, hypothesis=RSI_oversold_breakout"
   git branch develop
   ```

### 产出
- strategy_id（文档）
- .gitignore 和初始 commit
- strategy_registry.yaml 记录（新增或更新）
- version.json 初始版本（version: 0.0, status: hypothesis_stage）

### 通过标准
- registry 中有明确的 strategy_id 记录
- Git repo 初始化完成，有至少一个 commit
- 项目目录结构已建立，README 可读

---

## Stage 1：Strategy Hypothesis（策略假说）

### 目标
清晰定义策略的核心假说，确保后续所有分析都围绕同一个可验证的观点。假说必须是市场微观结构的某个观察，而不是"赚钱"。

### 必做项

1. **一句话假说**：策略的核心观点必须能用一句话表达，例如"RSI < 30 时 reversal 概率上升 30 个基点"。

2. **市场行为基础**：解释为什么这个信号应该有效。例如，是因为过度卖出导致反弹？是因为技术面违背基本面？是因为流动性缺失的时间窗口？必须指出市场微观结构的具体观察。

3. **期望收益来源**：说明该信号的正期望是否来自波动率均值回归、趋势延续、或流动性摩擦获利。注意：不能只说"历史数据显示有效"，必须指出动力机制。

4. **信号的可观察性**：信号必须在入场时刻、基于当时已知的数据计算。禁止使用未来数据或事后信息。

5. **样本期望**：粗略估计交易频率。例如"预期每月 20-50 笔"。

6. **记录在 README.md 或 hypothesis.md**，并 commit：
   ```
   [STAGE] strategy_id=STRAT_RSI_001, action=hypothesis

   RSI oversold reversal 假说

   - 假说：RSI(14) < 30 表示超卖，未来 5-20 bar 内反弹概率 > 50%
   - 市场基础：过度卖出导致流动性不足，市场参与者争夺便宜筹码
   - 交易频率：预期 EUR/USD H1 每月 20-30 笔
   ```

### 产出
- hypothesis.md 或 README.md 中的假说陈述
- 一个 commit 记录假说

### 通过标准
- 假说能用一句话清晰表达
- 市场基础给出了动力解释，不是纯数据驱动
- 假说可测试（能通过数据验证或反驳）
- 没有假说的回测结果无效

---

## Stage 2：Execution Audit（执行审计）

### 目标
检查回测框架是否存在数据泄露、逻辑错误、费用模型失效等致命问题。任何回测结果都必须通过审计，否则数字完全无信息量。

### 必做项

1. **前视偏差检查**（Data Leakage）：
   - 明确决策时点与可成交时点：bar-close 策略在 `bar t` 收盘后才知道的信号，最早以 `bar t+1` 的首个可成交 bid/ask 执行。
   - 检查 RSI、MACD、MA 等指标是否使用了订单提交后才可知的信息。
   - 禁止使用 `bar t` 的 close 生成信号后，又假设订单按同一个 close 无滑点成交；若确有逐 tick 执行证据，必须记录事件顺序。
   - 检查是否有"当日 high/low"用于止损或获利，如果有，这是未来数据，必须改为前一日的数据或前一根 bar 的数据。

2. **入场当根止损/获利逻辑**：
   - 确认 initial SL、initial TP、动态退出和头寸规模都可在提交订单时由已知数据计算。
   - 确认多仓 SL 低于 fill、TP 高于 fill；空仓相反。
   - 如果一个 OHLC bar 同时触及 SL 与 TP，必须使用预先声明的有序细粒度数据或保守的 `SL-first` 规则。
   - 检查跳空越过 stop/target 时是否按首个真实可成交报价而非理想价成交。

3. **非法止损方向检查**：
   - 检查是否存在"只有亏损时才关闭头寸"的逻辑。这会导致样本偏差。
   - 确认所有交易都有明确的出场条件，不是"无限持仓直到手动平仓"。

4. **冲突持仓检查**：
   - 确认不存在同时持多和持空的情况（除非是配对交易）。
   - 如果有多个合约，确认同一合约不能同时持多和持空。

5. **费用模型检查**：
   - 验证 bid-ask spread 是否合理，例如 EUR/USD H1 应该是 0.1-0.3 pips，而不是 0 或 0.01 pips。
   - 验证 commission、swap、slippage 是否包含。
   - 确认费用是否对称（entry 和 exit 都计费）。

6. **样本末端检查**：
   - 检查最后一笔交易是否未平仓。如果未平仓，必须标记"open position"或排除该笔。
   - 确认样本终止日期不是在某笔交易的中间，导致数据被切割。

7. **历史回填 vs 前向区分**：
   - 确认回测数据是否包含前向验证周期（framework_start_time）之后的数据。
   - 如果包含，必须严格分离，用不同的标签标记"backtest"和"forward"。

8. **输出审计报告**：
   ```
   # Execution Audit Report for STRAT_RSI_001

   ## Data Leakage Check
   - ✓ 信号在 bar t close 确认，订单在 bar t+1 首个可成交报价执行
   - ✓ Entry/exit 使用正确的 bid/ask 与费用模型
   - ✓ SL/TP collision 采用预声明的保守或有序数据规则

   ## Fee Model
   - Bid-ask: 0.0002 (reasonable for EUR/USD H1)
   - Commission: 0.001 per round trip
   - Slippage: 0 (conservative)

   ## Sample Check
   - Total trades: 234
   - Open positions at end: 0
   - Data range: 2020-01-01 to 2025-05-31

   ## Conclusion: PASS / FAIL
   ```

9. **Commit 审计结果**：
   ```
   [AUDIT] strategy_id=STRAT_RSI_001, action=audit-fix
   
   执行审计通过，修复 RSI 前视偏差
   
   - RSI 计算改为前一根 bar（第 42 行）
   - Entry bar 不使用当日 high/low
   - 费用模型验证无误
   ```

### 产出
- execution_audit.md（详细报告）
- 修正后的 signal_engine.py 或 backtest.py
- audit pass/fail 的明确标记

### 通过标准
- 没有前视偏差
- 费用模型合理且对称
- 成交、SL/TP、gap、collision、position sizing 与 MT5/broker 约束审计通过
- 样本完整，末端没有未平仓或被切割的交易
- 审计报告明确写出 PASS 或 FAIL，不能含混

---

## Stage 3：Event Study（事件研究）

### 目标
研究信号本身的有效性，不考虑风险管理。输出信号的胜率、效果大小、延迟衰减等基础统计，为后续的规则优化提供参考。

### 必做项

1. **每笔交易记录完整数据**：
   ```
   entry_time, symbol, timeframe, signal_type, entry_price,
   stop_loss, take_profit, exit_reason, pnl_R,
   MFE_R, MAE_R, time_to_1R, time_to_2R, bars_to_exit,
   entry_bar_adverse_excursion, signal_structure_features, environment_features
   ```

2. **计算 MFE 和 MAE**：
   - MFE（Maximum Favorable Excursion）：从进场到出场期间达到的最大有利点差
   - MAE（Maximum Adverse Excursion）：从进场到出场期间遭遇的最大不利点差
   - 输出格式：相对于 entry price 的 R 单位数，例如 MFE_R = 1.5 表示最有利时比止损距离多了 50%

3. **命中概率分析**：
   - Hit 1R：多少笔交易达到或超过 1R 利润
   - Hit 2R：多少笔交易达到或超过 2R 利润
   - 胜率：赢利笔数 / 总笔数
   - 平均赢利 / 平均亏损

4. **延迟衰减分析**（Decay Analysis）：
   - 分析信号强度如何随时间衰减，例如 T+0（进场日）、T+1、T+2、T+5、T+20
   - 输出：不同时间窗口的胜率、期望值
   - 目的：找出信号的最优持仓时间

5. **样本分层分析**：
   - 按 symbol 分层（如果有多个市场）
   - 按 timeframe 分层
   - 按年份分层
   - 按 ATR regime 分层（低、中、高波动率）
   - 按 trend 分层（上升、下降、范围）
   - 检查信号在不同子集上的一致性

6. **输出 event_study_report.md**：
   ```
   # Event Study Report for STRAT_RSI_001

   ## Overall Statistics
   - Total events: 234
   - Win rate: 48.3%
   - Avg winner: +1.8R
   - Avg loser: -0.9R
   - Expected value per trade: +0.25R

   ## MFE / MAE Distribution
   - [图表或分布统计]

   ## Hit Probability
   - Hit 1R: 62%
   - Hit 2R: 28%
   - Hit 3R: 8%

   ## Decay Analysis
   - T+0: win rate 50%, expectancy +0.3R
   - T+5: win rate 48%, expectancy +0.2R
   - T+20: win rate 42%, expectancy -0.1R
   - Optimal holding: 5-10 bars

   ## Stratification
   - High ATR (>1.0): win rate 62%, expectancy +0.4R
   - Low ATR (<0.5): win rate 35%, expectancy -0.2R
   - Conclusion: signal stronger in volatile environments
   ```

7. **Commit 事件研究**：
   ```
   [EVENT] strategy_id=STRAT_RSI_001, action=event-analysis

   事件研究完成，信号在高波动环境下有效

   - 总样本：234 笔
   - 胜率：48.3%
   - 期望值：+0.25R
   - 高 ATR 胜率：62%，低 ATR 胜率：35%
   ```

### 产出
- event_study_report.md（含统计表格和图表）
- trade_summary.csv（含 MFE/MAE/时间等字段）
- 一个 commit

### 通过标准
- 事件研究基于 approved audit result
- 所有交易都有 MFE/MAE 计算
- 有明确的分层分析，不是单一总结
- 期望值（expectancy）明确计算，正期望通过通过的前提

---

## Stage 4：Fixed-Rule Backtest（固定规则回测）

### 目标
基于固定的信号和风险管理规则，对 `discovery_train`（以及协议允许时的 `development_validation`）运行基线回测，输出基础交易明细、月度、年度、最大回撤等指标，为后续归因与优化提供开发基线。不得为了建立基线而提前打开 `locked_final_holdout`。

### 必做项

1. **冻结规则**：确认不再改变任何信号逻辑或止损/获利方式。当前规则版本记录在 config.yaml，例如：
   ```yaml
   signal:
     type: RSI_oversold
     rsi_period: 14
     threshold: 30
   exit:
     take_profit: 1.5R
     stop_loss: 1.0R
   ```

2. **基线回测**：跑协议中已经允许消费的历史开发样本；`locked_final_holdout` 保持 sealed，输出：
   - 交易明细：entry_time, entry_price, exit_time, exit_price, pnl, pnl_R, commission
   - 月度汇总：month, trades, wins, losses, pnl, win_rate, max_dd, sharpe
   - 年度汇总：year, trades, wins, losses, pnl, win_rate, max_dd, sharpe, calmar
   - 整体指标：total_trades, total_pnl, sharpe, calmar, sortino, max_drawdown, recovery_factor

3. **顶部交易分析**：
   - Top 5% removal：移除最好的 5% 交易后，Sharpe/Calmar 如何变化
   - 目的：检查整体收益是否高度依赖少数大赢利交易

4. **成本透明度**：
   - 总费用 vs 总盈利的比例（例如费用占盈利 10%）
   - 月度费用变化（检查是否有某些月份交易异常频繁或成本异常高）

5. **Commit 固定规则结果**：
   ```
   [BACKTEST] strategy_id=STRAT_RSI_001, action=fixed-rule

   固定规则回测完成，无后续优化

   - 总交易数：234
   - 胜率：48.3%
   - 总盈利：+5200 USD
   - Sharpe：1.2
   - 最大回撤：-8%
   - Top 5% removal: Sharpe 降至 0.9
   ```

6. **保存所有中间结果**：
   - trades_detail.csv（完整交易明细）
   - monthly_summary.csv
   - yearly_summary.csv
   - backtest_stats.json（所有指标的 JSON 格式）

### 产出
- trades_detail.csv
- monthly/yearly summary
- backtest_stats.json
- fixed_rule_backtest_report.md
- 一个 commit 记录结果（含 commit hash 和时间戳）

### 通过标准
- 规则冻结，无参数优化
- 交易明细完整，样本数合理
- Top 5% removal 分析完成
- 成本透明

---

## Stage 5：Trade Attribution（交易赢亏归因）

### 目标
对比盈利单和亏损单，找出成功和失败的共同特征，区分入场前可见特征与事后 hindsight 特征。这是决定是否添加新 filter 的唯一根据。

### 必做项

1. **建立交易特征矩阵**。每笔交易除了 PnL 外，还要计算以下特征（入场前可观察）：
   - ATR（当日波动率）
   - Trend（过去 20 bar 的平均方向，上升/下降/范围）
   - RSI value（当日 RSI 的绝对值）
   - Price level（距离日高/日低的位置）
   - MA distance（价格与 20/50/200 MA 的距离）
   - Session（伦敦、纽约、亚洲市场的哪个时段）
   - Day of week（星期几）
   - News indicator（有无重大经济数据发布）
   - Entry bar structure（大实体 vs 小实体，向上 vs 向下）

2. **分组对比**（Cohort Analysis）：
   ```
   Winners (pnl > 0) vs Losers (pnl < 0):
   - 平均 ATR: winners 0.85, losers 1.20 → 低波动环境胜率更高
   - 平均 RSI: winners 28, losers 25 → 极端超卖时反而容易失败
   - Session: 伦敦时段胜率 62%, 纽约时段 45%, 亚洲时段 38%
   - Trend: 上升趋势中胜率 55%, 下降趋势 45%, 范围内 48%

   Fast Losers (exit in <5 bars) vs Slow Losers (>20 bars):
   - 快速止损单平均 MAE 0.5R, 慢速亏损单平均 MAE 2.0R
   - 意味着：止损设置得当，市场方向与信号反向

   Top 10% Winners vs Typical Winners:
   - 大赢利单的 MFE 平均 2.5R，普通赢利单 1.7R
   - 大赢利单多发生在高波动、大趋势环境
   ```

3. **区分可见特征 vs Hindsight 特征**：
   - 可见：ATR、session、day of week、price level（都是 entry bar 之前就知道的）
   - Hindsight：exit bar 的 size、之后的价格涨跌、实际的 MFE（这些是交易执行后才知道的）
   - 任何基于 hindsight 的 filter 都是过拟合的陷阱

4. **统计检验**（如果有统计基础）：
   - T-test：winners 和 losers 的 ATR 均值差异是否显著（p < 0.05）
   - 如果 p > 0.05，说明差异可能是随机的，不应该加 filter

5. **候选 filter 评估**。对每个发现的差异，评估是否值得加 filter：
   ```
   Candidate Filter: Only trade in high ATR (> 0.8) environment
   
   Evaluation:
   - 低 ATR (<0.5) 交易数：80 笔，胜率 38%
   - 高 ATR (>0.8) 交易数：154 笔，胜率 58%
   - Filter 的效果：移除 80 笔低 ATR 交易
   - 新的总胜率：(234 - 80) / (234 - 80) 的正确计算... (让我重新算)
   - 旧的 Sharpe：1.2，新的 Sharpe：1.45（如果加 filter）
   - Trade-off：少交易 34%，但 Sharpe 提升 20%，可接受
   - Development validation：在未参与发现该 filter 的 `development_validation` 上筛选候选；一旦查看，该数据即记为 consumed，不是最终 holdout
   ```

6. **输出 attribution report**：
   ```
   # Trade Attribution Report for STRAT_RSI_001

   ## Winners vs Losers
   [详细对比表格]

   ## Candidate Filters
   1. ATR > 0.8: Sample reduction 34%, Sharpe gain 20%, VALID
   2. Trend mode: Only in uptrend: Sample reduction 40%, Sharpe loss 5%, INVALID
   3. Session filter: Skip first hour: Sample reduction 15%, Sharpe gain 8%, BORDERLINE

   ## Recommendations
   - Implement ATR filter (sample sufficient, gain confirmed)
   - Reject trend filter (not cost-effective)
   - Further test session filter in development_validation; preserve locked_final_holdout
   ```

7. **Commit 归因结果**：
   ```
   [ATTRIB] strategy_id=STRAT_RSI_001, action=attribution

   交易赢亏归因完成，发现 ATR 显著影响

   - 低 ATR 胜率 38%，高 ATR 胜率 58%
   - T-test p-value < 0.001（显著）
   - 候选 filter：ATR > 0.8，预期 Sharpe +20%
   ```

### 产出
- trade_attribution.md（完整对比和分析）
- cohort_analysis.csv（分组统计）
- candidate_filters.md（候选规则和评估）
- 一个 commit

### 通过标准
- 对比基于完整样本
- 区分可见特征和 hindsight
- 候选 filter 都有评估
- 样本数足够（每个子集 >= 30）

---

## Stage 6：Logic Refinement（逻辑优化）

### 目标
基于 Trade Attribution 的发现，提出改进规则的候选方案，每个候选都必须单独验证。禁止边看结果边改规则。

本阶段适用于新增 filter，也适用于 initial SL/TP、trailing、breakeven、timeout、分批出场、position sizing 或成交/成本规则变化。任何此类改动必须先写 `logic_change_proposal.md`，并按 `EXIT_RISK_AND_LOGIC_REFINEMENT_STANDARD.md` 重新执行 Stage 2 audit。

### 必做项

1. **候选规则清单**：根据 Stage 5 的发现，列出所有候选改进：
   ```
   Candidate 1: Add ATR filter (ATR > 0.8)
   Candidate 2: Add session filter (skip first hour of London)
   Candidate 3: Adjust RSI threshold from 30 to 25
   Candidate 4: Combine ATR filter + RSI threshold
   ```

2. **单个候选验证**：每个候选必须在冻结的规则基础上进行单独回测，不能混合测试多个候选。例如：
   ```
   Test Candidate 1 (ATR filter):
   - Base rule: unchanged
   - New rule: only enter if ATR > 0.8
   - Backtest result: trades 154 (from 234), win rate 58%, Sharpe 1.45
   - Conclusion: valid improvement
   
   (不测试 Candidate 1 + Candidate 2，先逐个确认)
   ```

3. **对比明确**：输出 base case 和 candidate case 的并排对比，例如：
   ```
   | Metric | Base | Candidate 1 | Improvement |
   |--------|------|------------|-------------|
   | Trades | 234  | 154        | -34%        |
   | Win%   | 48.3 | 58.0       | +9.7pp      |
   | Sharpe | 1.20 | 1.45       | +20%        |
   | MaxDD  | -8%  | -6%        | +2pp        |
   ```

4. **承认改进也可能是过拟合**。对于通过验证的候选：
   - 记录这是在训练集（backtest sample）上的结果
   - 明确说明需要在 OOS-Dev 进行筛选，最终完整候选还需在 `locked_final_holdout` 上仅评价一次
   - 不要在这个阶段宣布"策略改进成功"

5. **筛选候选**：只推进那些"样本足够 + 改进幅度明显 + 逻辑合理"的候选，例如：
   ```
   Candidate 1 (ATR filter): ACCEPT - 参与 Stage 7 参数优化
   Candidate 2 (session filter): REJECT - 改进仅 8%，不值得减少交易数 15%
   Candidate 3 (RSI threshold): ACCEPT - 与 attribution 发现一致
   Candidate 4 (combined): HOLD - 先单独验证 Candidate 1 和 3
   ```

6. **Commit 逻辑优化**：
   ```
   [LOGIC] strategy_id=STRAT_RSI_001, action=refine-rule

   基于 attribution 结果提出两个改进候选

   - Candidate 1: ATR filter (ATR > 0.8)
     Base Sharpe 1.20 → 1.45 (+20%)
     Base trades 234 → 154 (-34%)
     Status: ACCEPT
   
   - Candidate 2: Session filter
     Base Sharpe 1.20 → 1.28 (+8%)
     Status: REJECT (改进不足)
   ```

### 产出
- logic_refinement.md（候选规则和单独验证）
- 多个回测报告（base case + 每个 candidate case）
- 一个 commit

### 通过标准
- 每个候选都有单独的对比验证
- 不混合多个候选测试
- 承认结果还需要 OOS 验证

---

## Stage 7：Parameter Optimization（参数优化）

### 目标
对通过 Stage 6 的候选规则，进行参数微调和稳健性检验。参数优化不是找最高 Sharpe，而是检验逻辑假说在参数空间上的稳健性。此阶段必须维护 `data_usage_ledger.yaml`，且不能复用 Stage 5 已消费的数据冒充最终样本外。

### 必做项

1. **优化前写 optimization_protocol.md**：
   ```
   # Parameter Optimization Protocol for STRAT_RSI_001

   ## Objective
   Validate the robustness of ATR filter hypothesis across parameter space

   ## Search Space
   - ATR threshold: 0.6, 0.7, 0.8, 0.9, 1.0
   - RSI period: 12, 14, 16, 18
   - TP ratio: 1.3, 1.5, 1.7, 2.0
   - SL ratio: 0.8, 1.0, 1.2

   Total combinations: 5 * 4 * 3 * 3 = 180

   ## Optimization Metric
   Primary: Sharpe ratio (risk-adjusted return)
   Secondary: Calmar ratio (recovery speed)
   Tertiary: Sample count (must maintain > 50 trades)

   ## Data Split
   discovery_train: 2020-2023 (IS)
   development_validation: 2024 (OOS-Dev; consumed after candidate selection)
   locked_final_holdout: 2025-05-31 (OOS-Final; sealed until final candidate)

   ## Output
   Full candidate list with all 180 results
   Parameter plateau analysis
   IS/OOS-Dev comparison plus data_usage_ledger.yaml; OOS-Final is deferred until required development diagnostics are complete
   ```

2. **IS/OOS-Dev/OOS-Final/Forward-Live 四层分离**：
   - discovery_train：2020-2023，用于发现和参数搜索（IS）
   - development_validation：2024，用于筛选已声明候选（OOS-Dev，使用后 consumed）
   - locked_final_holdout：2025 至今，用于完全固定且已通过开发诊断的候选的一次性最终评价（OOS-Final，之前 sealed）
   - forward_live：冻结时刻之后新产生的数据，不属于历史 OOS
   - 时间上严格不重叠

3. **网格搜索或随机搜索**：在训练集上尝试所有参数组合（或采样），输出完整的候选列表：
   ```
   ATR_threshold | RSI_period | TP_ratio | SL_ratio | Train_Sharpe | Val_Sharpe | Trades
   0.6           | 14         | 1.5      | 1.0      | 1.25         | 1.10       | 340
   0.7           | 14         | 1.5      | 1.0      | 1.35         | 1.15       | 280
   0.8           | 14         | 1.5      | 1.0      | 1.45         | 1.25       | 154  ← Candidate
   ...
   ```

4. **参数高原检查**：
   - 观察参数变化时 Sharpe 如何变化
   - 如果最优参数处于搜索空间的边界（例如 ATR 的上限或下限），说明搜索空间可能太小
   - 检查是否存在"平台"（一个参数区间内 Sharpe 变化不大），说明参数鲁棒性较强

5. **Local Robustness**：
   - 最优参数周围的参数是否也有好的结果？
   - 如果最优参数孤立无援（周围参数都差很多），说明可能过拟合

6. **IS / OOS-Dev / OOS-Final 一致性**：
   - 用 IS 与 OOS-Dev 完成候选选择。若 Stage 8-10 仍作为进入冻结的开发门槛，先保持 OOS-Final sealed；这些诊断通过且候选不变后，再在 OOS-Final 上查看一次最终表现。
   - OOS-Final 不用于比较和重新选择全体候选；若最终候选失败，该版本失败。

7. **输出 optimization_report.md**：
   ```
   # Final Historical Evaluation Report for STRAT_RSI_001
   # Created only after Stage 8-10 development diagnostics pass unchanged

   ## Best Parameters
   ATR_threshold: 0.8
   RSI_period: 14
   TP_ratio: 1.5
   SL_ratio: 1.0

   ## Performance Comparison
   | Set | Sharpe | Calmar | Trades | MaxDD |
   |-----|--------|--------|--------|-------|
   | Train | 1.45 | 1.88 | 154 | -6% |
   | Validation | 1.25 | 1.52 | 98 | -7% |
   | OOS-Final / Locked Holdout | 1.10 | 1.35 | 52 | -8% |

   ## Interpretation
   Sharpe degrades from IS (1.45) to OOS-Final (1.10), suggesting some overfitting.
   This OOS-Final result is reported once and cannot be used to patch this version.

   ## Parameter Plateau
   [图表显示参数空间的 Sharpe 分布]
   ATR threshold 在 0.7-1.0 范围内都有不错的效果，说明参数鲁棒性好
   ```

8. **在 Stage 8-10 完成且候选未变后，Commit 最终历史评价结果**：
   ```
   [OOSFINAL] strategy_id=STRAT_RSI_001, action=locked-final-evaluation

   开发诊断完成后执行一次性 OOS-Final，Sharpe 1.10

   - 最优参数：ATR_threshold=0.8, RSI_period=14, TP_ratio=1.5, SL_ratio=1.0
   - IS Sharpe: 1.45 → OOS-Dev: 1.25 → OOS-Final: 1.10
   - 参数鲁棒性：ATR 范围 0.7-1.0 均可接受
   - OOS-Final trades: 52 (足够样本，已消费一次)
   ```

### 产出
- optimization_protocol.md
- full_candidate_list.csv（所有 180+ 参数组合的结果）
- optimization_report.md
- 一个 commit

### 通过标准
- 有清晰的优化协议和搜索空间定义
- IS/OOS-Dev/OOS-Final/Forward-Live 四层严格分离，并提交数据消费台账
- 输出完整的候选列表，不只是最优结果
- 参数鲁棒性检查完成
- 若 Stage 8-10 尚未完成，locked final holdout 保持 sealed；完成后仅打开一次，且无基于其结果的规则或参数补丁

---

## Stage 8：Walk-Forward / Out-of-Sample（回溯时间序列验证）

本阶段的诊断窗口只能来自已消费的开发历史，必须排除为 `locked_final_holdout` 保留的数据。如果该 holdout 已因兼容旧流程被打开，本阶段仍不得读取它来决定当前版本是否通过或如何修改。

### 目标
验证参数的时间稳定性。参数在不同时间窗口上是否保持有效，是否存在"参数漂移"（optimal parameters 随时间变化）。

### 必做项

1. **划分滚动窗口**。例如，用 12 个月的数据训练参数，然后在后续 3 个月上验证：
   ```
   Window 1: Train 2020-01 ~ 2020-12, Test 2021-01 ~ 2021-03
   Window 2: Train 2020-04 ~ 2021-03, Test 2021-04 ~ 2021-06
   Window 3: Train 2020-07 ~ 2021-06, Test 2021-07 ~ 2021-09
   ...
   Window N: Train 2023-01 ~ 2023-12, Test 2024-01 ~ 2024-03  # 仅示意，必须位于 consumed development history
   ```

2. **每个窗口独立优化**。在每个 train 段内重新搜索最优参数，然后在对应的 test 段上评估：
   ```
   Window 1:
   - Train on 2020 data → find best params (ATR=0.8, RSI=14, ...)
   - Test on 2021 Q1 → result Sharpe 1.20
   
   Window 2:
   - Train on 2020-2021 Q1 data → find best params (ATR=0.75, RSI=15, ...)  # 注意参数可能不同
   - Test on 2021 Q2-Q3 → result Sharpe 1.15
   ```

3. **参数稳定性分析**。查看每个窗口的最优参数是否相同：
   ```
   | Window | Best_ATR | Best_RSI | Best_TP | Sharpe |
   |--------|----------|----------|---------|--------|
   | 1      | 0.80     | 14       | 1.5     | 1.20   |
   | 2      | 0.75     | 15       | 1.5     | 1.15   |
   | 3      | 0.85     | 14       | 1.7     | 1.25   |
   | 4      | 0.80     | 14       | 1.5     | 1.18   |
   | Avg    | 0.80     | 14.25    | 1.55    | 1.19   |
   | Std    | 0.04     | 0.43     | 0.09    | 0.04   |
   ```
   - 如果 Std 很小，说明参数稳定，可以用平均参数作为最终参数
   - 如果 Std 很大，说明参数在不同时期有很大变化，可能是过拟合的迹象

4. **窗口稳定性**。检查 Test segment 上的 Sharpe 是否稳定：
   - 所有窗口的 test Sharpe 均值和标准差
   - 是否存在某个特定时期（例如 2022）性能急剧下降
   - 最坏窗口和最好窗口的 Sharpe 差异有多大

5. **输出 walk-forward report**：
   ```
   # Walk-Forward Analysis for STRAT_RSI_001

   ## Parameter Stability
   [上表所示]

   ## Test Performance
   Average Test Sharpe: 1.19 (std 0.04)
   Average Test Trades per Window: 28 (std 8)
   Consistency: Good (all windows > 1.1)

   ## Worst Window
   Window 2024 Q2: Sharpe 0.98 (market shock period?)
   Reason: High volatility spike, fewer profitable signals

   ## Conclusion
   Walk-forward test shows consistent out-of-sample performance,
   parameters stable across time, no significant drift
   ```

6. **Commit walk-forward 结果**：
   ```
   [WALKFW] strategy_id=STRAT_RSI_001, action=walk-forward

   回溯时间序列验证完成，参数稳定，OOS Sharpe 1.19

   - 12 个滚动窗口测试
   - 参数稳定性：ATR std 0.04，RSI std 0.43
   - Test Sharpe 均值 1.19 ± 0.04
   - 最坏窗口 Sharpe 0.98（2024 高波动期）
   ```

### 产出
- walk_forward_analysis.md
- walk_forward_details.csv（每个窗口的参数和结果）
- 一个 commit

### 通过标准
- 有至少 8-12 个滚动窗口
- 参数稳定性有定量衡量（std）
- 解释最坏窗口的性能原因
- OOS Sharpe 合理（不能远高于或远低于训练集）

---

## Stage 9：Environment Validation（环境验证）

本阶段用于过关或产生建议的分析仅可读取已消费开发历史，必须排除 `locked_final_holdout`。报告中的年份仅为格式示例，实际区间以 `data_usage_ledger.yaml` 为准。

### 目标
诊断策略在不同市场条件下的表现，找出策略擅长的环境和不擅长的环境。这是诊断目的，不是美化结果。禁止删除亏损环境然后宣布"策略改进"。

### 必做项

1. **ATR Regime 分层**：
   ```
   Low ATR (< 0.5 pips): trades 50, win rate 35%, Sharpe 0.8
   Medium ATR (0.5-1.0): trades 120, win rate 52%, Sharpe 1.4
   High ATR (> 1.0): trades 64, win rate 62%, Sharpe 1.8
   
   Conclusion: Strategy thrives in volatile conditions, struggles in calm markets
   ```

2. **Trend Regime 分层**：
   ```
   Uptrend (MA50 > MA200, slope positive): trades 100, win rate 55%, Sharpe 1.5
   Downtrend: trades 95, win rate 42%, Sharpe 0.7
   Range-bound: trades 39, win rate 48%, Sharpe 1.0
   
   Conclusion: Strategy is trend-directional, less effective in downtrends
   ```

3. **Session 分层**：
   ```
   London Open (08:00-10:00 UTC): trades 80, win rate 62%, Sharpe 1.9
   NY Session (13:00-16:00): trades 90, win rate 48%, Sharpe 1.1
   Asia Session (22:00-06:00): trades 64, win rate 40%, Sharpe 0.6
   ```

4. **Volatility Transition**：检查市场从低波动率切换到高波动率时会发生什么
   ```
   Transition period (volatility jump > 20%): trades 12, win rate 25%, Sharpe -0.5
   → Strategy struggles during Vol regime shifts, consider adding safety filter
   ```

5. **Compression / Expansion**：
   ```
   Compression (Bollinger Band width < 20pips): trades 35, win rate 38%, Sharpe 0.5
   Expansion (Bollinger Band width > 80pips): trades 85, win rate 58%, Sharpe 1.6
   → Signal very effective in expansion, dead in compression
   ```

6. **Year / Month 分层**：
   ```
   2020 (COVID): Sharpe 2.1
   2021 (Recovery): Sharpe 1.3
   2022 (Fed Hike): Sharpe 0.8
   2023 (Stabilization): Sharpe 1.2
   2024 (Normalize): Sharpe 1.1
   2025 YTD: Sharpe 0.95
   
   Trend: Performance declining year-over-year, possibly indicating regime change or adaptation
   ```

7. **样本数检查**。标记任何样本数 < 30 的 regime 为 "low_sample"，不能作为正式结论：
   ```
   High ATR + Compression + Asia Session: trades 8 (< 30, LOW SAMPLE, not reliable)
   ```

8. **Interaction Matrix**。构建多维表格，检查 regime 之间的互动：
   ```
            | London | NY | Asia |
   ---------|--------|-----|------|
   High ATR | 1.9S   | 1.1 | 0.6  |
   Med ATR  | 1.4S   | 0.9 | 0.5  |
   Low ATR  | 0.9    | 0.6 | 0.3  |
   
   (S = significant sample, blank = low sample)
   ```

9. **输出 regime validation report**：
   ```
   # Regime Validation Report for STRAT_RSI_001

   ## ATR Regime
   [表格和结论]

   ## Trend Regime
   [表格和结论]

   ## Session Analysis
   [表格和结论]

   ## Key Findings
   1. Strategy performs best in high ATR + London session
   2. Struggles in downtrend and Asia session
   3. Vulnerable during volatility transitions
   4. Performance declining 2023-2025, possibly market adaptation

   ## Recommendations
   - Consider adding downtrend filter to avoid worst-performing regime
   - Add volatility transition safeguard
   - Monitor performance drift in 2025+
   - Do NOT delete low-ATR regime; instead, adjust expectations for calm markets
   ```

10. **禁止过度优化**。不允许：
    - 删除整个 regime 后宣布"策略改进"（例如，移除 downtrend 环境）
    - 用 low_sample 环境构造新 filter
    - 在同一个 regime 上既发现特征又验证特征（双重使用问题）

11. **Commit 环境验证**：
    ```
    [REGIME] strategy_id=STRAT_RSI_001, action=regime-validation

    环境验证完成，策略在高波动伦敦时段最强

    - 高 ATR：Sharpe 1.8，低 ATR：Sharpe 0.8
    - 伦敦：Sharpe 1.9，亚洲：Sharpe 0.6
    - 上升趋势：胜率 55%，下降趋势：42%
    - 警告：2023-2025 性能下降，需监控市场适应
    ```

### 产出
- regime_validation_report.md（含所有分层和矩阵）
- regime_stratification.csv（详细数据）
- 一个 commit

### 通过标准
- 至少 5 个维度的分层分析（ATR、trend、session、volatility transition、year/month）
- 低样本环境标记为 low_sample，不作为正式结论
- 禁止删除亏损环境
- 有明确的机制诊断和改进建议

---

## Stage 10：Temporal Validation（时间验证）

本阶段用于过关或产生建议的分析仅可读取已消费开发历史，必须排除 `locked_final_holdout`。若需要把最终样本外做时间分解，只能作为一次 OOS-Final 报告的一部分且不得由此修改当前候选。

### 目标
检查策略在不同时间粒度上的稳定性（年度、季度、月度、滚动交易数）。这补充了 walk-forward 的时间序列验证，提供更细致的时间分解。

### 必做项

1. **年度分解**：
   ```
   2020: trades 35, win rate 54%, Sharpe 2.1, MaxDD -5%
   2021: trades 42, win rate 51%, Sharpe 1.4, MaxDD -7%
   2022: trades 38, win rate 45%, Sharpe 0.8, MaxDD -12%
   2023: trades 45, win rate 50%, Sharpe 1.2, MaxDD -8%
   2024: trades 48, win rate 49%, Sharpe 1.1, MaxDD -9%
   2025: trades 26, win rate 48%, Sharpe 0.95, MaxDD -7%
   
   Trend: Sharpe declining from 2.1 (2020) to 0.95 (2025), indicating regime drift
   ```

2. **季度分解**：
   ```
   Q1: Sharpe 1.2
   Q2: Sharpe 1.1
   Q3: Sharpe 1.3
   Q4: Sharpe 0.9
   
   Q4 consistently weaker, possibly year-end market behavior
   ```

3. **月度分解**：
   ```
   Jan: Sharpe 1.4, trades 18
   Feb: Sharpe 1.1, trades 20
   Mar: Sharpe 0.9, trades 19
   ...
   
   First quarter generally strong, March tends to be weak
   ```

4. **滚动 50 笔交易**：
   ```
   Trades 1-50: Sharpe 1.5
   Trades 51-100: Sharpe 1.3
   Trades 101-150: Sharpe 1.1
   Trades 151-200: Sharpe 0.9
   Trades 201-234: Sharpe 0.8
   
   Consistent degradation, suggesting market saturation or regime change
   ```

5. **滚动 100 笔交易**：
   ```
   Trades 1-100: Sharpe 1.4
   Trades 51-150: Sharpe 1.1
   Trades 101-200: Sharpe 0.95
   Trades 135-234: Sharpe 0.88
   ```

6. **Top 1% / 5% / 10% Removal**：
   ```
   Base (all trades): Sharpe 1.1, trades 234
   Remove top 1% (best 2 trades): Sharpe 1.05, trades 232 (-4.5%)
   Remove top 5% (best 12 trades): Sharpe 0.9, trades 222 (-18%)
   Remove top 10% (best 23 trades): Sharpe 0.6, trades 211 (-27%)
   
   Conclusion: Performance heavily dependent on best trades, lottery-like distribution
   ```

7. **Time Under Water（水下时间）**：
   ```
   Peak-to-trough drawdown: -12% (from 2022 Q3)
   Recovery time: 8 months
   Days underwater: 245 days / 1826 days = 13% of time
   
   Longest consecutive drawdown: -10%, 6 months (2022)
   ```

8. **输出 temporal validation report**：
   ```
   # Temporal Validation Report for STRAT_RSI_001

   ## Yearly Performance
   [表格]
   Trend: Declining from 2.1 to 0.95, -55% drop

   ## Rolling 50-Trade Window
   [表格]
   Consistent degradation, no recovery

   ## Top X% Removal
   Removing top 5% trades cuts Sharpe 18%, indicating concentration risk

   ## Time Under Water
   13% of time in drawdown, longest 8 months recovery

   ## Interpretation
   Performance shows clear temporal decay and concentration in early periods.
   Current 2025 performance (0.95) is lowest in history.
   Suggests either market adaptation or genuine regime change.
   ```

9. **Commit 时间验证**：
   ```
   [TEMPORAL] strategy_id=STRAT_RSI_001, action=temporal-validation

   时间验证完成，发现显著的性能衰减

   - 年度 Sharpe：2020 (2.1) → 2025 (0.95)，-55%
   - 滚动 50 笔：持续衰减，无反弹迹象
   - 水下时间：13%，最长 8 个月恢复期
   - 2025 性能创历史新低，需要警惕
   ```

### 产出
- temporal_validation_report.md（年/季/月/滚动窗口分解）
- rolling_window_analysis.csv
- 一个 commit

### 通过标准
- 至少 5 个时间维度的分析
- 明确指出性能趋势（上升、下降、波动）
- 解释水下时间和恢复周期
- top X% removal 分析完成

---

## Stage 11：Freeze Version（版本冻结）

### 目标
正式冻结已验证的策略版本，记录所有相关的代码、配置、数据、参数，生成版本号和 Git tag，为后续的前向验证和实盘部署做准备。冻结后，任何修改都必须新建版本。

### 必做项

1. **冻结代码**：
   - signal_engine.py 的最终版本，所有改进已完成
   - backtest.py 的最终版本，经过审计
   - config.yaml 的最终参数
   - 生成 code hash：`sha256(signal_engine.py + backtest.py)`

2. **冻结配置**：
   - 生成 config hash：`sha256(config.yaml)`
   - 记录所有参数：ATR_threshold, RSI_period, TP_ratio, SL_ratio, commission model 等

3. **冻结数据**：
   - 数据起止日期：2020-01-01 to 2025-05-31
   - 数据来源：（例如 oanda, interactive brokers）
   - 数据快照 hash（如果是本地数据文件）

4. **冻结策略规则**：
   - Entry rule：明确的英文或伪代码表示
   - Exit rule：明确的出场逻辑
   - Risk management：SL/TP、trailing/breakeven/timeout（如有）、R 定义、头寸大小和风险上限
   - Execution model：信号决策时点、fill 时点、bid/ask、gap 与同 bar SL/TP collision 规则
   - Conflict rule：如何处理冲突持仓

5. **生成冻结 manifest 和版本号**：格式为 `v<major>.<minor>`，例如 `v0.1`。第一个发布版本通常是 v0.1。`version.json` 在 freeze commit 中记录文件/config/data hash、规则和预定 tag；它不能预知并包含承载其自身的 commit hash。实际 frozen commit hash 由随后的 Git tag 和 registry 记录。
   ```json
   {
     "version": "0.1",
     "frozen_tag": "v0.1-frozen",
     "frozen_timestamp": "2025-06-01 10:30:00 UTC",
     "code_hash": "sha256:...",
     "config_hash": "sha256:...",
     "data_snapshot_hash": "sha256:...",
     "entry_rules": "RSI(14) < 30 on H1, ATR > 0.8",
     "exit_rules": "TP at 1.5R or SL at 1.0R",
     "execution_model": "signal on bar t close, market fill on first executable quote of bar t+1, SL-first on ambiguous OHLC collision",
     "cost_model": "bid_ask=0.0002, commission=0.001",
     "conflict_rules": "no concurrent long/short",
     "signal_engine_version": "0.1",
     "backtest_engine_version": "v1.0",
     "data_start": "2020-01-01",
     "data_end": "2025-05-31",
     "framework_start_time": "2025-06-01 11:00:00 UTC"
   }
   ```

6. **提交 manifest 并生成 Git tag**：
   ```
   git add version.json frozen_report.md data_usage_ledger.yaml
   git commit -m "[FREEZE] strategy_id=STRAT_RSI_001, version=v0.1"
   git rev-parse HEAD  # 此输出为 frozen_commit，写入 registry 与 tag annotation
   git tag -a v0.1-frozen -m "Freeze v0.1: RSI oversold strategy, audit pass, walk-forward pass, regime validation pass"
   git push origin v0.1-frozen
   ```

7. **创建 frozen 分支**（可选但推荐）：
   ```
   git checkout -b frozen-v0.1
   git push origin frozen-v0.1
   ```
   frozen 分支被标记为只读，任何修改都被禁止。

8. **生成冻结报告**。汇总所有从 Stage 1 到 Stage 10 的关键发现：
   ```
   # Freeze Report for STRAT_RSI_001 v0.1

   ## Strategy Summary
   RSI(14) < 30 oversold reversal strategy on EUR/USD H1

   ## All Stages Status
   ✓ Stage 1: Hypothesis - RSI oversold reversal
   ✓ Stage 2: Execution Audit - PASS
   ✓ Stage 3: Event Study - Win rate 48%, expectancy +0.25R
   ✓ Stage 4: Fixed Rule Backtest - Sharpe 1.2, trades 234
   ✓ Stage 5: Trade Attribution - High ATR has 62% win rate, low ATR 35%
   ✓ Stage 6: Logic Refinement - ATR filter accepted
   ✓ Stage 7: Parameter Optimization - Best params: ATR=0.8, RSI=14, TP=1.5, SL=1.0
   ✓ Stage 8: Walk-Forward - OOS Sharpe 1.19, parameters stable
   ✓ Stage 9: Environment Validation - Best: London + high ATR (1.9), Worst: Asia + low ATR (0.3)
   ✓ Stage 10: Temporal Validation - Declining trend 2020 (2.1) to 2025 (0.95)

   ## Key Metrics
   - Backtest Sharpe: 1.2
   - Holdout Sharpe: 1.1
   - Walk-Forward OOS Sharpe: 1.19
   - Average trades per month: 4.6
   - Max drawdown: -12% (2022)
   - Recovery time: 8 months

   ## Frozen Parameters
   version = v0.1
   ATR_threshold = 0.8
   RSI_period = 14
   TP_ratio = 1.5
   SL_ratio = 1.0

   ## Risk & Limitations
   1. Declining performance 2020-2025, regime drift suspected
   2. Concentration in best trades (top 5% accounts for 18% Sharpe)
   3. Vulnerable in downtrends and low volatility
   4. Performance drops 40% in Asia session

   ## Recommendation
   Ready for forward-live deployment, but monitor regime change closely.
   Consider adding downtrend filter or session-based adjustment in future versions.
   ```

9. **记录冻结提交标识**。冻结 commit 产生后，将其记录到中央 registry、freeze report 外部审计记录和 forward 配置；不要再修改已经打 tag 的 frozen commit 来回填其自身 hash。

10. **更新 strategy_registry.yaml**：
    ```yaml
    - strategy_id: STRAT_RSI_001
      root_path: D:\MT5\strategies\STRAT_RSI_001
      git_repo: https://github.com/user/STRAT_RSI_001
      git_branch: main
      current_stage: stage_11_frozen
      current_status: frozen
      frozen_commit: a1b2c3d4e5f6
      frozen_tag: v0.1-frozen
      frozen_timestamp: 2025-06-01 10:30:00
      key_files:
        - signal_engine.py (hash: ...)
        - config.yaml (hash: ...)
      last_result: Walk-Forward Sharpe 1.19
      next_action: forward-live deployment
      owner_machine: machine_001
      last_updated: 2025-06-01
    ```

### 产出
- version.json（完整的冻结信息）
- frozen_report.md（汇总报告）
- Git tag（v0.1-frozen）
- 可选的 frozen-v0.1 分支
- 更新的 strategy_registry.yaml

### 通过标准
- 所有 Stage 1-10 都通过
- version.json 记录冻结 manifest（code hash、config hash、framework_start_time），registry/tag annotation 记录 frozen commit hash
- Git tag 已创建并 push
- 冻结报告明确写出风险和局限性，不隐瞒缺点

---

## Stage 12：Forward-Live（前向交易）

### 目标
记录 framework_start_time 之后新产生的信号和交易，严格分离历史数据和实时数据，通过 Gate A 或 Gate B 检验策略在未见过的市场中的表现。

### 必做项

1. **创建 forward-live 分支**：
   ```
   git fetch --tags
   git switch --detach v0.1-frozen
   git switch -c forward-v0.1  # 明确从 frozen tag 派生，不从漂移中的 main 派生
   ```

2. **初始化 forward-live 配置**：
   ```json
   {
     "forward_live_config": {
       "strategy_id": "STRAT_RSI_001",
       "version": "v0.1",
       "frozen_commit": "a1b2c3d4",
       "frozen_tag": "v0.1-frozen",
       "framework_start_time": "2025-06-01 11:00:00 UTC",
       "signal_engine_version": "0.1",
       "parameters": {
         "ATR_threshold": 0.8,
         "RSI_period": 14,
         "TP_ratio": 1.5,
         "SL_ratio": 1.0
       }
     }
   }
   ```

3. **严格的时间约束**。forward-live 数据只包含 `framework_start_time` 之后新产生的信号。任何历史回填都被禁止。

4. **创建 forward-live 数据文件**：
   ```
   forward_live_signals.csv:
   signal_timestamp, symbol, timeframe, signal_type, signal_price, ...
   (只包含 2025-06-01 11:00:00 之后的信号)

   forward_live_trades.csv:
   entry_time, entry_price, exit_time, exit_price, pnl, pnl_R, ...
   (只包含 2025-06-01 11:00:00 之后的交易)
   ```

5. **每日（或每周）更新**。新信号和新交易追加到 CSV，定期 commit：
   ```
   [FORWARD] strategy_id=STRAT_RSI_001, action=forward-live

   新增 2 笔信号，1 笔交易

   - 交易日期：2025-06-10
   - 新交易：entry 1.0850, exit 1.0875, +25 pips, +0.5R
   - 当前 Gate 进度：3/30 (Gate A)
   ```

6. **Gate 检查**：
   ```
   Gate A: 3 个月 + 30 笔交易
   Gate B: 50 笔交易
   
   当前进度：
   - 实时交易数：35 笔（Gate A 通过）
   - 自 framework_start_time：2025-06-01 至 2025-09-15（超过 3 个月）
   - 胜率：48.6% (17 win / 35 total)
   - 平均 R：+0.18R
   - 当月收益：+1.2%
   
   Status: GATE A PASS
   ```

7. **完整性检查**。每次添加新数据，运行完整性检查脚本：
   ```
   ✓ 所有新信号时间戳 >= framework_start_time
   ✓ 新交易不覆盖历史数据
   ✓ 信号逻辑与冻结版本一致（验证 commit hash）
   ✓ 费用模型与冻结 config 一致
   ✓ 没有未来数据污染（检查 exit bar 是否使用当日未来数据）
   ```

8. **forward-live 分支保护**：
   ```
   forward-live 分支不允许 merge 回 main 或 frozen 分支
   不允许修改冻结逻辑或参数
   只允许追加新信号和新交易
   任何改进必须新建版本（v0.2）
   ```

9. **输出 forward-live 状态报告**：
   ```
   # Forward-Live Status for STRAT_RSI_001 v0.1

   ## Gate Progress
   ✓ Gate A (3M + 30T): PASS (3.5 months, 35 trades)
   - Gate B (50T): 70% (35/50)

   ## Current Metrics
   - Trades: 35
   - Win rate: 48.6%
   - Profit factor: 1.8
   - Expectancy: +0.18R per trade
   - Max drawdown: -6%
   - Monthly return: +1.2%

   ## Comparison with Backtest
   | Metric | Backtest | Forward-Live | Difference |
   |--------|----------|--------------|-----------|
   | Win% | 48.3% | 48.6% | +0.3pp |
   | Avg R | +0.25R | +0.18R | -0.07R |
   | Sharpe | 1.20 | 0.95 (est.) | -0.25 |

   Status: In line with expectations, no red flags
   ```

10. **Commit forward-live 更新**：每次通过 Gate 检查时标记：
    ```
    [FORWARD] strategy_id=STRAT_RSI_001, action=forward-live

    前向交易：Gate A 通过

    - 交易数：35 笔
    - 胜率：48.6%
    - 期望值：+0.18R
    - 性能与回测一致，无明显偏差
    - 下一个目标：Gate B (50 笔)
    ```

### 产出
- forward_live_config.yaml（冻结配置）
- forward_live_signals.csv（所有新信号）
- forward_live_trades.csv（所有新交易）
- forward_live_state.json（当前状态）
- gate_status_reports.md（Gate 进度）
- 多个 commit（每次 Gate 检查或定期更新）

### 通过标准
- 数据仅来自 framework_start_time 之后
- Gate A 或 Gate B 通过（至少 3 个月或 50 笔交易）
- forward-live 性能与 backtest 一致（不能好很多，也不能坏很多）
- 完整性检查通过，没有数据污染

---

## Stage 13：Portfolio / Deployment（投资组合与部署）

### 目标
评估单个策略与其他策略的协同性、组合风险、同时持仓、最终确认是否适合实盘部署。

### 必做项

1. **策略相关性分析**。如果已有其他正式策略，计算 forward-live 收益的相关性：
   ```
   Correlation Matrix:
                  STRAT_RSI_001  STRAT_MACD_002  STRAT_BB_003
   STRAT_RSI_001      1.0           0.15           0.22
   STRAT_MACD_002     0.15          1.0            0.65
   STRAT_BB_003       0.22          0.65           1.0
   
   Average correlation: 0.30 (good diversification, low correlation)
   ```

2. **同时持仓检查**：
   ```
   最多同时持仓笔数（所有策略）：5 笔
   平均同时持仓：2.3 笔
   总账户风险：5 * 1.0R (SL) = 5.0R worst case
   
   对于账户大小 10,000 USD，1R = 100 USD，最大风险 500 USD (5%) → 可接受
   ```

3. **组合 Sharpe 和 Calmar**（如果有多个策略）：
   ```
   单个策略：
   - STRAT_RSI_001: Sharpe 1.2, Calmar 1.5
   - STRAT_MACD_002: Sharpe 0.9, Calmar 1.2
   - STRAT_BB_003: Sharpe 1.4, Calmar 1.8
   
   组合（等权重）：
   Sharpe: 1.3 (better than average, 低相关性好处)
   Calmar: 1.6
   Max drawdown: -7% (better than worst individual, -12%)
   ```

4. **部署检查清单**：
   ```
   ✓ 策略已通过 Stage 2 Execution Audit
   ✓ 策略已通过 Stage 8 Walk-Forward 验证
   ✓ 策略已通过 Stage 11 Freeze
   ✓ 策略已通过 Stage 12 Forward-Live Gate A 或 Gate B
   ✓ 单个策略与其他策略相关性可接受
   ✓ 组合持仓和回撤风险可控
   ✓ 费用模型与实际经纪商一致
   ✓ 账户规模足以承受最大回撤
   ```

5. **实盘配置**。准备最终的部署参数：
   ```json
   {
     "strategy_id": "STRAT_RSI_001",
     "version": "v0.1",
     "live_status": "approved_for_deployment",
     "account_size": 10000,
     "risk_per_trade": 0.01,
     "max_concurrent_trades": 5,
     "execution_broker": "oanda",
     "slippage_model": "fixed_spread_0.0002",
     "commission": 0.001,
     "max_account_drawdown_tolerance": 0.20,
     "monitoring_frequency": "daily",
     "alert_rules": "drawdown > 15%, Sharpe < 0.5 (monthly)"
   }
   ```

6. **部署报告**：
   ```
   # Deployment Report for STRAT_RSI_001 v0.1

   ## Approval Status
   ✓ APPROVED FOR LIVE TRADING

   ## Strategy Performance Summary
   Backtest Sharpe: 1.2
   Forward-Live Sharpe (30 trades): 0.95
   Forward-Live Win Rate: 48.6%

   ## Risk Assessment
   Max Drawdown (backtest): -12%
   Expected Monthly Return: +1.2%
   Sharpe Degradation: 1.2 → 0.95 (20% drop, acceptable)

   ## Portfolio Integration
   Correlation with STRAT_MACD_002: 0.15 (good)
   Correlation with STRAT_BB_003: 0.22 (good)
   Portfolio Sharpe: 1.3 (improved)

   ## Execution Plan
   - Account size: 10,000 USD
   - Risk per trade: 1% (100 USD)
   - Max concurrent: 5 trades
   - Monitoring: Daily Sharpe and drawdown

   ## Monitoring Rules
   - Alert if monthly Sharpe < 0.5
   - Alert if drawdown > 15%
   - Monthly review of win rate and regime shifts
   - Quarterly re-validation against Stage 9 (environment) and Stage 10 (temporal)

   ## Deployment Date
   2025-06-15
   ```

7. **实盘监控**。部署后，持续监控：
   - 月度 Sharpe 和胜率
   - 实际费用 vs 预期费用
   - 执行滑点 vs 预期滑点
   - 账户最大回撤
   - regime 变化的迹象

8. **Commit 部署决策**：
   ```
   [DEPLOY] strategy_id=STRAT_RSI_001, action=deployment-approved

   策略 v0.1 通过全部验证，批准实盘部署

   - Backtest Sharpe: 1.2
   - Forward-Live: 35 笔，Sharpe 0.95
   - 组合相关性：0.15-0.22（良好分散）
   - 组合 Sharpe：1.3（改善）
   - 部署日期：2025-06-15
   ```

### 产出
- deployment_report.md（完整部署报告）
- portfolio_correlation_analysis.csv
- live_trading_config.json
- monitoring_checklist.md
- 一个 commit 记录部署决策

### 通过标准
- 单个策略已通过所有前序 Stage
- 与其他策略的相关性可接受（< 0.5）
- 组合回撤和持仓风险可控
- 部署检查清单全部勾选

---

## 总结：完整闭环流程

```
Stage 0: Registry → Stage 1: Hypothesis → Stage 2: Audit
   ↓
Stage 3: Event Study → Stage 4: Fixed Rule → Stage 5: Attribution
   ↓
Stage 6: Logic Refine → Stage 7: Optimization → Stage 8: Walk-Forward
   ↓
Stage 9: Regime Validation → Stage 10: Temporal Validation
   ↓
Stage 11: Freeze → Stage 12: Forward-Live (Gate A/B) → Stage 13: Deployment
```

每个 Stage 都有明确的产出和通过标准，不允许跳过。任何违反流程的决策都会导致过拟合或执行偏差。这套流程的目标是减少过拟合、减少执行偏差、减少跨目录混乱。
