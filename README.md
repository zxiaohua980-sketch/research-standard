# MT5 量化策略研究规范体系

## 核心哲学

**策略开发不是回测-优化-实盘，而是：假说-审计-事件研究-固定规则-赢亏归因-逻辑优化-OOS/WF-环境与时间验证-冻结-前向。**

这套规范体系的唯一目标是：减少过拟合、减少执行偏差、减少跨目录混乱。不是为了提高回测收益，而是为了确保：
1. 每个决策都有数据支撑
2. 每个结果都能被重现
3. 每个策略都能被追踪
4. 每个版本都能被锁定

---

## Codex / Claude 自动生效入口

- Codex 全局入口：`C:\Users\86640\.codex\AGENTS.md`，使新的 Codex 对话在遇到自动化交易任务时先加载本规范。
- MT5 目录入口：`D:\MT5\AGENTS.md`，覆盖 `D:\MT5` 下所有策略项目。
- 外置登记项目必须在自身目录放置 `AGENTS.md` 指针，或迁入 `D:\MT5` 管理范围。
- 本目录中的 `AGENTS.md` 是研究门禁的权威正文；其他入口只负责强制找到它。

---

## 文档清单

### 0. GIT_AND_REPRODUCIBILITY_STANDARD.md
**Git 与可复现性规范** — 量化研究的基础设施

建立统一的 Git、版本控制、可复现性规范。核心思想：量化研究不是"当前目录里的代码"，而是：某个 commit + 某个 config + 某个数据快照 + 某个输出结果的完整四元组。

**关键内容**：
- 为什么 Git 是必需的基础设施
- Git 初始化和 .gitignore 规范
- Commit message 格式和版本绑定
- Branch 管理策略（main/develop/feature/frozen/forward）
- Frozen 版本的 Git tag 和分支保护
- Forward-live 分支的管理
- Cross-machine 同步规范
- Claude Code 的 Git 行为规范
- 可复现性检查清单

**何时使用**：任何新策略初始化时必读。每次 commit 时参考。

---

### 1. CLAUDE.md
**Claude Code / Codex 策略研究最高优先级指令**

这是 Claude Code 执行任何策略任务时的最高约束。包含十大禁区和每次接收任务时的必做检查表。

**十大禁区**：
1. 禁止在没有执行审计的情况下相信回测结果
2. 禁止在没有 Trade Attribution 的情况下新增 filter
3. 禁止用全样本选择参数
4. 禁止把历史回填当成 forward validation
5. 禁止在 forward-live 阶段修改 frozen strategy
6. 禁止用少量连亏作为改策略理由
7. 禁止为了提高 PF 盲目扫参
8. 每一个新策略必须先登记到 registry
9. 每一个策略必须有独立目录
10. 每一次策略规则变化必须开启新版本或新分支

**何时使用**：Claude Code 接到每个策略任务时必读。

---

### 2. RESEARCH_WORKFLOW.md
**完整量化策略研究流程（Stage 0-13）**

从项目注册到前向交易的完整 13 阶段流程。每个阶段都有明确的目标、必做项、产出、通过标准。

**13 个阶段**：
- Stage 0: Project Registration（项目注册）
- Stage 1: Strategy Hypothesis（策略假说）
- Stage 2: Execution Audit（执行审计）
- Stage 3: Event Study（事件研究）
- Stage 4: Fixed-Rule Backtest（固定规则回测）
- Stage 5: Trade Attribution（交易赢亏归因）
- Stage 6: Logic Refinement（逻辑优化）
- Stage 7: Parameter Optimization（参数优化）
- Stage 8: Walk-Forward / OOS（回溯时间序列）
- Stage 9: Environment Validation（环境诊断）
- Stage 10: Temporal Validation（时间诊断）
- Stage 11: Freeze Version（版本冻结）
- Stage 12: Forward-Live（前向交易）
- Stage 13: Portfolio / Deployment（组合与部署）

**何时使用**：开发新策略时，按照这个流程逐个阶段完成。

---

### 3. STRATEGY_DEVELOPMENT_STANDARD.md
**策略开发项目结构规范**

规范每个策略目录的结构、文件职责、代码分层。信号引擎、回测引擎、诊断脚本、前向运行必须分离。

**核心内容**：
- 必需的目录结构
- signal_engine.py 职责
- backtest.py 职责
- config.yaml 职责
- tests/ 单元测试
- analysis/ 诊断脚本
- forward_live/ 前向交易
- 文件职责矩阵

