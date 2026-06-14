# Codex / Claude Code 策略研究最高优先级指令

## 核心原则

本文档是 Codex、Claude Code 以及所有跨目录研究流程的最高优先级约束。任何策略任务必须遵循以下十三大禁区，违反任何一条意味着该研究结果无效。涉及数据切分与 OOS 声明时必须遵循 `DATA_SPLIT_AND_OOS_POLICY.md`；涉及成交、止损、止盈、移动止损、头寸规模或实盘保护时，还必须遵循 `EXIT_RISK_AND_LOGIC_REFINEMENT_STANDARD.md`；涉及费用、点差、滑点、手续费或成本模型时，还必须遵循 `BROKER_COST_MODEL_STANDARD.md`；涉及多周期特征、逐根回测、版本目录、输出文件或跨版本对比时，还必须遵循 `MTF_LOOKAHEAD_AND_VERSION_ISOLATION_STANDARD.md`；涉及审计、修复未来函数、加固、批准、重放一致性或安全补丁时，还必须进入 `STRICT_AUDIT_ENFORCEMENT_STANDARD.md` 定义的 Strict Audit Enforcement Mode；涉及 MT5 runtime、EXE 打包、dry-run/demo 模拟下单、订单监控、持仓管理或换电脑运行时，还必须遵循 `MT5_RUNTIME_PACKAGING_STANDARD.md`。

## 三阶段研发主流程

策略研究优先采用 `THREE_PHASE_RESEARCH_PIPELINE.md` 中的三阶段流水线：

1. **Phase 1 快速开发测试**：用于提出假设、量化规则、快速写代码、致命审计、快速测试、盈亏比测试和多维归因。该阶段可以没有完整 registry，但必须标记为 `exploratory / not decision-grade / not OOS / not forward-live`。
2. **Phase 2 成型后版本迭代**：用于把有潜力的探索结果注册成候选策略，执行完整审计、版本化迭代、归因优化、参数/盈亏比平台检查，并在冻结前通过逐根回测。
3. **Phase 3 EXE 模拟下单**：用于冻结候选后的 dry-run/demo runtime 打包、模拟下单、安全门、日志、订单意图和持仓恢复验证。打包必须符合 `MT5_RUNTIME_PACKAGING_STANDARD.md`，包括源码预检、直接 EXE 启动、外置配置、日志/对账、3000K 缓存、便携目录和 audit hook。REAL 账户下单不属于本制度允许范围。

原 Stage 0-13 流程仍然有效，但它主要约束 Phase 2 和 Phase 3 的正式验证、冻结、前向和部署准备。Phase 1 的结果只能用于研发判断，不能作为正式策略结论。

## 研究效率与分级门禁原则

制度的目标是服务策略研究，不是替代研究本身。优先级始终是：

```text
提出假设 -> 写代码 -> 快速测试 -> 数量/亏损归因 -> 修改优化 -> 再审计
```

门禁按阶段分级，不能用 Phase 3 的严谨度拖垮 Phase 1：

1. **Phase 1 快速探索：轻门禁。** 可以先写单文件代码、快测、盈亏比测试和归因；不强制完整 registry、完整 data ledger、完整报告。只要求独立探索文件/目录、致命审计、清楚标记 `exploratory_not_decision_grade`，且不碰 frozen/forward 版本。
2. **Phase 2 候选迭代：中高门禁。** 进入正式候选后，必须有新版本子目录、单独复制出来的 `.py` 主文件、version manifest、重新审计、版本隔离和归因记录。中央 registry 只做最小索引和里程碑更新，不记录每一次小试错。
3. **Phase 3 打包前：最高门禁。** 冻结、逐根回测、Strict Audit Enforcement、runtime safety、EXE 打包和 demo/dry-run 交付必须严格执行。

如果某个治理要求会明显阻断 Phase 1 的快速研究，应优先降级证据标签，而不是停止写代码；只有当结果要进入 Phase 2 决策级候选、冻结、OOS、forward-live 或 runtime handoff 时，才强制完整门禁。

