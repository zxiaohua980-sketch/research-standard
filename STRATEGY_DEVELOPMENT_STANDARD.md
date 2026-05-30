# 策略开发项目结构规范

## 核心原则

量化策略的成功开发依赖于清晰的代码分层和职责划分。信号定义、交易执行、环境诊断、前向处理必须分离，不允许把所有逻辑混在一个脚本里。这种分层不仅便于审计和验证，也是防止过拟合的关键。每个组件都必须有明确的输入和输出，可以独立测试。

---

## 必需的目录结构

每个正式策略项目必须包含以下目录和文件：

```
strategy_root/
├── .git/                          # Git 仓库
├── .gitignore                     # 文件忽略列表
├── README.md                      # 项目文档
├── version.json                   # 版本信息
├── data_usage_ledger.yaml         # IS/OOS 数据切分和消费台账
│
├── signal_engine.py               # 信号生成引擎（Stage 1-3）
├── backtest.py                    # 回测执行引擎（Stage 4）
├── config.yaml                    # 参数和规则配置
│
├── tests/
│   ├── test_signal_engine.py      # 信号引擎单元测试
│   ├── test_backtest.py           # 回测逻辑单元测试
│   └── test_integration.py        # 集成测试
│
├── analysis/
│   ├── event_study.py             # Stage 3 事件研究脚本
│   ├── attribution.py             # Stage 5 交易归因脚本
│   ├── environment_validation.py  # Stage 9 环境诊断脚本
│   ├── temporal_validation.py     # Stage 10 时间诊断脚本
│   └── walk_forward.py            # Stage 8 回溯验证脚本
│
├── forward_live/
│   ├── forward_live_runner.py     # Stage 12 前向交易执行
│   ├── forward_live_config.yaml   # 前向配置
│   ├── forward_live_signals.csv   # 前向信号记录
│   ├── forward_live_trades.csv    # 前向交易记录
│   └── integrity_check.py         # 完整性验证脚本
│
└── output/
    ├── reports/
    │   ├── v0.1/
    │   │   ├── execution_audit.md
    │   │   ├── backtest_result.csv
    │   │   └── trades_detail.csv
    │   └── v0.2/
    ├── regime/
    │   ├── v0.1_environment_validation.md
    │   └── ...
    ├── forward/
    │   ├── v0.1_gate_progress.csv
    │   └── ...
    └── temp_*/ (临时输出，可删除)
```

---

## 核心模块职责

### 1. signal_engine.py（信号生成引擎）

**职责**：根据当时已知的市场数据，生成交易信号。信号生成必须是纯函数，不涉及风险管理、交易执行或统计分析。

若策略按 bar close 生成信号，`bar t` 的 close 可用于在收盘后形成决策，但成交必须交给执行引擎在 `bar t+1` 的首个可成交报价处理。信号引擎不得暗含“按刚看到的 close 成交”的假设。

**必须包含的类和方法**：

```python
class SignalEngine:
    def __init__(self, config):
        # 从 config 中加载参数
        self.rsi_period = config['RSI_period']
        self.atr_threshold = config['ATR_threshold']
        self.symbol = config['symbol']
        self.timeframe = config['timeframe']
    
    def calculate_rsi(self, prices):
        # RSI 计算，基于前一根 bar（防止前视偏差）
        # 返回 RSI 数组
        pass
    
    def calculate_atr(self, high, low, close):
        # ATR 计算
        pass
    
    def generate_signal(self, bars_data, bar_index):
        # 核心信号生成逻辑
        # 输入：历史 bars 数据（至 bar_index）
        # 输出：signal 对象（如果有信号）或 None
        # 关键：在 bar_index 处，不能使用 bar_index+1 的数据
        pass
    
    def backtest_generate_signals(self, historical_data):
        # 回测模式：对所有历史 bars 生成信号
        # 输出：signals 列表，每个元素是 {'timestamp': ..., 'type': 'LONG', ...}
        pass
```

**输入**：
- historical bars data（OHLC）
- config（parameters）

**输出**：
- signal objects（时间戳、信号类型、强度等）

**禁止**：
- 不得混入 risk management（SL/TP 不在这里设置）
- 不得混入统计分析（这里只生成信号）
- 不得使用 hindsight 特征（未来数据）

---

### 2. backtest.py（回测执行引擎）

**职责**：基于信号和风险管理规则，执行交易逻辑，计算 PnL。必须分离"信号的出现"和"交易的执行"。

执行引擎必须实现并配置：决策/成交时点、LONG/SHORT 对应 bid/ask、spread/commission/slippage/swap、gap fill、同一 OHLC bar 同时触及 SL/TP 的处理规则，以及 position sizing 和 broker/MT5 限制。详细门槛见 `EXIT_RISK_AND_LOGIC_REFINEMENT_STANDARD.md`。

**必须包含的类和方法**：

