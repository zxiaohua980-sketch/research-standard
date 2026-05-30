# 样本内、样本外与数据消费政策

## 核心原则

样本外不是一个文件名，也不是简单等同于时间更晚的数据。判断某段数据是否仍然是可靠的样本外证据，唯一标准是：

> 在最终规则、参数、成交模型、SL/TP、头寸规模和成本模型冻结之前，研究者是否已经看过这段数据并据此做过选择。

只要一段数据被用于发现模式、接受或拒绝 filter、调整止损止盈、挑选参数、选择市场或改变成本假设，它就已被研究过程消耗；之后只能作为开发历史，不能再称为独立最终样本外证据。

---

## 1. 术语定义

### IS: In-Sample / 样本内

`IS` 包括所有已用于开发决策的数据，而不只包括最初的训练集：

- 用来提出假说、发现特征或归因模式的数据；
- 用来筛选 filter、SL/TP、trailing、breakeven、timeout、position sizing 的数据；
- 用来选择参数、市场、周期、成本假设或评价门槛的数据；
- 任何看过结果后触发过代码、规则或参数调整的数据。

名称仍叫 `validation` 的数据，一旦参与选择，在后续最终评价语义中也属于已消费开发数据。

### OOS-Dev: Development Validation / 开发型样本外

`development_validation` 在某个候选提出时可以是相对于 discovery 的样本外数据，用于早期淘汰明显不稳的规则。它可以支持“进入下一开发阶段”，但不能证明策略完成验证。

规则：

- 首次查看前，它对当前候选是 OOS-Dev；
- 查看后如用其决定保留、删除或修改候选，它立即成为 consumed development data；
- 不得把同一 OOS-Dev 结果重新命名为 locked final holdout。

### OOS-Final: Locked Final Holdout / 最终锁定样本外

`locked_final_holdout` 是历史研究中唯一可用于最终决策的一次性独立评价集。

要求：

- 在研究协议开始时就切分并记录日期范围与数据 hash；
- 在 entry、exit、SL/TP、动态管理、position sizing、成本模型和全部参数固定前不得查看指标；
- 固定候选后仅运行一次；
- 结果无论好坏都必须报告；
- 若失败，该版本失败；不得利用此 holdout 修补后再次宣称其仍为 OOS-Final。

### WF-OOS: Walk-Forward Historical OOS / 回溯滚动样本外

walk-forward 中每个 test window 对对应训练窗口是历史样本外。它用于评估流程稳定性和参数漂移风险，但当整套 walk-forward 结果已被用于决定是否继续或怎样改规则时，这些窗口都成为已查看历史证据。

WF-OOS 不等同于 locked final holdout，也不等同于 forward-live。

### Forward-Live / 真正前向

`framework_start_time` 之后，基于已冻结策略新产生的信号和交易才是 forward-live。它不属于历史 OOS，不允许历史回填或规则调整污染。

---

## 2. 必须采用的四层结构

| 层级 | 名称 | 用途 | 是否允许据此改规则/选参 | 最终证据地位 |
|------|------|------|--------------------------|--------------|
| 1 | `discovery_train` | 假说、归因发现、初始搜索 | 允许 | IS |
| 2 | `development_validation` | 筛选候选、阻止明显过拟合 | 允许，但使用后记为 consumed | OOS-Dev，非最终 |
| 3 | `locked_final_holdout` | 对完整冻结候选做一次最终历史评价 | 不允许调整当前版本 | OOS-Final |
| 4 | `forward_live` | 冻结后真实新数据验证 | 不允许改冻结版本 | 最强前向证据 |

Stage 8 的 walk-forward 应在协议中明确其窗口来自哪一层数据。推荐只使用层级 1-2 做模型开发和稳健性检查，保留层级 3 完全不参与 walk-forward。

---

## 3. 数据消费台账

每个正式策略项目必须创建 `data_usage_ledger.yaml`，并在每次正式研究运行前更新。最低格式：

