# 三阶段策略研发流水线

## 目标

本流程把策略研发分成三个阶段：

1. **快速开发测试阶段**：优先发现盈利点，允许快速假设、快速编码、快速测试和反复归因。
2. **成型后版本迭代阶段**：把有潜力的想法变成可审计、可回溯、可比较的候选策略。
3. **EXE 模拟下单阶段**：把冻结候选打包成可复制运行的 dry-run/demo runtime，验证运行安全和模拟下单链路。

制度的作用不是替代研究判断，而是保障：

- 代码不犯致命错误；
- 文件和版本不乱；
- 每个结果可以回溯到代码、配置、数据和时间；
- 多周期特征只能使用决策当时已经完成且可见的数据；
- 每个正式版本都有自己的文件夹，不能读取其他版本的回测数据和记录；
- 临时、无效、半截输出能及时清理，不让文件垃圾污染下一轮研究；
- 探索结果不会被误标为 OOS、forward-live 或可实盘证据。

---

## 分级门禁：研究效率优先

制度必须围绕策略研究服务，不能把 Phase 3 的严谨度提前压到 Phase 1。默认分级：

1. **Phase 1 轻门禁**：允许单文件快速写代码、快测、盈亏比测试和多维归因；不强制完整 registry、完整 ledger、完整报告。必须做到独立探索目录/文件、致命审计、证据降级和及时清理临时文件。
2. **Phase 2 中高门禁**：有潜力的想法进入候选迭代后，必须新版本子目录、复制父版本 active `.py` 为新版本单独文件、重新审计、版本隔离、归因记录和必要的 manifest。中央 registry 只在里程碑更新，不记录每次小试错。
3. **Phase 3 最高门禁**：冻结、逐根回测、Strict Audit Enforcement、runtime safety、EXE 打包、demo/dry-run 交付必须严格执行。

如果治理动作会阻断 Phase 1 的快速研究，优先选择“继续探索但降级证据标签”，不要停止写代码、归因和优化。只有进入 Phase 2 决策级候选、冻结、OOS、forward-live 或 runtime handoff 时，才强制完整门禁。

### 文件卫生原则

每轮结束要清理临时文件、半截输出、debug dump、未绑定 version/root/hash 的 loose `latest/final/copy/副本/saved_runs`。Phase 1 可以简单删除明显垃圾；Phase 2+ 对不确定文件先放入当前 `version_root/_trash_review/<timestamp>/`，并在 `CLEANUP_LOG.md` 或报告 cleanup section 记录。不得删除原始数据、ledger、manifest、审计/归因/replay 报告、冻结版本、forward-live 日志或 runtime 订单/对账证据。

---

## 横向强制模式：Strict Audit Enforcement Mode

当任务是审计、查未来函数、修复普通回测与逐根回测差异、加固、批准候选、MTF/pivot/swing/execution 检查、重放一致性检查或 runtime safety 检查时，三阶段流程必须临时切入 `STRICT_AUDIT_ENFORCEMENT_STANDARD.md`：

- 只允许最小安全补丁，不允许顺手优化 PF、胜率、RR、交易数量、参数或策略逻辑；
- 必须检查全局时间模型：`bar_open_time <= feature_available_at <= signal_time <= execution_time`；
- MT5 OHLC 的 `bar_close_time` 按下一根 bar 的 open time 理解；
- pivot/swing/structure 必须记录 detect/confirm/signal 时间顺序；
- 多周期特征必须证明 `feature_available_at <= decision_time/signal_time`；
- 逐根/增量 replay 与 batch 回测不一致时，默认视为 `REPAINTING_OR_LOOKAHEAD_FAIL`，除非能用保守执行/成本/gap 规则逐项解释；
- 修复 safety 缺陷后，缺陷引擎产生的所有 downstream metrics 作废并重新生成。

该模式不替代 Phase 1/2/3，而是审计任务的执行方式：先证明系统没有未来函数、时间错位、重绘、跨版本污染和执行模型错误，再继续探索、迭代或打包。

---

## Phase 1: 快速开发测试阶段

### 目标

快速判断一个假设有没有盈利潜力。此阶段允许反复试错，但所有输出必须标记为：

```text
exploratory
not decision-grade
not OOS
not forward-live
```

### 输入

每个想法先写一张轻量 `idea_card.md`：

- 假设；
- 交易对象；
- 周期；
- 目标胜率；
- 目标盈亏比；
- 预期交易数量；
- 入场逻辑；
- 初始 SL/TP 思路；
- 失效条件；
- 本轮要验证的问题。

### 允许

- 快速写信号代码和回测代码；
- 快速扫描多个想法；
- 使用开发数据做探索；
- 根据数量归因和亏损归因修改逻辑；
- 多轮重复：假设 -> 代码 -> 致命审计 -> 快测 -> 归因 -> 修改。

