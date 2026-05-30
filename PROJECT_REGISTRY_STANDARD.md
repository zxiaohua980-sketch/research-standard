# 项目登记规范（Stage 0）

## 核心原则

所有策略都必须登记到中央 registry。Registry 是跨目录协调的唯一权威记录，用于追踪策略的状态、版本、责任人、关键里程碑。没有 registry 记录的策略不允许进入正式研究。

---

## 第一部分：Registry 文件位置

**主 registry**：`D:\MT5\research_registry\strategy_registry.yaml`

**Fallback registry**（如主 registry 不可用）：`D:\MT5\RESEARCH_STANDARD\strategy_registry_backup.yaml`

---

## 第二部分：Registry 条目的必需字段

每个策略条目必须包含以下字段：

```yaml
- strategy_id: STRAT_RSI_001
  strategy_name: RSI Oversold Reversal on EUR/USD H1
  
  # 路径和仓库
  root_path: D:\MT5\strategies\STRAT_RSI_001
  git_repo: https://github.com/user/STRAT_RSI_001
  git_branch: develop
  latest_commit: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
  latest_commit_message: "[OPTIM] Parameter optimization complete"
  
  # 当前阶段和状态
  current_stage: stage_12_forward_live
  current_status: forward_live_active
  
  # 版本控制
  current_version: v0.1
  frozen_commit: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
  frozen_tag: v0.1-frozen
  frozen_timestamp: 2025-06-01 10:30:00 UTC
  
  # Forward-live 追踪
  forward_live_branch: forward-v0.1
  forward_live_commit: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
  framework_start_time: 2025-06-01 11:00:00 UTC
  
  # 关键文件
  key_files:
    signal_engine: signal_engine.py (hash: abc123)
    backtest: backtest.py (hash: def456)
    config: config.yaml (hash: ghi789)
    version: version.json (hash: jkl012)
  
  # 最新结果
  last_result: Forward-Live Sharpe 0.95 (35 trades, Gate A pass)
  last_result_date: 2025-09-15
  evidence_type: forward_live  # IS | OOS-Dev | WF-OOS | OOS-Final | forward_live | legacy_unverified
  data_usage_ledger: data_usage_ledger.yaml
  
  # 下一步行动
  next_action: Monitor forward-live performance, target Gate B (50 trades)
  expected_next_milestone_date: 2025-12-15
  
  # 责任和联系
  owner_machine: machine_001
  owner_name: Claude Code
  last_updated: 2025-09-15 14:30:00 UTC
  
  # 性能总结
  performance_summary:
    backtest_sharpe: 1.20
    forward_sharpe: 0.95
    backtest_trades: 234
    forward_trades: 35
    performance_trend: Stable
    regime_sensitivity: High
    
  # 风险和限制
  risks_and_limitations:
    - "Performance declining since 2020 (2.1 → 0.95, -55%)"
    - "Highly sensitive to market environment (Sharpe 0.2-1.9)"
    - "May be losing effectiveness as market adapts"
  
  # 标签和分类
  tags:
    - reversal
    - rsi
    - short_timeframe
    - eur_usd
  
  # 禁止操作标记
  do_not_modify: false
  do_not_delete: false
  production_live: false
```

---

## 第三部分：Registry 的维护规则

### 创建新条目

1. **Stage 0（Project Registration）时创建**：
   - 必须有 strategy_id
   - 必须有 root_path
   - 必须有 git_repo
   - current_stage 初始化为 "stage_0_registration"
   - current_status 初始化为 "active"

2. **初始记录示例**：
   ```yaml
   - strategy_id: STRAT_NEW_001
     strategy_name: New Strategy Idea
     root_path: D:\MT5\strategies\STRAT_NEW_001
     git_repo: https://github.com/user/STRAT_NEW_001
     git_branch: develop
     latest_commit: 1234567890abcdef
     current_stage: stage_0_registration
     current_status: active
     current_version: v0.0
     owner_machine: machine_001
     last_updated: 2025-09-15 10:00:00 UTC
   ```

### 更新条目

每个阶段完成后，必须更新 registry：