## 文件卫生与删除边界

研究可以快，但文件不能乱。每轮开发、快测、归因、审计或版本迭代结束时，都要做一次轻量文件清理，防止无效文件、临时文件、旧输出和 loose cache 污染后续结果。

### 必须及时清理

- `__pycache__`、`.pyc`、`.tmp`、`.bak`、编辑器临时文件；
- 中断运行产生的半截 CSV/JSON/HTML/MD 报告；
- 无效快测输出、debug dump、临时 notebook/export、一次性 scratch 文件；
- loose `latest`、`final`、`new`、`copy`、`副本`、`saved_runs` 中未绑定 version/root/hash 的文件；
- 当前版本内已经被汇总到报告中的重复临时图表、临时日志、临时缓存；
- 空目录、误放在版本根外的临时输出。

### 不能随便删除

- 原始市场数据快照、带 hash 的共享数据、data ledger；
- `version_manifest.yaml`、`version.json`、audit/replay/attribution 报告；
- 冻结版本、forward-live 信号/交易/干预日志；
- runtime 订单意图、对账、持仓、错误日志；
- registry 记录、handoff、用户提供的源文件；
- 任何已在报告、commit、registry 或 forward/runtime 中被引用的证据文件。

### 清理方式

- 明显临时文件可以直接删除。
- 证据价值不确定的文件，先移动到当前 version_root 下的 `_trash_review/YYYYMMDD_HHMMSS/`，并在确认无引用后再删除。
- Phase 2+ 清理必须在版本目录写 `CLEANUP_LOG.md` 或追加 cleanup section，记录删除/隔离了什么、为什么无效、是否影响证据链。
- 清理本身不得改变策略逻辑、回测输入、审计证据或 forward-live 历史。

## 十三大禁区

### 1. 禁止在没有执行审计的情况下相信回测结果

任何回测数据都必须经过 Stage 2 Execution Audit 才能用于正式决策、候选晋级、冻结或 forward-live 声明。Phase 1 可以运行探索性快测，但必须先做致命审计并标记为 `exploratory_not_decision_grade`。审计内容包括但不限于：检查前视偏差（data leakage）、验证入场当根 SL/TP 逻辑、确认非法止损方向、检查冲突持仓、验证费用模型准确性、检查样本末端未平仓状况、区分历史回填与前向数据。未通过审计的数字不得作为正式结论。

### 2. 禁止在没有 Trade Attribution 的情况下新增 filter

任何进入 Phase 2 的正式候选改动，包括新的入场 filter、出场条件、止损或止盈调整、breakeven/trailing/time exit、分批出场、头寸规模规则，都必须基于 Trade Attribution 的定量发现。Phase 1 可以快速试验改动，但每次改动必须标记为探索性，并通过数量归因和亏损归因解释。归因过程包括对比盈利单和亏损单的统计特征、识别失败特征和成功特征、严格区分决策当时可见特征与事后 hindsight 特征。不允许把直觉改动或少量样本探索包装成正式策略改进。

### 3. 禁止用全样本选择参数

规则发现、filter 选择和参数优化必须遵循 `discovery_train` / `development_validation` / `locked_final_holdout` / `forward_live` 四层分离。训练集用于发现和搜索，开发验证集用于筛选候选，锁定最终 holdout 只允许在入场、出场、风险、成本和参数全部固定后评价一次，forward-live 只收集冻结时刻之后的新交易。已用于接受 filter 或调整逻辑的数据不得再声称是最终 holdout。禁止用全样本选择规则或参数，禁止反复在 OOS/holdout 上补丁。

### 4. 禁止把历史回填当成 forward validation

Forward validation 的严格定义：仅有 framework_start_time 之后新产生的信号和交易才算 forward-live。历史回填（historical backfill）、固定规则回测（fixed-rule backtest）、回溯时间序列验证（walk-forward）都属于历史分析，不可混淆。forward-live 必须通过 Gate A（3个月+30笔）或 Gate B（50笔）才能正式评价。