### 禁止

- 使用 locked final holdout；
- 宣称 OOS 有效、forward 有效或可实盘；
- 隐藏失败结果，只保留最好曲线；
- 用同一根 bar 的 close 同时产生信号并成交；
- 不计费用、点差和 SL/TP 冲突；
- 对 frozen 或 forward-live 策略直接改原版本。

### 致命审计

Phase 1 不要求完整正式审计报告，但每次快测前必须按 `STRICT_AUDIT_ENFORCEMENT_STANDARD.md` 做致命审计快检：

- 是否有未来函数或数据泄漏；
- 如果使用多周期，是否把未完成的高周期 bar 提前合并进低周期决策；
- bar-close 信号是否在下一根或下一可成交报价执行；
- 全局时间模型 `bar_open_time <= feature_available_at <= signal_time <= execution_time` 是否成立；
- pivot/swing/structure 是否在确认完成后才允许出信号；
- SL/TP 方向是否合法；
- 同一根 OHLC 同时触及 SL/TP 时是否使用预声明规则；
- 费用、点差、滑点是否至少有保守估计；
- 是否有重复开仓、冲突持仓或未平仓样本切割；
- 交易数量是否足以支持本轮观察。

### 快速测试指标

最小输出：

- trades；
- win_rate；
- avg_win_R；
- avg_loss_R；
- EV_R；
- PF；
- max_drawdown；
- max_consecutive_losses；
- cost_sensitivity；
- top_5pct_removed_EV_R；
- monthly/yearly stability。

### 盈亏比测试

固定入场和初始风险定义，扫描多个目标 R：

```text
0.5R, 1R, 1.5R, 2R, 3R, 4R, 6R
```

记录：

| target_R | trades | hit_rate | breakeven_win_rate | EV_R | PF | max_dd_R | top_5pct_removed_EV_R |
|----------|--------|----------|--------------------|------|----|----------|------------------------|

重点不是找单点最佳，而是找盈亏比平台：

- 多个相邻 R 都能赚钱：可能存在真实边；
- 只有一个 R 点赚钱：高度疑似偶然或过拟合；
- 高 R 赚钱但剔除 top 5% 后崩掉：依赖少数大单；
- 低 R 赚钱高 R 不赚钱：信号偏短冲；
- 高 R 赚钱低 R 不赚钱：可能过早止盈。

### 多维归因

每轮快测必须至少从这些角度看盈利和亏损：

- 结构：突破、回踩、假突破、压缩、扩张、反转、趋势延续；
- 时段：亚洲、伦敦、纽约、交叉时段、隔夜；
- 波动：ATR 分层、波动扩张/收缩；
- 趋势环境：趋势、震荡、反转、过渡；
- 入场质量：追高追低、回调入场、结构确认；
- 出场质量：直接 SL、盈利回吐、TP 不现实、timeout；
- 成本：点差、滑点、佣金、swap；
- 集中度：是否依赖少数年份、少数品种、少数大单。

### 退出标准

Phase 1 只能得出：

```text
keep_exploring
reject
promote_to_candidate
```

进入 Phase 2 的最低条件：

- 样本数量基本够；
- 盈亏比测试存在平台或可解释结构；
- 盈利来源有归因解释；
- 成本后仍有边；
- 不是明显依赖少数大单；
- 无明显致命审计问题。

### Phase 1 清理要求

Phase 1 结束一轮快测后，应删除明显临时文件和失败半截输出，只保留能支持下一轮归因的最小代码、配置、结果摘要和关键样本。清理不需要复杂审批，但不得删除用户原始资料、原始市场数据或仍需复核的证据文件。

---

## Phase 2: 成型后版本迭代阶段

### 目标

把探索中发现的盈利点变成可管理的候选策略版本。此阶段开始要求 registry、version、audit、attribution 和 Git 回溯。

### 进入条件

- Phase 1 结果为 `promote_to_candidate`；
- 有明确策略目录；
- 有最小 registry 记录；
- 有 `version.json`；
- 有独立 `versions/<version>/` 目录和 `version_manifest.yaml`；
- 有固定的候选规则和配置。

### 最小 registry

```yaml
strategy_id:
strategy_name:
root_path:
current_stage: candidate_iteration
current_status: active
current_version: v0.1-dev
hypothesis:
symbol:
timeframe:
latest_result:
next_action:
```

### 版本迭代循环

```text
固定候选逻辑
建立独立 version_root
复制父版本 active .py 到新版本子目录
重启 thread/上下文并写 handoff
完整执行审计
Strict Audit Enforcement Mode 修复所有 blocking safety defect
多周期时间可用性审计（如适用）
常规回测
盈亏比平台检查
数量归因
亏损归因
提出单一改动
新建版本或实验分支
重新审计
重新测试
对比父版本
保留、回滚、继续或放弃
清理临时/无效输出并记录 CLEANUP_LOG
```

