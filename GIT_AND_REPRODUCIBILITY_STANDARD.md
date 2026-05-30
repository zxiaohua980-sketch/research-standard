# Git 与可复现性规范

## 核心思想

量化研究不是"当前目录里的代码"，而是**四元组**的完整记录：某个 commit + 某个 config + 某个数据快照 + 某个输出结果。只有这四者同时固定，一个实验才能被认为是"已完成"和"可复现"的。没有 Git 版本控制，就无法知道哪个版本真正赚钱，forward-live 就无法追溯原始假说，环境验证的结果也无法绑定到信号引擎版本。

## 第一部分：为什么 Git 是必须的基础设施

### 没有 Git，三个问题无法解决

**问题1：版本追溯**。假设某个策略在今年前两个月赚了 5000 美元，但无法说出这个盈利对应的代码版本。下个月同一策略亏损，想回到上月的逻辑重新跑，但不知道改了什么。这个情况下，forward-live 数据完全无效，因为无法知道回测的规则和实盘的规则是否一致。

**问题2：环境分析的一致性**。环境验证需要把策略按 ATR regime、trend regime、session 分层分析。如果 signal engine 在不同时间有不同实现，同一笔交易在环境诊断和正式回测中看到的信号可能不同。这会导致环境分析的结论无法复用到实盘。

**问题3：跨电脑、跨会话同步**。多台电脑上同时开发策略时，A 电脑修改了参数，B 电脑还在用旧逻辑，两台电脑的回测数据来自不同版本。最终不知道哪个版本是"官方"版本。这种情况下，portfolio 级别的相关性分析、组合回撤评估都无法进行。

### Git 三大用途

**用途1：代码版本锁定**。每个 backtest result、每个 environment report、每个 forward-live metric 都记录其对应的 commit hash。任何人、任何时刻都能通过 `git checkout <hash>` 还原当时的信号逻辑，重现结果。

**用途2：分支隔离**。开发分支（feature branches）、冻结分支（frozen-v0.1）、forward-live 分支（forward-v0.1）分离，避免互相污染。forward-live 分支一旦创建，除了添加新信号，不允许修改已冻结逻辑。

**用途3：跨电脑同步**。Git 是分布式版本控制系统，所有本地改动通过 commit 明确化，通过 push/pull 同步。每个开发者看到的都是清晰的 commit 历史，而不是"哪台电脑上的代码"。

## 第二部分：Git 初始化规范

### 策略项目的强制性 Git 要求

每个正式策略项目必须：

1. **初始化仓库**：`git init` 或 `git clone` 远程仓库。新策略必须在第一次 commit 之前初始化。
2. **编写 .gitignore**：必须包含以下条目：
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
   原则：源代码和配置入库，运行输出（CSV、PNG）和临时缓存不入库，除非是正式报告。

3. **初始 commit**：包含 README.md、strategy_xxx.py 的第一个版本、config.yaml。commit message 格式：`[PROJECT_INIT] strategy_id=STRAT_001, hypothesis=<one_line_hypothesis>`。

4. **版本标签**：每个通过 Execution Audit 的版本必须打 git tag，格式：`v0.1-audit-pass`、`v0.2-oos-pass`、`v0.3-frozen`。

### .gitignore 细则

- **入库**：signal_engine.py、backtest.py、config.yaml、analysis scripts、version.json、registry entries。
- **不入库**：当日 backtest 输出的 CSV、中间计算缓存、trade logs（除非是冻结版本的正式报告）。
- **特殊处理**：forward-live 数据必须入库，但用 `forward_live_trades.csv.LOCK` 标记"未完成"状态，防止其他会话修改。

## 第三部分：Commit 规范

### Commit Message 格式

每个 commit 必须遵循以下格式，便于后续追溯和自动化脚本解析：

```
[STAGE] strategy_id=<id>, action=<action_type>

<一句话描述修改内容>

- <具体改动1>
- <具体改动2>
```

其中 STAGE 和 action_type 必须从以下列表选择：

| STAGE | action_type | 说明 |
|-------|------------|------|
| INIT | init | 项目初始化 |
| AUDIT | audit-fix | 执行审计，修复 data leakage 或费用模型 |
| EVENT | event-analysis | Stage 3 事件研究 |
| BACKTEST | fixed-rule | Stage 4 固定规则回测 |
| ATTRIB | attribution | Stage 5 交易归因分析 |
| LOGIC | refine-rule | Stage 6 逻辑优化，基于 attribution 结果 |
| OPTIM | optimize-params | Stage 7 参数优化 |
| WALKFW | walk-forward | Stage 8 回溯时间序列验证 |
| REGIMEADD | frozen | Stage 11 冻结版本，生成 git tag |
| FORWARD | forward-live | Stage 12 前向交易，添加新信号 |