```yaml
strategy_id: STRAT_EXAMPLE_001
protocol_version: v0.1-dev
splits:
  discovery_train:
    range: "2020-01-01/2023-12-31"
    data_hash: "sha256:..."
    status: consumed_for_discovery
    permitted_uses:
      - attribution
      - candidate_generation
      - parameter_search
  development_validation:
    range: "2024-01-01/2024-12-31"
    data_hash: "sha256:..."
    status: locked_until_candidate_declared
    first_opened_at: null
    consumed_by_decisions: []
  locked_final_holdout:
    range: "2025-01-01/2025-05-31"
    data_hash: "sha256:..."
    status: sealed
    opened_at: null
    evaluated_version: null
  forward_live:
    range: "from framework_start_time"
    status: unavailable_before_freeze
decisions:
  - timestamp: "..."
    decision: "..."
    datasets_seen: ["discovery_train"]
```

### 状态转换

```text
sealed -> opened_once_for_final_evaluation -> consumed_final_holdout
locked_until_candidate_declared -> opened_for_candidate_screening -> consumed_development
```

`locked_final_holdout` 不得回到 `sealed`。换参数、补 filter 或改 SL/TP 后重测同一个 final holdout，是重复使用，不是新的 OOS。

---

## 4. 各阶段允许看的数据

| Stage | 允许使用的数据 | 禁止事项 |
|-------|----------------|----------|
| Stage 1-5 | `discovery_train`；候选写定后可用 `development_validation` 初筛 | 查看 final holdout 来发明规则 |
| Stage 6 | `discovery_train` + 已解锁的 `development_validation` | 因 final holdout 结果改逻辑 |
| Stage 7 | `discovery_train` 搜参，`development_validation` 评估平台与筛选 | 在 final holdout 上选参数 |
| Stage 8-10 | 开发层 walk-forward/regime/temporal 诊断；或对最终固定候选做只读 final report | 诊断后悄悄改变冻结候选并复用 final holdout |
| Stage 11 | 记录所有已消费数据和最终 holdout 一次结果 | 隐瞒已查看的数据 |
| Stage 12 | 仅 `framework_start_time` 后的新信号/交易 | 混入历史或根据初期输赢改冻结规则 |

**推荐顺序**：Stage 7 在 IS/OOS-Dev 上确定参数候选，Stage 8-10 仅在已消费开发历史上完成 walk-forward、regime 和 temporal 诊断，随后才打开 `locked_final_holdout` 一次，作为 Stage 11 冻结前的最终历史门槛。

**兼容旧流程**：如果某版本已经在 Stage 7 打开过 `locked_final_holdout`，该数据立即记为 `consumed_final_holdout`。后续 Stage 8-10 必须排除这段数据，且不得基于诊断修改当前版本；需要修改时必须建立新版本并保留全新的最终证据来源。

---

## 5. OOS 失败后的处理

### OOS-Dev 失败

候选可被拒绝，或在同一个开发周期内重新提出新候选；所有已查看的 OOS-Dev 数据记为 consumed，不再作为最终证据。

### OOS-Final 失败

当前版本结论必须记录为 `FAIL_ON_LOCKED_FINAL_HOLDOUT`。接下来可以：

1. 结束该策略；或
2. 建立新版本/新分支继续研究；
3. 将已失败的 final holdout 降级为新版本的开发已知数据；
4. 为新版本保留新的、尚未观察的未来数据或进入冻结后的 forward-live。

绝对禁止看到 OOS-Final 坏结果后修改策略，再在同一 OOS-Final 上宣布“修复成功”。

---

## 6. 报告必须明确标注的指标

所有正式报告不得只写 `OOS Sharpe`，必须标注证据类型：

```text
IS discovery_train Sharpe:
OOS-Dev development_validation Sharpe:
WF-OOS historical rolling test Sharpe:
OOS-Final locked_final_holdout Sharpe:
Forward-Live metrics (Gate status and framework_start_time):
```

若某项数据曾被用于任何决策，报告必须写明 `consumed_for_development: true`。

---

## 7. 对 Codex / Claude 的强制检查

在做归因、逻辑调整、参数优化、OOS 报告、冻结或 forward 评估前，必须先回答：

1. 这次运行读取的是 IS、OOS-Dev、OOS-Final、WF-OOS 还是 Forward-Live？
2. 该数据此前是否被查看或用于决策？证据在 `data_usage_ledger.yaml` 哪里？
3. 这次运行是否会消耗一个尚未打开的数据层？
4. 如果结果不好，允许做的是拒绝当前候选，还是仍可继续调整？

没有数据消费台账的现有策略，只能把既有历史结果标为 `legacy / split integrity unverified`；在补做切分和审计之前，不得宣称拥有可靠 OOS-Final 结果。