```
Stage 1 完成: current_stage = "stage_1_hypothesis"
Stage 2 完成: current_stage = "stage_2_execution_audit"
...
Stage 11 完成: current_stage = "stage_11_frozen", frozen_tag = "v0.1-frozen"
Stage 12 开始: current_stage = "stage_12_forward_live", forward_live_branch = "forward-v0.1"
```

### 关键转折点

以下时刻必须更新 registry：

1. **冻结时**（Stage 11）：
   ```yaml
   frozen_commit: <hash>
   frozen_tag: v0.1-frozen
   frozen_timestamp: <time>
   ```

2. **进入 forward-live 时**（Stage 12）：
   ```yaml
   forward_live_branch: forward-v0.1
   framework_start_time: <time>
   current_status: forward_live_active
   ```

3. **通过 Gate 时**：
   ```yaml
     current_status: forward_live_gate_a_pass  # 或 gate_b_pass
   ```

4. **部署到生产时**（Stage 13）：
   ```yaml
   current_status: production_live
   production_live: true
   ```

5. **声称 OOS 或迁移历史策略时**：
   ```yaml
   evidence_type: OOS-Final  # 必须明确是哪类证据
   data_usage_ledger: data_usage_ledger.yaml
   ```
   缺少数据消费台账的旧项目必须标记 `evidence_type: legacy_unverified`，既有结果不得直接表述为独立最终样本外验证。

### 撤销或弃用策略

如果策略失效或被放弃：

```yaml
current_status: abandoned  # 或 deprecated, paused
do_not_modify: true
do_not_delete: false
reason_for_status_change: "Performance degradation > 50%, market adaptation suspected"
last_result: "Final Sharpe 0.5, no longer viable"
```

---

## 第四部分：Registry 的查询和使用

### 按状态查询

找出所有处于某个阶段的策略：

```bash
# 所有进行中的策略
grep "forward_live_active" strategy_registry.yaml

# 所有已冻结的版本
grep "stage_11_frozen" strategy_registry.yaml | cut -d: -f2

# 所有已部署的策略
grep "production_live: true" strategy_registry.yaml
```

### 按策略 ID 查询

```bash
# 查找特定策略
grep "STRAT_RSI_001:" strategy_registry.yaml -A 50
```

### 生成报告

```bash
# 列出所有活跃策略和其状态
python scripts/registry_report.py --status active

# 生成按阶段的统计
python scripts/registry_stats.py

# 输出：
# Stage 0 (Registration): 2 策略
# Stage 6 (Logic Refinement): 1 策略
# Stage 12 (Forward-Live): 3 策略
# Production: 1 策略
# Abandoned: 2 策略
```

---

## 第五部分：Registry 的完整性检查

定期运行完整性检查，确保 registry 与实际文件系统一致：

```python
def registry_integrity_check():
    """检查 registry 条目与实际目录的一致性"""
    
    registry = load_yaml('strategy_registry.yaml')
    
    for entry in registry:
        strategy_id = entry['strategy_id']
        root_path = entry['root_path']
        git_repo = entry['git_repo']
        
        # 检查 1：root_path 是否存在
        if not os.path.exists(root_path):
            warn(f"{strategy_id}: root_path does not exist: {root_path}")
        
        # 检查 2：Git repo 是否初始化
        if not os.path.exists(f"{root_path}/.git"):
            warn(f"{strategy_id}: not a git repo")
        
        # 检查 3：关键文件是否存在
        required_files = ['signal_engine.py', 'backtest.py', 'config.yaml', 'version.json']
        for file in required_files:
            if not os.path.exists(f"{root_path}/{file}"):
                warn(f"{strategy_id}: missing {file}")
        
        # 检查 4：latest_commit 是否与 git log 一致
        git_latest = get_latest_commit(root_path)
        if entry['latest_commit'] != git_latest:
            warn(f"{strategy_id}: latest_commit mismatch (registry vs git)")
            entry['latest_commit'] = git_latest  # 自动更新
        
        # 检查 5：frozen_tag 是否存在（如果是冻结状态）
        if entry['current_stage'] == 'stage_11_frozen':
            if not tag_exists(root_path, entry['frozen_tag']):
                warn(f"{strategy_id}: frozen_tag does not exist: {entry['frozen_tag']}")
        
        # 检查 6：forward_live_branch 是否存在（如果是 forward-live 状态）
        if 'forward_live' in entry['current_status']:
            if not branch_exists(root_path, entry['forward_live_branch']):
                warn(f"{strategy_id}: forward_live_branch does not exist: {entry['forward_live_branch']}")
    
    print("Registry integrity check complete")
```