### 5. 禁止在 forward-live 阶段修改 frozen strategy

一旦策略进入 forward-live（Stage 12），代码、参数、规则、成本模型全部冻结，不得修改。任何改动都必须新建版本号、新建 forward phase、不得混合旧数据。这是保证 forward 结果纯度的唯一方式。

### 6. 禁止用少量连亏作为改策略理由

forward-live 初期（未达 Gate）的少量亏损单是正常的统计波动。不允许因为连亏2-3笔就立即调整策略。必须等到样本足够（Gate A 最少 30 笔）才能做正式评价。

### 7. 禁止为了提高 PF 盲目扫参

参数优化的目标是检验逻辑假说的稳健性和跨环境一致性，不是找最高的夏普或最高的 PF。禁止无限扩大搜索空间、禁止只报告最优结果而隐瞒其他候选、禁止在参数平台边缘硬优化。必须输出全部候选参数的评分，检查 local robustness 和参数高原。

### 8. 每一个新策略必须先登记到 registry

任何新策略项目进入 Phase 2 正式候选迭代前，必须在 D:\MT5\research_registry\strategy_registry.yaml（或 fallback registry）中有最小登记，包括 strategy_id、root_path、current_stage、current_status。Phase 1 探索可以先使用 `idea_card.md` 或单独探索目录，不得因缺少完整 registry 阻断写代码、快测和归因，但不得声称正式研究、OOS 或 forward-live。registry 是跨目录协调的权威索引，但不应变成每次小试错都要更新的流水账；Phase 2+ 的细节优先写在版本目录内的 manifest、报告和 handoff 中，中央 registry 只在进入候选、切换 current_version、冻结、forward/runtime、关闭/放弃等里程碑更新。

### 9. 每一个策略必须有独立目录

每个策略必须有独立的 root_path，不允许多个策略共享可变输出、配置或 forward-live 日志。多个策略可以引用同一个只读、带来源和 hash 的市场数据快照，但必须在各自报告中记录引用方式和数据版本。

### 10. 每一次策略规则变化必须开启新版本或新分支

任何对信号定义、入场规则、成交价约定、出场规则、止损/止盈/动态管理、头寸规模或成本模型的 Phase 2+ 改动都必须启动新版本（v0.1 → v0.2）或新分支（main → experiment_branch）。新版本启动时必须执行以下三件事：

1. **复制父版本，不改父版本。** 在新的 `versions/<new_version>/` 子目录中复制父版本的 active `.py` 主文件，形成一个新版本专用的单独 `.py` 文件（例如 `strategy_v0_2.py`）。该文件可以引用只读稳定工具库，但不得把父版本目录中的可变 backtest、cache、report、signals、trades 或 mutable strategy file 当作输入。
2. **重新审计。** 复制后的 baseline 先做致命/执行/MTF/版本隔离审计，再开始本版本的逻辑修改、归因和优化。不能假设父版本审计自动覆盖子版本。
3. **重启上下文。** 新版本实施应建立新的 Codex thread/对话或等价的上下文重启，并以 `NEW_VERSION_HANDOFF.md`、`PROJECT_STATE.md` 或版本目录 handoff 作为唯一上下文入口。旧版本长对话里的结论只能作为参考，不得作为当前版本事实来源。无法新建 thread 时，必须在输出中标记 `context_contamination_risk`。

每个新版本必须记录 parent_version、new_version、active_py_file、intended_change、created_at、git base、数据范围和重新审计状态。不允许在原版本上无声地改动。

### 11. 禁止未通过多周期时间可用性审计的 MTF 回测进入正式结论

任何使用多周期数据的策略，必须证明每个高周期特征在低周期决策时已经完成且可见。默认安全规则是只使用上一根已经完成的高周期 bar；如果要使用与低周期决策同一时间戳收盘的高周期 bar，必须证明数据源是 close-time labeling 且订单最早在下一可成交报价执行。禁止把 open-time 标记的 H1/H4/D1 行提前合并到未完成的 M15/M30 行。未输出 `mtf_timing_audit.md`、未记录 `feature_available_at <= decision_time`、或逐根回测与普通回测存在无法解释差异时，该结果不得进入 Phase 2 冻结、OOS、forward-live 或 runtime handoff。