```python
class BacktestEngine:
    def __init__(self, config, signals):
        self.signals = signals
        self.entry_rule = config['entry_rule']  # 何时进场
        self.exit_rule = config['exit_rule']    # 何时出场
        self.risk_model = config['risk_model']  # SL/TP 设置
        self.commission = config['commission']
        self.slippage = config['slippage']
    
    def calculate_sl_tp(self, entry_price, entry_signal):
        # 根据 entry 价格和信号强度，计算 SL 和 TP
        # 必须在订单成交时由当时已知信息计算完成
        stop_loss = entry_price - self.risk_model['sl_pips']
        take_profit = entry_price + self.risk_model['tp_pips']
        return stop_loss, take_profit
    
    def check_exit_condition(self, trade, current_bar, bar_index):
        # 检查是否满足出场条件
        # 输入：当前持仓和当前 bar 数据
        # 输出：exit 对象（时间戳、原因、价格）或 None
        pass
    
    def process_bar(self, bar, bar_index, open_trades):
        # 处理单个 bar：检查新信号、更新现有持仓、处理出场
        # 输出：新建的交易、平仓的交易
        pass
    
    def run_full_backtest(self, historical_data, signal_data):
        # 完整回测：逐 bar 处理
        # 输出：完整的交易列表（entry_time, entry_price, exit_time, exit_price, pnl, ...）
        trades = []
        for bar_index, bar in enumerate(historical_data):
            new_trades = self.process_bar(bar, bar_index, open_trades)
            trades.extend(new_trades)
        return trades
```

**输入**：
- signal objects（from signal_engine）
- historical bars data
- config（risk model, commission, etc.）

**输出**：
- trade objects（完整的交易记录，含所有属性）

**禁止**：
- 不得在回测中修改信号定义
- 不得在回测中优化参数
- 不得混入统计分析

---

### 3. config.yaml（参数配置文件）

**职责**：集中管理所有参数和规则，便于版本管理和冻结。

**必须包含的字段**：

```yaml
strategy:
  id: STRAT_RSI_001
  name: RSI Oversold Reversal
  symbol: EUR/USD
  timeframe: H1

signal_config:
  type: RSI_threshold
  parameters:
    rsi_period: 14
    rsi_threshold: 30
  environment_filters:
    atr_threshold: 0.8
    session: ["London", "NY"]

risk_model:
  position_size: 0.01  # 账户百分比
  stop_loss: 1.0       # 相对于 SL 点数的倍数
  take_profit: 1.5
  max_concurrent: 5

execution:
  commission: 0.001    # 佣金（往返）
  spread: 0.0002       # 点差
  slippage: 0.00005    # 滑点

backtest:
  data_start: "2020-01-01"
  data_end: "2025-05-31"
  exclude_news_events: true

forward_live:
  framework_start_time: "2025-06-01 11:00:00"
  frozen_commit_hash: "a1b2c3d4e5f6"
  data_source: "oanda"
```

**冻结时的行为**：
- 一旦策略进入 Stage 11 冻结，config.yaml 的版本被锁定
- 任何参数修改都必须新建版本（v0.2）
- 版本历史通过 Git tag 记录

---

### 4. tests/（单元和集成测试）

**职责**：验证每个组件的正确性，防止逻辑错误在回测中隐藏。

**必须包含的测试**：

```python
# test_signal_engine.py
def test_rsi_calculation():
    # 验证 RSI 是否按标准公式计算
    engine = SignalEngine(config)
    prices = [100, 101, 99, 102, 100, 103, ...]
    rsi = engine.calculate_rsi(prices)
    assert rsi[-1] > 0 and rsi[-1] < 100

def test_no_lookahead_bias():
    # 确认信号在 bar[i] 不使用 bar[i+1] 的数据
    engine = SignalEngine(config)
    for bar_index in range(10, len(historical_data)):
        signal = engine.generate_signal(historical_data, bar_index)
        # 验证信号仅基于 historical_data[:bar_index+1]
        assert not signal.uses_future_data

def test_bar_close_signal_fills_on_next_executable_quote():
    # bar t close 后形成的信号不得以同一根 bar 的 close 回填成交
    trade = backtest.execute_next_quote_fill(signal_from_bar_t)
    assert trade.entry_bar_index == signal_from_bar_t.bar_index + 1

# test_backtest.py
def test_sl_tp_consistency():
    # 验证 SL 和 TP 总是与 entry 价格一致
    backtest = BacktestEngine(config, signals)
    sl, tp = backtest.calculate_sl_tp(1.0850, signal)
    assert sl < 1.0850 < tp

def test_ambiguous_sl_tp_bar_is_conservative():
    # 没有 tick 顺序时，同 bar 同触 SL/TP 必须使用预声明的 SL-first 规则
    assert backtest.resolve_collision(bar_touching_both, policy='sl_first') == 'stop_loss'

def test_trade_pnl_calculation():
    # 验证 PnL 计算的准确性
    trade = backtest.execute_trade(entry_bar, exit_bar, config)
    expected_pnl = (exit_bar['close'] - entry_bar['close']) * size - commission
    assert abs(trade.pnl - expected_pnl) < 0.01

# test_integration.py
def test_full_backtest_no_data_leakage():
    # 完整回测，确认没有前视偏差
    # 运行完整回测，验证结果的合理性
    trades = backtest.run_full_backtest(historical_data, signals)
    assert all(trade.pnl_in_range for trade in trades)
```