**何时使用**：创建新策略项目时遵循这个结构。避免把所有逻辑混在一个脚本。

---

### 4. TRADE_ATTRIBUTION_STANDARD.md
**交易赢亏归因标准（Stage 5）**

最重要的文档。对比盈利单和亏损单，找出成功和失败的共同特征，区分入场前可见特征与事后 hindsight 特征。这是决定是否添加新 filter 的唯一根据。

**关键内容**：
- 每笔交易必须记录的属性（30+ 个字段）
- 核心对比分析（Winners vs Losers, TP Winners vs SL Losers 等）
- 可见特征 vs Hindsight 特征的严格区分
- 候选 filter 的七层检验
- 当失败者和成功者特征差异极小时的处理

**何时使用**：Stage 5 时必读。任何想要新增 filter 时参考。

---

### 5. OPTIMIZATION_POLICY.md
**参数优化政策（Stage 7）**

参数优化只能在 attribution 之后进行。禁止全样本优化、禁止看 OOS 结果反复调参、禁止搜索空间无限扩大。目标是检验逻辑假说的稳健性，不是找最高 Sharpe。

**关键内容**：
- 禁止的优化方式（5 种常见错误）
- 正确的优化流程（编写协议、网格搜索、IS/OOS-Dev/OOS-Final/Forward 四层分离、参数高原检查）
- Parameter plateau 和 local robustness 分析
- Optimization protocol 的编写

**何时使用**：Stage 7 参数优化时必读。

---

### 6. REGIME_VALIDATION_STANDARD.md
**环境验证规范（Stage 9）**

诊断策略在不同市场条件下的表现。禁止删除亏损环境后宣布"策略改进"。

**五个必须分析的维度**：
- ATR Regime（波动率）
- Trend Regime（趋势）
- Session（交易时段）
- Volatility Transition（波动率切换）
- Compression / Expansion（压缩/扩张）

**关键内容**：
- Low sample 处理（样本数 < 30 标记为不可靠）
- Interaction matrix（多维交叉分析）
- Year/Month 分解
- 禁止的做法（删除亏损环境、用小样本构造 filter）

**何时使用**：Stage 9 环境验证时参考。

---

### 7. FORWARD_VALIDATION_STANDARD.md
**前向验证规范（Stage 12）**

定义 forward-live 的严格标准。仅有 `framework_start_time` 之后新产生的信号和交易才算 forward-live。

**关键内容**：
- 四种验证形式的区别（历史回填、固定规则、Walk-Forward、Forward-Live）
- Framework start time 的定义和不可变性
- Forward-live 的四大约束（无回填、信号来自冻结代码、无参数调整、无规则调整）
- Forward-live 数据结构（config、signals、trades、state）
- Gate A（3 个月 + 30 笔）和 Gate B（50 笔）的定义
- Forward-live 监控规范

**何时使用**：Stage 11 冻结后、Stage 12 前向开始前必读。

---

### 8. VERSIONING_AND_FREEZE_POLICY.md
**版本控制与冻结政策（Stage 11）**

策略冻结的完整规范。包括版本号、Git tag、冻结内容清单、version.json 完整结构、修改冻结策略的流程。

**关键内容**：
- 版本号规范（v<major>.<minor>.<patch>）
- 冻结内容清单（代码、参数、规则、成本模型、数据范围、关键指标）
- Git tag 规范（v0.1-frozen）
- Frozen branch 管理
- version.json 的完整内容
- 版本生命周期
- 修改冻结策略的正确流程

**何时使用**：Stage 11 冻结时必读。

---

### 9. PROJECT_REGISTRY_STANDARD.md
**项目登记规范（Stage 0）**

所有策略都必须登记到中央 registry。Registry 是跨目录协调的唯一权威记录。

**关键内容**：
- Registry 文件位置
- Registry 条目的必需字段（30+ 个字段）
- Registry 的维护规则（创建、更新、关键转折点）
- Registry 的查询和报告
- Registry 的完整性检查脚本
- Registry 条目示例（不同阶段）

**何时使用**：创建新策略（Stage 0）时必读。每完成一个 Stage 时更新。

---

### 10. README.md（本文件）
**总体指南和文档索引**

---

### 11. EXIT_RISK_AND_LOGIC_REFINEMENT_STANDARD.md
**成交、止损止盈、风险与逻辑调整规范**

定义 bar/tick 成交时点、bid/ask 与费用处理、同一 bar 触及 SL/TP 的处理方式、exit/risk attribution、逻辑变更提案、重新审计、冻结与 live 安全控制。