### Commit 示例

```
[AUDIT] strategy_id=STRAT_RSI_001, action=audit-fix

修复 RSI 计算中的前视偏差：RSI 在信号日期计算，但应在前一根 bar 完成

- 修改 signal_engine.py 第 42 行，RSI 查看日期从 signal_date 改为 signal_date - 1bar
- 重新运行 fixed-rule backtest，输出新的 trades.csv
- Sharpe 从 1.2 改为 0.9，验证修复有效
```

```
[ATTRIB] strategy_id=STRAT_RSI_001, action=attribution

交易归因：对比 winners 和 losers 的 ATR 和 trend 特征

- 添加 trade_attribution.py，输出 winners 平均 ATR = 0.85，losers 平均 ATR = 1.20
- 发现低 ATR 环境胜率仅 35%，高 ATR 环境胜率 62%
- 候选 filter：只在 ATR > 0.8 时入场
```

## 第四部分：Branch 管理策略

### 分支命名与用途

每个策略项目必须遵循以下分支架构：

| 分支名 | 用途 | 修改策略 |
|-------|------|--------|
| main | 正式发布版本，仅包含通过全部验证的代码 | 只允许 merge，不允许直接 commit |
| develop | 开发分支，包含当前正在研究的版本 | 允许提交 feature branches，review 后 merge |
| feature/strat_<id>_<stage> | 功能分支，用于单个 Stage 的工作 | 完成后提交 PR，merge 到 develop |
| frozen-v<x.y> | 冻结分支，对应某个通过 Stage 11 的版本 | 禁止修改，只允许打 tag |
| forward-v<x.y> | forward-live 分支，记录实盘新信号 | 只允许追加新的 Stage 12 数据，不允许改历史记录 |

### Branch 工作流示例

```
# 新策略初始化
git init
git add .
git commit -m "[INIT] strategy_id=STRAT_NEW_001, ..."
git branch develop
git checkout develop

# 开发 Stage 2 Audit
git checkout -b feature/STRAT_NEW_001_audit
# 修改代码，运行审计
git add signal_engine.py backtest.py
git commit -m "[AUDIT] strategy_id=STRAT_NEW_001, action=audit-fix"
git push origin feature/STRAT_NEW_001_audit
# 提交 PR，review 通过后 merge 到 develop

# 完成 Stage 11 冻结：先提交 manifest，再对该提交创建 frozen tag
git checkout main
git merge develop --no-ff
git add version.json frozen_report.md data_usage_ledger.yaml
git commit -m "[FREEZE] strategy_id=STRAT_NEW_001, version=v0.1"
git tag -a v0.1-frozen -m "frozen stage 11 complete; tagged commit is the frozen commit"
git push origin main --tags

# 进入 forward-live Stage 12，显式从 frozen tag 创建分支
git switch --detach v0.1-frozen
git switch -c forward-v0.1
# 添加 framework_start_time，创建 forward_live_config.yaml
git commit -m "[FORWARD] strategy_id=STRAT_NEW_001, action=forward-live"
git push origin forward-v0.1
```

## 第五部分：Frozen Strategy 的版本绑定

### Frozen 版本必须记录四元组

任何进入 forward-live 的策略，都必须在 version.json（存储在策略目录根目录）中冻结配置、数据与规则 manifest。承载 `version.json` 的 freeze commit 无法在自身内容中预知自身 hash，因此 `frozen_commit_hash` 以 Git tag 指向的 commit 和中央 registry 为权威记录，不要求回填修改已冻结文件：

```json
{
  "strategy_id": "STRAT_RSI_001",
  "version": "0.1",
  "frozen_tag": "v0.1-frozen",
  "frozen_timestamp": "2025-06-01 10:30:00",
  "config_hash": "sha256:abcd1234...",
  "data_snapshot_hash": "sha256:efgh5678...",
  "framework_start_time": "2025-06-01 11:00:00",
  "entry_rules": "RSI < 30 on H1 close, confirmation on H4",
  "exit_rules": "RSI > 70 or SL triggered",
  "cost_model": "bid_ask_spread=0.0002, commission=0.001",
  "conflict_rules": "no concurrent long and short",
  "signal_engine_version": "0.1",
  "backtest_engine_version": "v1.0",
  "data_start": "2020-01-01",
  "data_end": "2025-05-31"
}
```

中央 registry 与 tag annotation 另行记录：

```yaml
frozen_commit: a1b2c3d4e5f6
frozen_tag: v0.1-frozen
```

### Frozen 版本的代码保护

