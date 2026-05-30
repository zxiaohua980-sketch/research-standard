# 模板：signal_engine.py
# 复制并修改为你的策略

import numpy as np
import pandas as pd


class SignalEngine:
    """
    信号生成引擎 - 只负责生成信号，不涉及交易执行

    使用原则：
    1. 只生成信号，不涉及风险管理（SL/TP）
    2. 不使用未来数据
    3. 必须是纯函数（相同输入 → 相同输出）
    """

    def __init__(self, config):
        """
        初始化信号引擎

        Args:
            config (dict): 配置参数，来自 config.yaml
        """
        self.signal_type = config.get('type')
        self.rsi_period = config.get('rsi_period', 14)
        self.rsi_threshold = config.get('threshold', 30)
        self.atr_threshold = config.get('atr_threshold', 0.8)

    def calculate_rsi(self, prices, period=14):
        """
        计算 RSI 指标

        Args:
            prices: 收盘价数组
            period: 周期（默认 14）

        Returns:
            RSI 数组（0-100）
        """
        if len(prices) < period + 1:
            return np.full(len(prices), np.nan)

        deltas = np.diff(prices)
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period

        rsi = np.full(len(prices), np.nan)
        rsi[period] = 100 - 100 / (1 + up / down) if down != 0 else 50

        for i in range(period + 1, len(prices)):
            delta = deltas[i - 1]
            if delta > 0:
                up = (up * (period - 1) + delta) / period
                down = down * (period - 1) / period
            else:
                up = up * (period - 1) / period
                down = (down * (period - 1) - delta) / period

            rsi[i] = 100 - 100 / (1 + up / down) if down != 0 else 50

        return rsi

    def calculate_atr(self, high, low, close, period=14):
        """
        计算 ATR（平均真实波幅）

        Args:
            high: 最高价数组
            low: 最低价数组
            close: 收盘价数组
            period: 周期（默认 14）

        Returns:
            ATR 数组
        """
        tr = np.maximum(
            high - low,
            np.maximum(
                np.abs(high - np.roll(close, 1)),
                np.abs(low - np.roll(close, 1))
            )
        )

        atr = pd.Series(tr).rolling(window=period).mean().values
        return atr

    def generate_signal(self, bars_data, bar_index):
        """
        生成单个信号

        关键：在 bar_index 处，不能使用 bar_index+1 的数据

        Args:
            bars_data (DataFrame): 历史 OHLC 数据（至 bar_index 为止）
            bar_index (int): 当前 bar 的索引

        Returns:
            dict or None: 如果有信号，返回 {'type': 'LONG' or 'SHORT', 'strength': float}
                         否则返回 None
        """
        # 安全检查：确保有足够的历史数据
        if bar_index < self.rsi_period:
            return None

        # 获取至当前 bar 为止的历史数据（不包含未来）
        history = bars_data.iloc[:bar_index + 1]

        # 计算指标（基于历史数据）
        rsi = self.calculate_rsi(history['close'].values, self.rsi_period)
        atr = self.calculate_atr(
            history['high'].values,
            history['low'].values,
            history['close'].values
        )

        # 获取当前 bar 的指标值
        current_rsi = rsi[bar_index]
        current_atr = atr[bar_index]

        # 检查 NaN
        if np.isnan(current_rsi) or np.isnan(current_atr):
            return None

        # 信号逻辑：RSI < 30 且 ATR > threshold
        if current_rsi < self.rsi_threshold and current_atr > self.atr_threshold:
            return {
                'type': 'LONG',
                'strength': self.rsi_threshold - current_rsi,  # 越低越强
                'bar_index': bar_index,
                'rsi': current_rsi,
                'atr': current_atr
            }

        return None

    def backtest_generate_signals(self, bars_data):
        """
        为整个历史数据集生成所有信号

        Args:
            bars_data (DataFrame): 完整的 OHLC 数据

        Returns:
            list: 信号列表，每个元素对应一个 bar
        """
        signals = []

        for bar_index in range(len(bars_data)):
            signal = self.generate_signal(bars_data, bar_index)
            signals.append(signal)

        return signals


# 使用示例
if __name__ == '__main__':
    # 从 config.yaml 加载配置
    config = {
        'type': 'RSI',
        'rsi_period': 14,
        'threshold': 30,
        'atr_threshold': 0.8
    }

    # 初始化
    engine = SignalEngine(config)

    # 示例数据（实际使用时应从 CSV 或数据库读取）
    sample_data = {
        'close': [100, 101, 99, 102, 100, 103] * 5,  # 简化示例
        'high': [101, 102, 100, 103, 101, 104] * 5,
        'low': [99, 100, 98, 101, 99, 102] * 5
    }

    df = pd.DataFrame(sample_data)

    # 生成信号
    signals = engine.backtest_generate_signals(df)

    # 统计
    signal_count = sum(1 for s in signals if s is not None)
    print(f"Total signals: {signal_count}")