每次主要改动只改一个逻辑族：

- entry_filter；
- entry_timing；
- initial_sl；
- initial_tp；
- dynamic_exit；
- sizing；
- execution；
- cost_model。

### 必须产物

- `version.json`；
- `versions/<version>/version_manifest.yaml`；
- 新版本专用 active `.py` 主文件；
- `NEW_VERSION_HANDOFF.md` 或等价上下文入口；
- `config.yaml` 或等价配置；
- `CLEANUP_LOG.md` 或报告内 cleanup section；
- `execution_audit.md`；
- `mtf_timing_audit.md`（如果使用多周期）；
- `version_isolation_check.json`；
- `quick_test_report.md` 或正式报告；
- `attribution_report.md`；
- `logic_change_proposal.md`；
- Git commit；
- 关键结果绑定 commit、config hash、数据范围和生成时间。

### 逐根回测关口

Phase 2 末端、冻结候选前，必须执行 bar-by-bar replay。普通批量回测好看不代表策略可以运行。

如果策略使用多周期或重采样特征，逐根回测前必须先通过 `MTF_LOOKAHEAD_AND_VERSION_ISOLATION_STANDARD.md` 的时间可用性审计。逐根引擎必须按当时已经完成的数据增量计算高周期特征，不能预先读入未来已经完成的高周期特征表。

逐根回测必须模拟：

- bar close 后确认信号；
- 下一根或下一可成交报价执行；
- 持仓状态逐根更新；
- SL/TP、gap、collision 的真实顺序；
- breakeven/trailing/timeout 只使用当时已知信息；
- MTF 特征只使用 `feature_available_at <= decision_time` 的高周期 bar；
- one signal bar only one execution；
- 重启后状态恢复；
- 成本和成交模型与候选配置一致。

必须输出三类对账：

- signal diff：常规回测信号 vs 逐根信号；
- mtf feature diff：普通批量高周期特征 vs 逐根当时可见高周期特征；
- trade diff：常规回测交易 vs 逐根交易；
- equity diff：常规回测权益 vs 逐根权益。

通过标准：

- 信号数量一致或差异可解释；
- 交易数量一致或差异可解释；
- entry/exit 时间差异可解释；
- PnL 差异在成本、滑点或 gap 模型范围内；
- 无未来函数、无未完成高周期 bar 泄漏、无 pivot/swing/structure 未确认即使用、无同 bar 理想成交、无重复开仓、无状态漂移；
- batch vs incremental replay 无无法解释的 `REPAINTING_OR_LOOKAHEAD_FAIL`；
- 输出 `bar_by_bar_replay_report.md`。

### 版本文件夹隔离关口

Phase 2+ 执行"一个版本，一个文件夹"：

```text
strategy_root/
  versions/
    v0_1/
      version_manifest.yaml
      NEW_VERSION_HANDOFF.md
      CLEANUP_LOG.md
      src/
        strategy_v0_1.py
      config/
      data/
      backtests/
      audits/
      reports/
      cache/
      logs/
      _trash_review/
```

所有正式 backtest/replay 输出必须写入当前 `versions/<version>/`。除带 hash 的只读市场数据快照外，当前版本不得读取其他版本的 `backtests/`、`reports/`、`cache/`、`trades.csv`、`signals.csv` 或 loose `saved_runs`。发现跨版本读取时，本轮结果降级为 `version_isolation_unverified / not decision-grade`，需要清理路径并重新运行。

新版本必须从父版本复制 active `.py` 主文件到新子目录，形成新版本独立代码入口。允许引用只读稳定库，但禁止修改父版本 active `.py` 或从父版本输出目录读取数据。新版本开发应使用新 Codex thread/对话；如果无法新建 thread，必须以 `NEW_VERSION_HANDOFF.md` 作为上下文重启点，并标记 `context_contamination_risk`。

### Phase 2 结论

```text
continue_iteration
return_to_exploration
reject
freeze_candidate
```

---

## Phase 3: EXE 模拟/实盘运行阶段

### 目标

把冻结候选打包成可复制、可审计、可运行的 Windows EXE，并验证 dry-run/demo/live runtime 的运行安全性。具体打包规则必须遵循 `MT5_RUNTIME_PACKAGING_STANDARD.md`；用户授权实盘必须遵循 `LIVE_TRADING_AUTHORIZATION_STANDARD.md`。

### 进入条件