一旦生成 frozen tag，该分支对应的代码必须被标记为只读。任何后续改动都必须：
1. 在新的 feature branch 上工作；
2. 生成新的 version 号（v0.2）；
3. 完成新版本的完整 Stage 2-11 流程；
4. 生成新的 frozen tag；
5. 创建新的 forward-live 分支。

禁止在 frozen-v0.1 branch 上直接修改代码然后 push，这会污染 forward-live 数据的追溯链。

## 第六部分：Forward-Live 数据的 Git 管理

### Forward-Live 分支的独立性

forward-live 分支必须满足：
- 分离自某个 frozen tag（例如从 v0.1-frozen 创建 forward-v0.1）；
- 只允许在 forward_live_trades.csv 和 forward_live_signals.csv 追加新行，不允许修改历史行；
- 定期 commit 新信号：每周或每 10 笔交易后自动 commit；
- 与 main 分支保持分离，不允许 merge 回 main。

### Forward-Live Commit 规范

```
[FORWARD] strategy_id=STRAT_RSI_001, action=forward-live

新增 10 笔信号，当前 Gate 进度：30/30 (Gate A pass)

- 交易日期：2025-06-10 至 2025-06-15
- 新增交易数：3 笔，2 胜 1 负
- 当前月度收益：+1.2%
- 积累交易数：35
```

### Forward-Live 的完整性检查

每次添加新信号到 forward-live 分支，必须运行完整性检查脚本，验证：
- 新信号的时间戳 >= framework_start_time；
- 新交易不覆盖已冻结版本的历史数据；
- 信号逻辑与 frozen commit 的代码一致；
- 费用模型与 frozen config 一致。

完整性检查失败，该 commit 不允许 push。

## 第七部分：可复现性要求

### 可复现的定义

一个研究结果被认为是"可复现"的，当且仅当任何人在任何时刻都能通过以下信息重新生成该结果：

1. **commit hash**：git checkout <hash>
2. **config 文件**：完整的参数和逻辑定义
3. **data snapshot**：数据的起止日期和来源确认
4. **execution protocol**：运行脚本的命令、输入参数、环境变量
5. **generated timestamp**：结果生成的确切时刻
6. **data usage ledger**：明确结果使用的是 IS、OOS-Dev、WF-OOS、OOS-Final 或 Forward-Live，以及该数据是否已消费

### 可复现结果的输出格式

任何正式报告（backtest report、environment report、forward-live summary）都必须在文件头部包含以下元数据：

```
# Reproducibility Metadata
# ========================
# strategy_id: STRAT_RSI_001
# version: 0.1
# commit_hash: a1b2c3d4e5f6g7h8i9j0
# tag: v0.1-frozen
# config_hash: sha256:abcd1234efgh5678
# data_range: 2020-01-01 to 2025-05-31
# generated_timestamp: 2025-06-01 14:30:15 UTC
# environment: Windows 10, Python 3.11, pandas 2.0.1
# execution_command: python run_backtest.py --config config.yaml --output output/
# evidence_type: OOS-Final / locked_final_holdout
# data_usage_ledger: data_usage_ledger.yaml
```

### 临时输出 vs 正式输出

- **临时输出**：当日的 backtest run、quick analysis、exploratory chart。存放在 `output/temp_*` 目录，不需要完整的可复现元数据，可以删除。
- **正式输出**：通过 Stage 2 Audit 的 backtest result、通过 Stage 5 归因的 trade summary、通过 Stage 11 冻结的 final report。存放在 `output/reports/v<x.y>/`，必须包含完整元数据，永久保留。

## 第八部分：Output Artifact 管理

### Artifact 类型与保留期限

| Artifact | 保留期 | 位置 | 何时删除 |
|----------|-------|------|--------|
| signal engine source code | 永久 | git repo | 不删除，通过 tag 管理版本 |
| fixed-rule backtest result | 永久或离线只读归档 | output/reports/v<x.y>/ | 不删除；归档时保留 hash、版本和索引 |
| parameter optimization log | 永久或离线只读归档 | output/optimization/<v>/ | 不删除；归档时保留完整候选与 hash |
| environment validation report | 永久或离线只读归档 | output/regime/<v>/ | 不删除；归档时保留版本关联 |
| walk-forward metrics | 永久或离线只读归档 | output/walkfw/<v>/ | 不删除；归档时保留版本关联 |
| forward-live trades | 永久 | git repo (forward-live branch) | 不删除，追加新交易 |
| forward-live gate report | 永久 | output/forward/<v>/ | 不删除，追加新 gate check |

### Artifact 目录结构