### 12. 禁止跨版本读取回测数据、报告、缓存或记录

Phase 2+ 必须执行"一个版本，一个文件夹"。每个版本必须有独立 `versions/<version>/` 目录和 `version_manifest.yaml`；本版本的 backtest、report、audit、cache、log 只能写入并读取本版本目录。除带 hash 的只读原始市场数据快照外，不允许当前版本读取其他版本的 `backtests/`、`reports/`、`cache/`、`trades.csv`、`signals.csv` 或 loose `saved_runs`。版本对比只能读取父版本冻结摘要作为报告参考，不得作为当前版本回测输入。发现跨版本路径引用时，本轮结果立即降级为 `version_isolation_unverified / not decision-grade`。

### 13. 禁止在审计任务中顺手优化或改变策略逻辑

当用户要求审计、查未来函数、修复回测差异、加固、批准、重放一致性检查、MTF/pivot/swing/execution 检查或 runtime safety 检查时，必须进入 `STRICT_AUDIT_ENFORCEMENT_STANDARD.md`。该模式下只允许最小安全补丁：修复 lookahead/leakage、时间对齐、缺失时间元数据、断言、重放一致性和版本/数据污染问题。禁止同时改变入场/出场逻辑、指标公式、参数、RR、PF、胜率、交易数量或优化目标。若安全修复导致信号或指标变化，旧结果必须标为由缺陷引擎生成并作废；新结果只能视为修复后的事实，不得包装成策略优化收益。

## 成交与风险规则的额外门禁

1. 对基于 bar close 的策略，默认只允许在 `bar t` 收盘确认信号后，于 `bar t+1` 首个可成交报价执行；不能一边使用 `bar t` 的 close 生成信号，一边假定以同一 close 无摩擦成交。
2. 对同一 OHLC bar 同时触及 SL 与 TP 的交易，必须预先声明使用更细粒度有序数据，或采用保守的 SL-first 处理；不得按更盈利的结果选择。
3. SL、TP、trailing、breakeven、timeout 和 position sizing 均属于策略规则，必须在 Stage 2 审计，在 Stage 5 归因后才可提出变更，在 Stage 11 冻结，并在 Stage 12 保持不变。
4. live 阶段的 kill switch 或紧急平仓可以为安全而执行，但必须单独记录为人工/运行干预，不得冒充冻结策略本身的结果。

## Codex 每次接收策略任务的必做检查表

在执行任何策略相关代码修改、参数调整、数据分析时，必须先回答以下十一个问题：

1. **当前任务属于哪个研发阶段？** 先判断 Phase 1 快速开发测试、Phase 2 成型后版本迭代、还是 Phase 3 EXE 模拟下单；如果属于正式验证，再对标 RESEARCH_WORKFLOW.md 中的 Stage 0-13。

2. **是否允许修改代码？** 如果策略已进入 forward-live（Stage 12+），信号引擎代码不允许修改。如果仍在开发阶段（Stage 1-8），逻辑修改必须基于 Trade Attribution 的发现。否则回答"否"。

3. **是否允许优化参数？** 只有完成 Stage 2 Execution Audit、Stage 5 Trade Attribution、Stage 6 Logic Refinement 的策略才允许进入 Stage 7 Parameter Optimization。如果尚未通过这些阶段，回答"否，需先完成审计和归因"。

4. **是否需要先做审计？** 任何新的数据源、新的回测逻辑、新的信号定义都需要先执行 Stage 2 Execution Audit。审计未通过，所有后续步骤无效。

5. **是否会污染已有 forward-live 结果？** 检查当前修改是否会改变 framework_start_time 之前的历史数据处理逻辑或参数。如果会，这会破坏已有的 forward-live 纯度。

