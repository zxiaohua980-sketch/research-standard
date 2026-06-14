# 量化策略开发速查表

## 🎯 核心公式

```
成功的策略 = 正确的假说 + 严格的审计 + 深度的归因 + 稳健的优化 + 充分的验证 + 长期的前向
失败的策略 = 直觉假说 + 跳过审计 + 盲目加 filter + 全样本优化 + 忽视验证 + 短期过拟合
```

---

## 🚫 十三大禁区（必背）

1. ❌ 没审计就信回测结果 → `先读 Stage 2`
2. ❌ 没归因就加 filter → `先读 TRADE_ATTRIBUTION_STANDARD.md`
3. ❌ 用全样本选参数 → `先读 OPTIMIZATION_POLICY.md`
4. ❌ 把历史回填当 forward → `先读 FORWARD_VALIDATION_STANDARD.md`
5. ❌ forward 中修改冻结策略 → `先读 VERSIONING_AND_FREEZE_POLICY.md`
6. ❌ 连亏几笔就改策略 → `等 30 笔以上样本`
7. ❌ 为提高 PF 盲目扫参 → `目标是稳健性，不是最高数字`
8. ❌ 没注册到 registry → `先读 PROJECT_REGISTRY_STANDARD.md`
9. ❌ 策略目录混乱 → `按 STRATEGY_DEVELOPMENT_STANDARD.md 建立`
10. ❌ 不开新版本就改规则 → `改规则 = 新版本 = 新 tag`
11. ❌ MTF 未审计就信回测 → `先读 MTF_LOOKAHEAD_AND_VERSION_ISOLATION_STANDARD.md`
12. ❌ 跨版本读取旧输出 → `一个版本，一个文件夹`
13. ❌ 审计时顺手优化 → `先读 STRICT_AUDIT_ENFORCEMENT_STANDARD.md，只修安全缺陷`

---

## 🧯 Strict Audit Enforcement Mode（查错时必用）

触发：未来函数审计、MTF 泄漏、普通回测 vs 逐根回测差异、pivot/swing/structure 确认顺序、execution timing、runtime safety、候选批准。

只允许：
- 修 lookahead/leakage；
- 修时间对齐；
- 加 `feature_available_at` / `signal_time` / `execution_time` 元数据；
- 加断言、replay 检查和版本路径守卫；
- 输出审计报告。

禁止：
- 改入场/出场逻辑；
- 改指标公式；
- 调参数、RR、PF、胜率、交易数量；
- 把安全修复后的指标说成“优化提升”。

核心时间模型：

```text
bar_open_time <= feature_available_at <= signal_time <= execution_time
MT5 bar_close_time = next_bar_open_time
```

硬失败标记：
- `LOOKAHEAD_LEAK_DETECTED`
- `MULTI_TIMEFRAME_LOOKAHEAD_DETECTED`
- `REPAINTING_OR_LOOKAHEAD_FAIL`

输出必须有：`AUDIT_STATUS`、问题列表、文件/函数位置、最小补丁、batch-vs-incremental replay 结果。

---

## 🧬 开启新版本三件套

Phase 2+ 一旦开启新版本，必须先做：

1. **新目录**：`versions/<new_version>/`
2. **新 py 文件**：复制父版本 active `.py` 到新目录，例如 `src/strategy_v0_2.py`
3. **新上下文**：新建 Codex thread/对话；如果不能新建，写 `NEW_VERSION_HANDOFF.md` 并从它重启上下文

然后：

- 先审计 copied baseline；
- 再修改逻辑；
- 结束时清理临时/无效文件；
- 写 `CLEANUP_LOG.md`。

禁止：直接在父版本 `.py` 上改，或用旧版本长对话记忆当成当前版本事实。

---

## 🧹 文件清理规则

及时删除：
- `__pycache__`、`.pyc`、`.tmp`、半截输出；
- debug dump、临时 CSV/JSON/HTML/MD；
- 未绑定 version/root/hash 的 `latest/final/new/copy/副本/saved_runs`；
- 已汇总进报告的重复临时图表和日志。

不要乱删：
- 原始市场数据、ledger、manifest；
- audit/replay/attribution 报告；
- frozen、forward-live、runtime 订单/对账日志；
- 用户提供的源文件和 registry 记录。

不确定：移动到 `versions/<version>/_trash_review/<timestamp>/`，再写 `CLEANUP_LOG.md`。

