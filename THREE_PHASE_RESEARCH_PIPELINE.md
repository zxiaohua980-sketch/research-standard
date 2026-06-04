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
- 探索结果不会被误标为 OOS、forward-live 或可实盘证据。

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

Phase 1 不要求完整正式审计报告，但每次快测前必须检查：

- 是否有未来函数或数据泄漏；
- bar-close 信号是否在下一根或下一可成交报价执行；
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

---

## Phase 2: 成型后版本迭代阶段

### 目标

把探索中发现的盈利点变成可管理的候选策略版本。此阶段开始要求 registry、version、audit、attribution 和 Git 回溯。

### 进入条件

- Phase 1 结果为 `promote_to_candidate`；
- 有明确策略目录；
- 有最小 registry 记录；
- 有 `version.json`；
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
完整执行审计
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
- `config.yaml` 或等价配置；
- `execution_audit.md`；
- `quick_test_report.md` 或正式报告；
- `attribution_report.md`；
- `logic_change_proposal.md`；
- Git commit；
- 关键结果绑定 commit、config hash、数据范围和生成时间。

### 逐根回测关口

Phase 2 末端、冻结候选前，必须执行 bar-by-bar replay。普通批量回测好看不代表策略可以运行。

逐根回测必须模拟：

- bar close 后确认信号；
- 下一根或下一可成交报价执行；
- 持仓状态逐根更新；
- SL/TP、gap、collision 的真实顺序；
- breakeven/trailing/timeout 只使用当时已知信息；
- one signal bar only one execution；
- 重启后状态恢复；
- 成本和成交模型与候选配置一致。

必须输出三类对账：

- signal diff：常规回测信号 vs 逐根信号；
- trade diff：常规回测交易 vs 逐根交易；
- equity diff：常规回测权益 vs 逐根权益。

通过标准：

- 信号数量一致或差异可解释；
- 交易数量一致或差异可解释；
- entry/exit 时间差异可解释；
- PnL 差异在成本、滑点或 gap 模型范围内；
- 无未来函数、无同 bar 理想成交、无重复开仓、无状态漂移；
- 输出 `bar_by_bar_replay_report.md`。

### Phase 2 结论

```text
continue_iteration
return_to_exploration
reject
freeze_candidate
```

---

## Phase 3: EXE 模拟下单阶段

### 目标

把冻结候选打包成可复制、可审计、可运行的 Windows EXE，并验证 dry-run/demo runtime 的安全性。

### 进入条件

- Phase 2 结论为 `freeze_candidate`；
- 策略逻辑冻结；
- 参数冻结；
- 成本和成交模型冻结；
- 逐根回测通过；
- Git commit 和 config hash 明确；
- 不再边运行边改策略逻辑。

### 运行档位

```text
dry_run: 只扫描信号，不下单
demo_trade: 只允许模拟账户下单
live_trade: 禁止，除非未来另行建立真实账户部署制度
```

### 运行安全底线

- REAL 账户硬拒绝；
- `allow_live_trade=false`；
- demo 下单必须显式授权；
- `kill_switch` 可阻断；
- `max_positions` 和 `max_orders_per_cycle` 生效；
- `magic_number` 和 `comment_prefix` 每个策略/版本/环境唯一；
- 信号执行 ledger 防止同一根信号重复开仓；
- order intent journal 在下单前写入；
- 启动时先 reconciliation，再扫描新信号；
- EXE 不依赖开发机绝对路径；
- `config.ini` 外置；
- logs/tmp/cache 在 EXE 目录下相对路径。

### 必须产物

- EXE；
- `config.ini`；
- `run_status.bat`；
- `run_dry_run.bat`；
- `run_demo.bat`；
- `README_RUNTIME.md`；
- `hash_manifest.txt`；
- `runtime_audit_report.md`；
- demo/dry-run smoke logs；
- clean portable folder。

### Phase 3 结论

```text
runtime_blocked
dry_run_ready
demo_ready
portable_package_ready
```

Demo runtime 日志不能当作 OOS-Final；只有冻结时间之后新产生的信号和交易，才可在明确边界下作为 forward-like 观察材料。

---

## 阶段门禁总表

| 动作 | Phase 1 | Phase 2 | Phase 3 |
|------|---------|---------|---------|
| 快速写代码 | 允许 | 允许但需版本化 | 仅 runtime 适配 |
| 完整 registry | 不强制 | 强制 | 强制 |
| data ledger | 不强制，但不得声称 OOS | 强制用于正式验证 | 记录 forward/demo 边界 |
| 执行审计 | 致命审计 | 完整审计 | runtime 执行一致性审计 |
| 盈亏比测试 | 强制 | 强制复核 | 不适用 |
| 多维归因 | 强制 | 强制 | 不适用 |
| 逐根回测 | 可选 | 冻结前强制 | runtime 对齐依据 |
| EXE 打包 | 禁止 | 准备交接 | 强制安全门 |
| REAL 下单 | 禁止 | 禁止 | 禁止 |