- Phase 2 结论为 `freeze_candidate`；
- 策略逻辑冻结；
- 参数冻结；
- 成本和成交模型冻结；
- 逐根回测通过；
- Strict Audit Enforcement Mode 无 blocking FAIL；
- MTF 时间可用性审计通过（如适用）；
- 版本文件夹隔离检查通过；
- Git commit 和 config hash 明确；
- 不再边运行边改策略逻辑。

### 运行档位

```text
dry_run: 只扫描信号，不下单
demo_trade: 只允许模拟账户下单
live_trade: 允许，前提是 dry-run/demo 或运行烟测通过，用户明确授权，且 config.ini 显式设置 live_trade 安全字段
```

### 运行安全底线

- REAL 账户默认拒绝，但 `mode=live_trade` + `allow_live_trade=true` + `live_trade_ack=I_ACCEPT_REAL_MONEY_RISK` + 用户明确授权时允许；
- `allow_live_trade=false` 是默认安全值，不是永久禁令；
- demo/live 下单都必须显式授权；
- `kill_switch` 可阻断；
- `risk_cash_per_order`、最大手数、最大持仓、单轮最大开仓数必须从 `config.ini` 读取；
- `magic_number` 和 `comment_prefix` 每个策略/版本/环境唯一；
- 信号执行 ledger 防止同一根信号重复开仓，即使该单在同一根 K 线内被平仓或程序重启；
- order intent journal 在下单前原子写入；
- 启动时先 reconciliation，再扫描新信号；
- EXE 不依赖开发机绝对路径；
- `config.ini` 外置；
- `refresh_seconds`、挂单有效期、对账窗口、确认轮询、日志目录、数据缓存目录必须外置配置；
- 运行时必须用 MT5 API 获取本机终端数据，默认维护最近 3000 根已完成 K 线缓存；
- logs 和 data_cache 必须在 EXE 目录下相对路径；
- 直接打开 EXE 必须有动态控制台输出，不能只依赖 BAT 或隐藏日志。

### 必须产物

- 可直接双击运行的 EXE；
- EXE 同目录 `config.ini`；
- 空 `logs\` 目录；
- 空 `data_cache\` 目录；
- runtime/package audit 报告；
- source preflight 证据；
- EXE SHA256 和 config SHA256；
- portable copy smoke 证据；
- demo/dry-run smoke 证据（如已授权运行）。

BAT 文件只允许作为兼容包装，不是 Phase 3 的必需产物，也不能替代直接 EXE 验收。

### 打包验收顺序

1. 源码版本先用最终 `config.ini` 跑通一轮，确认能连接 MT5、输出身份、创建日志/缓存、完成对账和扫描；
2. audit/preflight 无 FAIL；
3. 才允许 PyInstaller 打包；
4. 打包后必须直接运行 EXE；
5. 把 portable 文件夹复制到另一个临时路径，再直接运行 EXE；
6. 确认输出只写入复制后的 EXE 目录；
7. 交付前清空 portable 目录中的历史日志和数据缓存，除非用户明确要求保留诊断证据。

### Phase 3 结论

```text
runtime_blocked
dry_run_ready
demo_ready
user_authorized_live_ready
live_trial_active
portable_package_ready
```

Dry-run/demo runtime 日志不能当作 OOS-Final；用户授权后的 REAL 账户交易记录属于 `live_trial_active` 操作证据，也不能回填成历史 OOS，但可作为真实资金运行记录单独评估。

---

## 阶段门禁总表

| 动作 | Phase 1 | Phase 2 | Phase 3 |
|------|---------|---------|---------|
| 快速写代码 | 允许 | 允许但需版本化 | 仅 runtime 适配 |
| 完整 registry | 不强制 | 强制 | 强制 |
| data ledger | 不强制，但不得声称 OOS | 强制用于正式验证 | 记录 forward/demo 边界 |
| 执行审计 | 致命审计 | 完整审计 | runtime 执行一致性审计 |
| MTF 时间审计 | 致命审计 | 多周期策略强制 | 与冻结版本对齐 |
| 版本文件夹隔离 | 建议 | 强制 | 继承冻结版本根目录 |
| 新版本复制 active `.py` | 不强制 | 强制 | 只允许 runtime 适配，不改策略 |
| 新 thread / 上下文重启 | 建议 | 新版本强制 | runtime handoff 强制 |
| 临时文件清理 | 强制轻量 | 强制并记录 | 交付前强制清空历史日志/缓存 |
| 盈亏比测试 | 强制 | 强制复核 | 不适用 |
| 多维归因 | 强制 | 强制 | 不适用 |
| 逐根回测 | 可选 | 冻结前强制，MTF 需 feature diff | runtime 对齐依据 |
| EXE 打包 | 禁止 | 准备交接 | 强制安全门 |
| REAL 下单 | 禁止 | 禁止 | 允许：用户明确授权 + live_trade 配置 + 运行安全检查通过 |