---

## 📅 典型开发时间表

```
Week 1
├─ Day 1: 建立项目目录 + 写假说 (8 小时)
├─ Day 2-3: 审计 + 第一版回测 (16 小时)
└─ Day 4-5: 事件研究 + 归因分析 (16 小时)

Week 2
├─ Day 1-2: 加 filter + 优化逻辑 (16 小时)
├─ Day 3-4: 参数优化 (16 小时)
└─ Day 5: 回溯时间序列验证 (8 小时)

Week 3
├─ Day 1-2: 环境诊断 + 时间诊断 (16 小时)
├─ Day 3: 冻结版本 (4 小时)
└─ Day 4-5: 前向交易开始 (持续)

总计: ~100-120 小时（2-3 周）
```

---

## 🔍 交易归因 - 最关键的一步

### 七层检验 (Pass all or don't add filter)

| # | 检验 | 标准 | 快速检查 |
|---|------|------|---------|
| 1 | 入场前可见 | filter 特征在 entry bar 已知 | ✓ yes or ✗ no |
| 2 | 样本数 | >= 30 笔 | 数出来 |
| 3 | 减亏 | 亏损笔数下降 20% 以上 | (old_losses - new_losses) / old_losses |
| 4 | 误杀 | 误杀赢利 < 30% | (killed_winners / total_winners) |
| 5 | 年份 | 所有 5+ 个年份都有效 | for year in 2020-2024: check +3pp+ |
| 6 | Regime | 高波动/低波动 都有效 | split by ATR, both improved |
| 7 | OOS-Dev | 开发验证集也有效 | discovery +5pp, dev validation +4pp → 可进入 Stage 6 |

**如果全部通过 → ACCEPT**  
**如果任何一项失败 → REJECT**

---

## 📊 IS / OOS 四层分离（必须做）

```
✓ discovery_train（IS）
  └─ 搜索参数空间 (grid search)
     └─ 输出全部候选（不只最优）

✓ development_validation（OOS-Dev）
  └─ 初步评估与筛选（查看后即 consumed）
     └─ 排除过度拟合的候选

✓ locked_final_holdout（OOS-Final）
  └─ 完整规则/参数/SL/TP 固定后只查看一次
     └─ 失败则该版本失败，不在该数据上补丁

✓ forward_live
  └─ 冻结时刻之后新产生的信号和交易
```

**时间顺序严格不能乱！**

---

## 🎲 环境诊断五维度速查

| 维度 | 快速检查 | 注意事项 |
|------|----------|---------|
| **ATR** | split by <0.5, 0.5-1.0, >1.0 | 低 ATR 往往更差 |
| **Trend** | split by uptrend/downtrend/range | 趋势方向性影响 |
| **Session** | split by London/NY/Asia | 时段流动性差异 |
| **Volatility** | mark volatility_surge periods | transition 时期弱 |
| **Time** | split by year, month, rolling | 衰减迹象 |

**重要**: 发现坏的 regime → 记录但不删除  
低于 30 笔样本 → 标记 low_sample，不可信

---

## 🔐 版本控制关键点

```
第一个版本: v0.1（通过全部验证）
    ↓ git tag v0.1-frozen
    ↓ 开始 forward-live
    
改了规则? → 新版本 v0.2
    ↓ git tag v0.2-frozen
    ↓ 新的 forward-v0.2 分支

forward 中修改规则?
    ✓ 创建新 commit（mark forward phase）
    ✗ 不能改参数或代码
```

---

## 📝 必须写的文件清单

### 每个策略项目必有

```
signal_engine.py        ← 信号逻辑（绝对不能混）
backtest.py            ← 交易执行（绝对不能混）
config.yaml            ← 参数配置
.gitignore             ← 排除输出文件
version.json           ← 版本记录
version_manifest.yaml  ← Phase 2+ 版本根目录记录
NEW_VERSION_HANDOFF.md ← Phase 2+ 新版本上下文入口
CLEANUP_LOG.md         ← Phase 2+ 临时/无效文件清理记录
README.md              ← 项目文档
```

### 每个阶段生成的报告