---

## 第六部分：Registry 的备份和版本控制

### 备份策略

Registry 本身应该被 Git 版本控制：

```bash
cd D:\MT5\research_registry
git add strategy_registry.yaml
git commit -m "Update registry: STRAT_RSI_001 forward-live active"
git push
```

### Fallback Registry

在主 registry 损坏时，使用备份：

```yaml
# D:\MT5\RESEARCH_STANDARD\strategy_registry_backup.yaml
# 定期（每周）手动备份
```

---

## 第七部分：Registry 条目示例

### 示例1：新建策略（Stage 0）

```yaml
- strategy_id: STRAT_NEW_MACD_001
  strategy_name: MACD Crossover Strategy
  root_path: D:\MT5\strategies\STRAT_NEW_MACD_001
  git_repo: https://github.com/user/STRAT_NEW_MACD_001
  git_branch: develop
  latest_commit: abc123...
  current_stage: stage_1_hypothesis
  current_status: active
  current_version: v0.0
  owner_machine: machine_001
  last_updated: 2025-09-15
  next_action: Complete hypothesis and Execution Audit
```

### 示例2：进行中的策略（Stage 7）

```yaml
- strategy_id: STRAT_BB_002
  strategy_name: Bollinger Bands Breakout
  root_path: D:\MT5\strategies\STRAT_BB_002
  git_repo: https://github.com/user/STRAT_BB_002
  git_branch: develop
  latest_commit: def456...
  current_stage: stage_7_parameter_optimization
  current_status: active
  current_version: v0.1
  owner_machine: machine_001
  last_updated: 2025-09-10
  last_result: Parameter optimization running, expected complete 2025-09-25
  next_action: Complete parameter optimization, move to Stage 8
```

### 示例3：已冻结策略（Stage 11）

```yaml
- strategy_id: STRAT_RSI_001
  strategy_name: RSI Oversold Reversal
  root_path: D:\MT5\strategies\STRAT_RSI_001
  git_repo: https://github.com/user/STRAT_RSI_001
  git_branch: main
  latest_commit: ghi789...
  current_stage: stage_11_frozen
  current_status: frozen
  current_version: v0.1
  frozen_commit: ghi789...
  frozen_tag: v0.1-frozen
  frozen_timestamp: 2025-06-01 10:30:00
  owner_machine: machine_001
  last_updated: 2025-06-01
  last_result: Backtest Sharpe 1.20 (234 trades), Walk-Forward 1.19
  next_action: Deploy to Stage 12 forward-live
```

### 示例4：前向交易策略（Stage 12）

```yaml
- strategy_id: STRAT_RSI_001
  strategy_name: RSI Oversold Reversal
  root_path: D:\MT5\strategies\STRAT_RSI_001
  git_repo: https://github.com/user/STRAT_RSI_001
  git_branch: forward-v0.1
  latest_commit: jkl012...
  current_stage: stage_12_forward_live
  current_status: forward_live_gate_a_pass
  current_version: v0.1
  frozen_commit: ghi789...
  frozen_tag: v0.1-frozen
  forward_live_branch: forward-v0.1
  framework_start_time: 2025-06-01 11:00:00
  owner_machine: machine_001
  last_updated: 2025-09-15
  last_result: Forward-Live Sharpe 0.95 (35 trades, Gate A pass), 70% toward Gate B
  next_action: Continue collecting forward data, target 50 trades (Gate B)
  expected_next_milestone_date: 2025-12-15
```

---

## 总结

Registry 是策略研究过程中的关键记录系统。通过统一的、可查询的、自动检查的 registry，我们能够：
1. 追踪所有策略的当前状态和版本
2. 防止策略"丢失"或被遗忘
3. 快速定位某个策略的位置和状态
4. 支持跨团队、跨电脑的协调
5. 为审计和合规性提供清晰的记录

registry 的维护应该成为每次研究里程碑时的常规操作。
