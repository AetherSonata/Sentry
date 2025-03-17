import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

class PricePlotter:
    def __init__(self, trading_engine):
        self.trading_engine = trading_engine
        self.initial_data_size = len(trading_engine.metrics)
        
        # Initialize figure with four subplots (backtesting subplot added)
        plt.ion()
        self.fig = plt.figure(figsize=(12, 9))  # Increased height slightly to fit new subplot
        
        # Main price plot (larger)
        self.ax_price = self.fig.add_subplot(411)  # 4 rows, 1 column, position 1
        # RSI subplot (smaller)
        self.ax_rsi = self.fig.add_subplot(412, sharex=self.ax_price)
        # EMA subplot (smaller)
        self.ax_ema = self.fig.add_subplot(413, sharex=self.ax_price)
        # Backtesting subplot (very slim, initially hidden)
        self.ax_backtest = self.fig.add_subplot(414, sharex=self.ax_price)
        self.ax_backtest.set_visible(False)  # Hidden until data is added
        
        # Adjust subplot sizes
        self.fig.subplots_adjust(hspace=0.5)
        self.ax_price.set_position([0.1, 0.55, 0.8, 0.4])  # [left, bottom, width, height]
        self.ax_rsi.set_position([0.1, 0.35, 0.8, 0.15])
        self.ax_ema.set_position([0.1, 0.2, 0.8, 0.15])
        self.ax_backtest.set_position([0.1, 0.1, 0.8, 0.05])  # Very slim
        
        # Backtesting data
        self.backtest_metrics = None
        self.targets_index = None
        self.similars_index = None

    def plot_live(self):
        """Plot price action and indicators in real-time"""
        self._clear_axes()
        metrics = self.trading_engine.metrics
        time = list(range(len(metrics)))
        
        self._plot_price(time, metrics)
        self._plot_rsi(time, metrics)
        self._plot_ema(time, metrics)
        
        self._customize_plots('Live Solana Token Price Action')
        plt.draw()
        plt.pause(0.001)

    def plot_static(self, start_position=0, end_position=None):
        """Plot complete price action and indicators with specified range"""
        plt.ioff()
        self._clear_axes()
        
        metrics = self.trading_engine.metrics
        end_position = end_position if end_position is not None else len(metrics)
        time = list(range(start_position, end_position))
        metrics = metrics[start_position:end_position]
        
        self._plot_price(time, metrics)
        self._plot_rsi(time, metrics)
        self._plot_ema(time, metrics)
        
        # Plot backtesting subplot if data exists
        if self.backtest_metrics is not None:
            self.ax_backtest.set_visible(True)
            self._plot_backtesting(time)
        
        self._customize_plots('Complete Solana Token Price Action')
        plt.show()

    def add_backtesting_points(self, metrics, targets_index, similars_index):
        """Add backtesting data to be plotted in the static subplot.

        Args:
            metrics (list): List of metric dictionaries to plot.
            targets_index (list): List of indices for green target points.
            similars_index (list): List of indices for purple similar points.
        """
        self.backtest_metrics = metrics
        self.targets_index = targets_index
        self.similars_index = similars_index

    def _clear_axes(self):
        """Clear all axes for fresh plotting"""
        self.ax_price.clear()
        self.ax_rsi.clear()
        self.ax_ema.clear()
        if self.backtest_metrics is not None:
            self.ax_backtest.clear()

    def _plot_price(self, time, metrics):
        """Plot price data with support/resistance zones"""
        prices = [m['price'] for m in metrics]
        
        # Initial data in grey
        if self.initial_data_size > 0:
            end_initial = min(self.initial_data_size, len(metrics))
            self.ax_price.plot(
                time[:end_initial],
                prices[:end_initial],
                'o-',
                color='grey',
                label='Initial Data'
            )
        
        # Live data in blue
        if len(metrics) > self.initial_data_size:
            start_live = max(0, self.initial_data_size - (len(self.trading_engine.metrics) - len(metrics)))
            self.ax_price.plot(
                time[start_live:],
                prices[start_live:],
                'o-',
                color='blue',
                label='Live Data'
            )
        
        self._plot_zones(metrics[-1])

    def _plot_rsi(self, time, metrics):
        """Plot RSI values"""
        rsi_short = [m['rsi']['short'] for m in metrics]
        rsi_mid = [m['rsi']['middle_short'] for m in metrics]
        rsi_long = [m['rsi']['long'] for m in metrics]
        
        self.ax_rsi.plot(time, rsi_short, '-', color='blue', label='RSI Short')
        self.ax_rsi.plot(time, rsi_mid, '-', color='orange', label='RSI Mid-Short')
        self.ax_rsi.plot(time, rsi_long, '-', color='purple', label='RSI Long')
        
        self.ax_rsi.axhline(y=70, color='r', linestyle='--', alpha=0.3)
        self.ax_rsi.axhline(y=30, color='g', linestyle='--', alpha=0.3)

    def _plot_ema(self, time, metrics):
        """Plot EMA values"""
        ema_short = [m['ema']['short'] for m in metrics]
        ema_medium = [m['ema']['medium'] for m in metrics]
        ema_long = [m['ema']['long'] for m in metrics]
        ema_longterm = [m['ema']['longterm'] for m in metrics]
        
        self.ax_ema.plot(time, ema_short, '-', color='blue', label='EMA Short')
        self.ax_ema.plot(time, ema_medium, '-', color='orange', label='EMA Medium')
        self.ax_ema.plot(time, ema_long, '-', color='purple', label='EMA Long')
        self.ax_ema.plot(time, ema_longterm, '-', color='green', label='EMA Long-term')

    def _plot_backtesting(self, time):
        """Plot backtesting points in the slim subplot"""
        prices = [m['price'] for m in self.backtest_metrics]
        
        # Plot all points in grey with low alpha
        self.ax_backtest.scatter(time, prices, color='grey', alpha=0.1, label='All Points', s=20)
        
        # Plot target points in green
        if self.targets_index:
            target_times = [time[i] for i in self.targets_index if i < len(time)]
            target_prices = [prices[i] for i in self.targets_index if i < len(time)]
            self.ax_backtest.scatter(target_times, target_prices, color='green', alpha=0.8, label='Targets', s=30)
        
        # Plot similar points in purple
        if self.similars_index:
            similar_times = [time[i] for i in self.similars_index if i < len(time)]
            similar_prices = [prices[i] for i in self.similars_index if i < len(time)]
            self.ax_backtest.scatter(similar_times, similar_prices, color='purple', alpha=0.8, label='Similars', s=30)
        
        self.ax_backtest.set_ylabel('Backtest')
        self.ax_backtest.legend()
        self.ax_backtest.grid(True, linestyle='--', alpha=0.7)

    def _plot_zones(self, metric):
        """Plot support and resistance zones"""
        current_price = metric['price']
        
        for i in range(1, 4):
            # Support levels
            dist = metric[f'support_level_{i}_dist']
            strength = metric[f'support_level_{i}_strength']
            if strength > 0:
                level = current_price + (dist / 100) * current_price
                self.ax_price.axhline(
                    y=level, color='green', linestyle='--', 
                    alpha=strength * 0.8, label=f'Support {i}' if i == 1 else None
                )
            
            # Resistance levels
            dist = metric[f'resistance_level_{i}_dist']
            strength = metric[f'resistance_level_{i}_strength']
            if strength > 0:
                level = current_price + (dist / 100) * current_price
                self.ax_price.axhline(
                    y=level, color='red', linestyle='--', 
                    alpha=strength * 0.8, label=f'Resistance {i}' if i == 1 else None
                )

    def _customize_plots(self, title):
        """Apply common styling to all plots"""
        # Price plot
        self.ax_price.set_ylabel('Price')
        self.ax_price.set_title(title)
        self.ax_price.legend()
        self.ax_price.grid(True, linestyle='--', alpha=0.7)
        
        # RSI plot
        self.ax_rsi.set_ylabel('RSI')
        self.ax_rsi.legend()
        self.ax_rsi.grid(True, linestyle='--', alpha=0.7)
        self.ax_rsi.set_ylim(0, 100)
        
        # EMA plot
        self.ax_ema.set_xlabel('Time (index)')
        self.ax_ema.set_ylabel('EMA')
        self.ax_ema.legend()
        self.ax_ema.grid(True, linestyle='--', alpha=0.7)