```
strategy_root/
├── signal_engine.py
├── backtest.py
├── config.yaml
├── version.json
├── .gitignore
├── output/
│   ├── reports/
│   │   ├── v0.1/
│   │   │   ├── execution_audit.md
│   │   │   ├── backtest_result.csv
│   │   │   └── trades_detail.csv
│   │   ├── v0.2/
│   │   └── ...
│   ├── regime/
│   │   ├── v0.1_environment_validation.md
│   │   └── ...
│   ├── forward/
│   │   ├── v0.1_gate_progress.csv
│   │   ├── v0.1_live_trades.csv (同步到 git)
│   │   └── ...
│   └── temp_*/ (临时输出，可删除)
└── .git/
```

## 第九部分：Cross-Machine 同步规范

### 多电脑开发的强制要求

当同一策略在多台电脑上开发时，必须遵循：

1. **单一 Git 来源**：所有改动通过 Git commit/push/pull 同步，不允许 USB、Dropbox、邮件传输代码。
2. **每日 push**：每个开发会话结束前，必须把所有 commit push 到远程仓库，确保其他电脑能 pull。
3. **分支隔离**：每个功能在单独的 feature branch 上开发，完成后提交 PR 再 merge，避免直接在 develop/main 上 push。
4. **锁定机制**：如果 signal engine 正在某台电脑上修改，其他电脑必须等待修改完成并 merge 后才能修改同一文件，否则冲突无法自动解决。

### Environment Validation 的 Git 要求

environment validation 的结果必须基于 frozen commit，而不是本地当前代码。具体要求：

- run_environment_analysis.py 脚本必须在开始前检查当前 commit 是否与 frozen_commit_hash 一致；
- 如果不一致，脚本拒绝运行，输出错误信息："当前 commit 不匹配 frozen version，请 git checkout <frozen_hash>"；
- environment report 的文件头必须明确写出使用的 commit hash，使其与正式 backtest 结果绑定。

这是防止"同一笔交易在不同 commit 上看到不同信号"的唯一方式。

## 第十部分：Claude Code / Codex 行为规范

### 每次接收任务时的必做检查

Claude Code 在执行任何策略相关任务前，必须：

1. **输出当前 Git 状态**：
   ```
   git branch -v
   git status
   git log --oneline -5
   ```
   这三条命令的输出必须在日志中可见，帮助用户和审计者确认当前工作环境。

2. **检查 working tree 是否 dirty**：
   如果 `git status` 显示有未 commit 的改动，不允许运行正式验证任务。必须先 commit，或者明确说明这是临时探索性工作（temporary exploratory work）。

3. **检查当前 branch**：
   如果当前处于 main 或 frozen-* 分支，不允许直接修改代码。必须切换到 feature 或 develop 分支，或者明确说明这是读操作（read-only）。

4. **检查 frozen commit**：
   如果任务涉及已冻结版本的分析，必须先 `git checkout <frozen_hash>` 确保分析基于冻结代码。

### Claude Code 禁止操作

- 禁止在 dirty working tree 上运行 `python run_backtest.py` 或其他正式验证脚本。
- 禁止在 frozen-* 或 main 分支上直接 `git commit`。所有修改必须通过 feature branch 提交。
- 禁止在未 commit 的情况下生成正式报告（audit report、attribution analysis 等）。
- 禁止修改已冻结版本的 signal_engine.py，即使只是"小改"。如果需要改进，必须新建 feature 分支和新版本号。
- 禁止跨 forward-live 分支混合历史数据，例如在 forward-v0.1 分支上添加来自 v0.0 的交易。

### Claude Code 推荐工作流

```
# 接收新任务
1. 输出: git branch -v && git status && git log --oneline -5
2. 确认: 当前是 feature/* 或 develop 分支，working tree 干净
3. 如果是冻结版本的分析，运行: git checkout <frozen_hash>
4. 执行分析
5. 输出: git diff (查看修改内容)
6. commit: git add -A && git commit -m "[STAGE] strategy_id=..., action=..."
7. 如果完成了 Stage，输出: git tag -a v<x.y>-<stage> -m "..."
8. 输出最终状态: git log --oneline -3
```

## 第十一部分：Reproducibility Checklist

任何声称"这个结果可复现"的正式产出，都必须通过以下检查表：

- [ ] 源代码已 commit 到 Git 仓库
- [ ] commit hash 明确记录在结果文件的头部注释中
- [ ] 如果有 git tag，tag 也记录在文件头部
- [ ] config.yaml 已 commit，hash 值已记录
- [ ] 数据起止日期已明确写出
- [ ] 运行命令（包括所有参数）已文档化
- [ ] 环境信息已记录（Python 版本、pandas 版本、OS）
- [ ] 生成时间戳已记录（精确到秒）
- [ ] working tree 在生成报告时是干净的（无未 commit 改动）
- [ ] 任何人能通过 commit hash 和参数重现该结果

如果任何一项未通过，该结果不能视为"可复现"，不能用于决策。