---

### 5. analysis/ 中的诊断脚本

**职责**：对回测结果进行统计分析，生成 Stage 3-10 的诊断报告。这些脚本读取 backtest.py 的输出，不修改交易数据。

```python
# event_study.py (Stage 3)
def analyze_events(trades, historical_data):
    # 计算每笔交易的 MFE、MAE、时间等
    for trade in trades:
        mfe = calculate_mfe(trade, historical_data)
        mae = calculate_mae(trade, historical_data)
    output_event_study_report()

# attribution.py (Stage 5)
def attribution_analysis(trades, historical_data):
    # 对比 winners 和 losers，生成特征矩阵
    winners = [t for t in trades if t.pnl > 0]
    losers = [t for t in trades if t.pnl <= 0]
    compare_features(winners, losers)

# environment_validation.py (Stage 9)
def environment_analysis(trades, historical_data):
    # 按 ATR regime、trend 等分层
    # 计算每个 regime 的 Sharpe 和胜率

# temporal_validation.py (Stage 10)
def temporal_analysis(trades, historical_data):
    # 按年/月/滚动窗口分解
    # 计算时间序列的稳定性
```

**关键原则**：
- 这些脚本只**读**回测数据，不**改**
- 每个脚本输出一个独立的诊断报告
- 禁止在诊断脚本中修改策略规则

---

### 6. forward_live/（前向交易）

**职责**：记录 framework_start_time 之后的新信号和交易，保证数据纯度。

```python
# forward_live_runner.py
def forward_live_process():
    # 每日运行（或每小时）：
    # 1. 读取最新市场数据
    # 2. 调用冻结版本的 signal_engine 生成新信号
    # 3. 执行交易
    # 4. 记录到 forward_live_trades.csv
    
    # 完整性检查：
    assert all(signal.timestamp >= FRAMEWORK_START_TIME)
    assert all(trade.entry_time >= FRAMEWORK_START_TIME)
    assert trades consistent with frozen_config
```

**数据文件**：
- `forward_live_signals.csv`：仅包含 framework_start_time 之后的信号
- `forward_live_trades.csv`：仅包含 framework_start_time 之后的交易

---

## 文件职责总结

| 文件 | 职责 | 允许修改时机 |
|------|------|-----------|
| signal_engine.py | 信号生成 | Stage 6（逻辑优化）后新建版本 |
| backtest.py | 交易执行 | Stage 2（审计）后不再修改 |
| config.yaml | 参数配置 | Stage 7（参数优化）后新建版本 |
| tests/ | 单元测试 | 随时添加更多测试 |
| analysis/*.py | 诊断脚本 | 不修改交易数据，只分析 |
| forward_live/ | 前向交易 | 只追加，不修改历史 |

---

## 关键不允许

1. **不允许多个脚本各自实现一套信号逻辑**：所有信号定义必须在 signal_engine.py 中集中实现。

2. **不允许在同一个脚本中混合信号、执行、分析**：职责分离是防止过拟合的前提。

3. **不允许在 forward-live 阶段修改冻结的 signal_engine.py**：前向数据必须基于冻结的代码。

4. **不允许在诊断脚本中修改交易**：分析是只读操作。

5. **不允许用参数和逻辑绕过结构化的代码流**：所有参数必须通过 config.yaml，所有规则必须通过明确的方法。

---

## 代码示例：最小化可行策略

```python
# signal_engine.py - Stage 1-3
class SignalEngine:
    def generate_signal(self, bars_data, bar_index):
        # 仅生成信号，不涉及交易
        rsi = self.calculate_rsi(bars_data['close'][:bar_index+1])
        if rsi[-1] < 30:
            return {'type': 'LONG', 'strength': 30 - rsi[-1]}
        return None

# backtest.py - Stage 4
class BacktestEngine:
    def run_full_backtest(self, bars_data, signals):
        trades = []
        for bar_index, bar in enumerate(bars_data):
            signal = signals[bar_index]
            if signal and bar_index + 1 < len(bars_data):  # bar-close 信号
                trade = self.open_trade_at_next_executable_quote(bars_data[bar_index + 1], signal)
                trades.append(trade)
            # 检查出场条件...
        return trades

# analysis/attribution.py - Stage 5
def analyze_attribution(trades):
    winners = [t for t in trades if t.pnl > 0]
    losers = [t for t in trades if t.pnl <= 0]
    
    avg_atr_winners = mean([t.atr_entry for t in winners])
    avg_atr_losers = mean([t.atr_entry for t in losers])
    
    print(f"Winners avg ATR: {avg_atr_winners}")
    print(f"Losers avg ATR: {avg_atr_losers}")
    # 发现低 ATR 胜率低 → 提出 ATR filter 候选
```

这样的结构确保了可审计性、可测试性、和可重复性。