6. **成交与风险模型是否已声明并允许变更？** 如果任务涉及入场成交、SL/TP、移动止损、头寸规模或实盘保护，必须定位对应的 audit/attribution/版本记录；没有记录则不得把变更作为正式策略改进。

7. **当前数据属于 IS 还是哪一种 OOS？** 必须核对 `data_usage_ledger.yaml`，区分 `discovery_train`、已消费的 `development_validation`、一次性的 `locked_final_holdout`、历史 `WF-OOS` 和真正 `forward_live`。没有台账的既有结果只能标为 `legacy / split integrity unverified`。

8. **是否涉及多周期或重采样特征？** 如果涉及 MTF、resample、merge_asof、高周期 filter、日内使用日线/小时线、ZigZag/pivot/fractal/swing/divergence 确认，必须先按 `MTF_LOOKAHEAD_AND_VERSION_ISOLATION_STANDARD.md` 做时间可用性审计；没有 `feature_available_at <= decision_time` 证据时不得信任结果。

9. **当前版本是否有独立 version_root？** Phase 2+ 必须确认 `versions/<version>/version_manifest.yaml`、输出根目录和路径守卫；不得把其他版本的回测数据、报告、缓存或 loose saved_runs 当作本版本输入。

10. **是否正在开启新版本？** 如果是 Phase 2+ 新版本，必须确认已在新子目录复制父版本 active `.py` 为新版本单独文件、已准备重新审计、并已建立新 thread/上下文重启或标记 `context_contamination_risk`。

11. **当前是否是 Strict Audit Enforcement Mode？** 如果任务是审计、修复未来函数、解释普通回测与逐根回测差异、批准候选、重放一致性或 safety hardening，则禁止优化和策略逻辑改动；输出必须包含 `AUDIT_STATUS`、问题列表、文件/函数位置、最小补丁说明和 batch-vs-incremental replay 结果或 `NOT_RUN/NOT_APPLICABLE`。

## 推荐工作流程

对于接收到的每个任务，Codex 应该按以下流程思考：

1. 先判断任务属于 Phase 1、Phase 2 还是 Phase 3。
2. Phase 1：允许使用 `idea_card.md` 开始探索；缺 registry 不阻断，但输出必须标记为探索性、非决策级。
3. Phase 2：必须查询 strategy_registry.yaml，定位策略的 root_path、current_stage 和 current_version；缺 registry 时先创建最小注册记录。
4. Phase 3：必须确认冻结候选、逐根回测报告、runtime handoff 和安全配置齐全。
5. 根据 current_stage/current_phase 判断是否允许修改代码或参数。如果 current_stage = "forward-live-active"，禁止修改冻结部分。
6. 如果任务是 Phase 1 探索，优先把假设写成可运行代码、快测和归因；门禁只做致命审计与证据降级，不要求完整登记。
7. 如果任务涉及新的 Phase 2+ 版本，先复制父版本 active `.py` 到新版本子目录，建立 handoff/新 thread，然后重新审计复制后的 baseline。
8. 如果任务涉及新的数据或正式逻辑，要求 Execution Audit 报告（Stage 2）；Phase 1 只允许致命审计快测。
9. 如果任务本身是审计、加固、修复未来函数、解释重放差异或批准候选，立即进入 `STRICT_AUDIT_ENFORCEMENT_STANDARD.md`：只做最小安全补丁，不做性能优化，不改变策略意图；任何修复后的指标必须重新生成并重新标注证据等级。
10. 如果任务涉及正式新增 filter、SL/TP、动态退出或头寸规模修改，先按 Trade Attribution 和 `EXIT_RISK_AND_LOGIC_REFINEMENT_STANDARD.md` 完成归因、逻辑变更提案和重新审计。
11. 如果任务涉及多周期、重采样或高周期特征，Phase 2+ 必须输出 MTF 时间可用性审计；没有通过时不得进入正式回测结论。
12. Phase 2+ 的每个候选必须有独立 version_root 和 `version_manifest.yaml`，并通过版本隔离检查；不得跨版本读取回测输出。
13. Phase 2 冻结前必须执行逐根回测，并输出 signal/trade/equity diff；MTF 策略还必须输出 mtf_feature_diff。
14. 如果任务涉及 forward-live 评估，检查是否已达 Gate（3个月+30笔或50笔）。
15. 任何 Phase 2+ 规则修改都必须记录到新版本目录、version.json 和 version_manifest.yaml；strategy_registry.yaml 只在 current_version/阶段/状态发生里程碑变化时更新。
16. 每轮结束前清理临时/无效/半截输出，确认正式输入输出只来自当前 version_root 或 hash 声明的只读数据；不确定是否可删的文件先进 `_trash_review/` 并记录。