**何时使用**：任何涉及 entry fill、SL、TP、breakeven、trailing、timeout、position sizing、cost model 或 live safeguard 的任务必读。

---

### 12. DATA_SPLIT_AND_OOS_POLICY.md
**样本内、样本外与数据消费政策**

明确 IS、OOS-Dev、OOS-Final、WF-OOS 和 Forward-Live 的边界，并要求用 `data_usage_ledger.yaml` 记录哪些历史数据已经被用于发现、筛选或最终评价。

**何时使用**：Stage 1 切分数据时建立；Stage 5-12 每次声明 OOS 结果或查看未开封数据之前必读。

---

## 快速导航

### 如果你是...

**新手研究员**：
1. 先读 CLAUDE.md（了解十大禁区）
2. 再读 GIT_AND_REPRODUCIBILITY_STANDARD.md（了解 Git 规范）
3. 然后读 RESEARCH_WORKFLOW.md（了解完整流程）

**要开发新策略**：
1. 按照 PROJECT_REGISTRY_STANDARD.md 注册新策略
2. 按照 STRATEGY_DEVELOPMENT_STANDARD.md 建立项目结构
3. 按照 RESEARCH_WORKFLOW.md 从 Stage 0 开始逐步推进

**要做 Trade Attribution**：
- 必读 TRADE_ATTRIBUTION_STANDARD.md（最重要的文档）

**要做参数优化**：
- 必读 OPTIMIZATION_POLICY.md（避免常见错误）

**要进入前向交易**：
1. 先完成 VERSIONING_AND_FREEZE_POLICY.md（冻结策略）
2. 再按照 FORWARD_VALIDATION_STANDARD.md（前向交易）

---

## 核心概念速查表

| 概念 | 定义 | 何时使用 |
|------|------|--------|
| **Framework Start Time** | 历史分析和前向验证的分界线，之前的都是 backtest，之后的都是 forward-live | Stage 11 冻结时设置，Stage 12 前向时严格遵守 |
| **Frozen Strategy** | 代码、参数、规则全部冻结的版本，用 Git tag 标记（v0.1-frozen） | Stage 11 完成，进入 Stage 12 |
| **Forward-Live** | framework_start_time 之后新产生的信号和交易，真实市场、未知未来 | Stage 12，通过 Gate A 或 B 后可考虑实盘 |
| **Gate A** | 3 个月 + 30 笔交易，第一个 forward-live 成熟的标志 | Stage 12 评估是否继续 |
| **Gate B** | 50 笔交易，更充分的 forward-live 证据 | Stage 12 评估是否可实盘 |
| **Trade Attribution** | 对比 winners 和 losers，找出可见特征，决定是否加 filter | Stage 5，必经环节 |
| **Strategy Version** | 用 v<major>.<minor> 标记，v0.1 是首个发布版 | Stage 11 冻结、后续版本升级时 |
| **Registry** | 中央策略登记簿，记录所有策略的状态、版本、责任人 | Stage 0 创建、每个 Stage 完成后更新 |
| **Look-Ahead Bias** | 在回测中使用了未来数据的错误，必须在 Stage 2 Execution Audit 中检查 | 每个新回测、新数据源时检查 |
| **Overfitting** | 参数过度优化到特定历史数据，导致样本外性能急剧下降 | Stage 7 优化时严防，Stage 8 WF 评估 |

---

## 一句话总结

**如果结果不能定位到 commit hash，则结果不可信。**

所有的分析、回测、优化、诊断都必须能够回答："这个结果来自哪个 commit？使用的是什么参数？基于什么数据？生成时间是什么时候？"。没有这四样信息，研究无法复现，无法审计，无法信任。

---

## 最后的话

这套规范不是为了增加工作量，而是为了减少过拟合和执行偏差。每一个阶段、每一个检查、每一个文档都是为了确保：
- **你的决策是数据驱动的，而不是直觉驱动的**
- **你的结果是可重现的，而不是一次性的**
- **你的版本是可追踪的，而不是丢失的**

如果在执行过程中发现规范有不合理之处，或者有新的最佳实践可以改进规范，欢迎反馈和更新。规范存在于这些文档中，文档存在于 Git 中，版本控制确保我们能够追踪规范本身的演进。

量化研究的成功不是看最高的回测 Sharpe，而是看：当市场条件改变时，策略是否还能按预期运行。这套规范的全部目的就是帮助我们实现这一点。

---

**创建时间**：2025-06-01
**最后更新**：2025-09-15
**维护者**：Claude Code, Quantitative Research Team