```
Stage 2: execution_audit.md
Strict audit: strict_audit_enforcement_report.md（查未来函数/重放差异/safety hardening）
Stage 2 MTF: mtf_timing_audit.md（多周期必需）
Phase 2+: version_isolation_check.json
Stage 3: event_study_report.md
Stage 4: fixed_rule_backtest.md
Stage 5: trade_attribution.md ⭐⭐⭐
Stage 6: logic_refinement.md
Stage 7: optimization_report.md
Stage 8: walk_forward_report.md
Stage 9: regime_validation.md
Stage 10: temporal_validation.md
Stage 11: version.json + git tag
Stage 12: forward_live_state.json
Phase 3: source_preflight_last.json + runtime_audit_report.md + EXE/config hashes
```

### Phase 3 EXE 打包速查

- [ ] 先读 `MT5_RUNTIME_PACKAGING_STANDARD.md`
- [ ] 源码版用最终 `config.ini` 跑通一轮
- [ ] audit/preflight 无 FAIL
- [ ] 再 PyInstaller 打包
- [ ] 直接双击 EXE 能运行，不依赖 BAT
- [ ] 控制台有动态扫描/对账输出
- [ ] `config.ini` 外置 `refresh_seconds`、每单投入金额、最大持仓/手数、挂单时长
- [ ] MT5 API 获取本机数据，缓存最近 3000 根已完成 K 线
- [ ] 写入 runtime/error/reconciliation/order/position 日志
- [ ] 换路径复制后 EXE 仍能运行
- [ ] 交付目录只保留 EXE、`config.ini`、空 `logs\`、空 `data_cache\`

---

## ✅ 每日检查清单

### 开始工作
- [ ] git status (working tree clean?)
- [ ] git log -1 (last commit message?)
- [ ] 今天属于哪个 Stage?
- [ ] 读相关 MD 文档 (5 min)

### 完成工作
- [ ] 生成该阶段的报告
- [ ] git add <files>
- [ ] git commit -m "[STAGE] ..."
- [ ] git log -1 (verify)

---

## 🚨 常见错误及解救

| 错误 | 症状 | 救救我 |
|------|------|--------|
| 全样本优化 | Sharpe 很高但 OOS 崩坏 | 用 IS/OOS-Dev/OOS-Final/Forward 重新设计，并登记已消费数据 |
| 前视偏差 | backtest Sharpe > 2.0 | 检查是否用了未来数据 |
| MTF 未来函数 | 普通回测和逐根回测差距巨大 | 检查高周期 `available_at <= decision_time` |
| pivot/swing 重绘 | 成品回测好、逐根消失 | 检查 `pivot_detect <= confirm <= signal` |
| 跨版本读错文件 | 新版本结果解释不清 | 检查 `versions/<version>/` 和路径守卫 |
| 旧版本上下文混乱 | 不知道当前改的是哪版 | 新建 thread，写 `NEW_VERSION_HANDOFF.md` |
| 临时文件污染 | latest/final/copy 一堆 | 清理或移入 `_trash_review/`，写 `CLEANUP_LOG.md` |
| 样本太小加 filter | 优化了但前向崩盘 | 要求 >= 30 笔样本 |
| 环境不好删掉 | Sharpe 漂亮但现实失效 | 不要删，这是市场真相 |
| 连亏就改 | 频繁改规则 | 等 30 笔再评估 |
| 不知道哪版本赚钱 | 无法复现 | 每个结果都记 commit hash |

---

## 💡 一句话规则

| 规则 | 核心 |
|------|------|
| **审计优先** | 没审计的数字 = 0 |
| **归因至上** | 没归因不加 filter |
| **四层必须** | IS/OOS-Dev/OOS-Final/Forward 不能乱 |
| **OOS 要封存** | 看过并用于选择的数据不再是最终 OOS |
| **假说驱动** | 凭数据选参，不凭直觉 |
| **环境尊重** | 找出弱点，不要删除 |
| **版本清晰** | commit hash 是真理 |
| **目录隔离** | 一个版本，一个文件夹 |
| **新版本三件套** | 新目录 + 新 py + 新 thread |
| **文件清理** | 无效/临时文件及时删，不确定进 `_trash_review` |
| **MTF 严格** | 高周期必须先完成再可用 |
| **审计纯粹** | 查错时只修安全缺陷，不顺手优化 |
| **冻结严格** | forward 中一个标点都不改 |
| **样本至上** | < 30 笔 = 无效 |
| **时间验证** | 前向是最后的试金石 |

---

## 🔗 文档速查地图

```
想开发新策略
├─ 先读: README.md (1 min)
├─ 再读: CLAUDE.md 十三大禁区 (3 min)
├─ 建立: STRATEGY_DEVELOPMENT_STANDARD.md
└─ 开发: RESEARCH_WORKFLOW.md Stage 1-4