## Git 与版本管理

### 任何正式研究结果必须绑定 Git 记录

量化研究不是"当前目录里的代码"，而是某个 commit + 某个 config + 某个数据快照 + 某个输出结果的完整四元组。任何声称的 backtest 结果、environment report、forward-live metric 都必须明确记录：

- git commit hash：标识信号引擎的确切代码版本
- config hash：标识参数和规则的确切版本
- data snapshot：标识数据范围（起止日期和来源）
- generated timestamp：结果生成的确切时刻

没有这四项信息的结果无法复现，因此不可信。

### Codex 的 Git 操作规范

Codex 在执行正式研究任务前，必须先输出当前 Git 状态：

```
git branch -v
git status
git log --oneline -5
```

这三条命令的输出必须在任务日志中可见，确保：
- 当前处于正确的 branch（不是 main 或 frozen-*）
- working tree 是干净的（没有未 commit 的改动）
- 当前 commit hash 清晰可追溯

禁止在 dirty working tree 上运行正式验证任务（`run_backtest.py`、environment validation、forward-live analysis），除非明确说明是临时探索性工作。

### Commit 与版本绑定

任何新的 Stage 完成、规则改变、参数调整都必须生成新的 commit，遵循格式。冻结 manifest 应先提交再对该 commit 打 tag；不得要求一个 commit 在其自身内容中预知自身 hash：

```
[STAGE] strategy_id=<id>, action=<action>

一句话描述

- 具体改动1
- 具体改动2
```

例如：
```
[AUDIT] strategy_id=STRAT_RSI_001, action=audit-fix

修复入场信号的前视偏差

- RSI 计算日期从 signal_date 改为 signal_date - 1bar
- 重新运行 fixed-rule backtest
- Sharpe 从 1.2 改为 0.9
```

### Frozen Strategy 必须打 Git Tag

任何通过 Stage 11 冻结的策略版本必须打 git tag，格式 `v0.1-frozen`、`v0.2-frozen` 等。frozen strategy 对应的 commit 不允许修改，任何后续改进必须在新的 feature branch 上开发，完成后生成新的 version 号和新的 tag。

### Forward-Live 数据的 Git 管理

forward-live 分支必须分离自某个 frozen tag，例如从 `v0.1-frozen` 创建 `forward-v0.1` 分支。forward-live 数据追加到 forward_live_trades.csv 和 forward_live_signals.csv，这两个文件必须 commit 到 Git，以提供完整的历史审计链。

任何 forward-live 分支不允许 merge 回 main 或 frozen 分支，保持分离状态。

## 禁止操作

- 不允许未经用户明确批准和归档记录就删除任何已登记的策略目录或文件。
- 不允许在 forward-live 数据中混入历史回填。
- 不允许用一个回测窗口既做参数搜索又做评估。
- 不允许忽视前视偏差而声称策略有效。
- 不允许因为样本太小（< 30）就强行加 filter。
- 不允许删除亏损环境后宣布策略成功。
- 不允许修改已冻结版本的代码或参数。
- 不允许在未完成 MTF 时间可用性审计时相信多周期回测。
- 不允许当前版本读取其他版本的回测数据、报告、缓存或 loose saved_runs。
- 不允许在 Strict Audit Enforcement Mode 下把审计修复和盈利优化、参数搜索或策略逻辑改动混在同一个补丁里。