第一次回测有结果
├─ 读: TRADE_ATTRIBUTION_STANDARD.md ⭐
├─ 分析: winners vs losers
├─ 评估: 七层检验
└─ 决定: 加 filter or 不加

要优化参数
├─ 读: OPTIMIZATION_POLICY.md
├─ 读: DATA_SPLIT_AND_OOS_POLICY.md
├─ 做: IS/OOS-Dev/OOS-Final/Forward 分离
└─ 输出: 全部候选

要诊断性能
├─ 读: REGIME_VALIDATION_STANDARD.md
├─ 分析: 5 维度分层
└─ 记录: 弱点但不删

要冻结版本
├─ 读: VERSIONING_AND_FREEZE_POLICY.md
├─ 生成: version.json + version_manifest.yaml
├─ 通过: MTF timing / version isolation checks
└─ 打标: git tag v0.1-frozen

要开始 forward
├─ 读: FORWARD_VALIDATION_STANDARD.md
├─ 创建: forward-v0.1 分支
└─ 监控: Gate A/B 进度

怕做错
├─ 读: CLAUDE.md
├─ 审计/查错: STRICT_AUDIT_ENFORCEMENT_STANDARD.md
├─ 查: CHEATSHEET.md (本文件)
└─ 问: 规范文档是你的律师
```

---

## 📞 求救热线

| 问题 | 查哪个文件 | 搜关键词 |
|------|----------|----------|
| 新策略怎么开始 | STRATEGY_DEVELOPMENT_STANDARD.md | "必需的目录结构" |
| 怎么检查前视偏差 | RESEARCH_WORKFLOW.md Stage 2 | "Data Leakage Check" |
| 多周期怎么防未来函数 | MTF_LOOKAHEAD_AND_VERSION_ISOLATION_STANDARD.md | "feature_available_at" |
| 如何防止跨版本读错文件 | MTF_LOOKAHEAD_AND_VERSION_ISOLATION_STANDARD.md | "One Version, One Folder" |
| 可以加这个 filter 吗 | TRADE_ATTRIBUTION_STANDARD.md | "七层检验" |
| 全样本优化行不行 | OPTIMIZATION_POLICY.md | "禁止1" |
| 为什么环境诊断不能删环境 | REGIME_VALIDATION_STANDARD.md | "禁止的做法" |
| forward 能改参数吗 | FORWARD_VALIDATION_STANDARD.md | "四大约束" |
| 版本号怎么定 | VERSIONING_AND_FREEZE_POLICY.md | "版本号规范" |
| 怎么记录 commit | GIT_AND_REPRODUCIBILITY_STANDARD.md | "Commit Message 格式" |

---

## ⏱️ 快速评估是否可行

```
新想法来了? 问自己:

1. 有假说吗? NO → 去 Stage 1 写假说 (30 min)
2. 审计过吗? NO → 去 Stage 2 审计 (1 day)
3. 做过归因吗? NO → 去 Stage 5 做归因 (2-3 days)
4. 通过七层检验吗? NO → 这个想法不可行
5. YES → 进入 Stage 6 开发
```

---

## 🎯 核心数字记住

| 数字 | 含义 |
|------|------|
| **30** | 最小样本量（< 30 不统计） |
| **3 months + 30** | Forward Gate A（基础确认） |
| **50** | Forward Gate B（充分确认） |
| **0.05** | p-value 显著性阈值（< 0.05 OK） |
| **4** | 数据证据层级（IS、OOS-Dev、OOS-Final、Forward-Live） |
| **5** | 最少年份数（跨年份验证） |
| **20%** | OOS 衰减上限（train-OOS 差异 > 20% 警惕） |
| **30%** | 误杀赢利上限（> 30% 不能加 filter） |

---

## 最后的最后

> 如果你记不住所有规则，**只需记住一句**：
>
> **"先审计，后研究；先归因，后优化；先冻结，后前向。"**
>
> 其他都是这三个原则的展开。

---

**打印这个文件，贴在你的电脑旁边。** 🖨️

每当想偷懒时，看一眼十三大禁区，冷静下来。
