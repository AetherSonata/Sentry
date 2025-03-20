import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

class PricePlotter:
    def __init__(self, trading_engine):
        self.trading_engine = trading_engine
        self.initial_data_size = len(trading_engine.metrics)
        
        # Initialize figure with four subplots
        plt.ion()
        self.fig = plt.figure(figsize=(12, 12))  # Increased height for extra subplot
        
        # Main price plot (larger)
        self.ax_price = self.fig.add_subplot(411)
        # RSI subplot
        self.ax_rsi = self.fig.add_subplot(412, sharex=self.ax_price)
        # Zone confidence subplot
        self.ax_confidence = self.fig.add_subplot(413, sharex=self.ax_price)
        # EMA subplot
        self.ax_ema = self.fig.add_subplot(414, sharex=self.ax_price)
        
        # Adjust subplot positions
        self.fig.subplots_adjust(hspace=0.6)
        self.ax_price.set_position([0.1, 0.65, 0.8, 0.3])    # Top: Price, height 0.3
        self.ax_rsi.set_position([0.1, 0.45, 0.8, 0.15])     # Second: RSI, height 0.15
        self.ax_ema.set_position([0.1, 0.25, 0.8, 0.15])     # Third: EMA, height 0.15
        self.ax_confidence.set_position([0.1, 0.05, 0.8, 0.1])  # Bottom: Confidence, height 0.1
        
        # Backtesting indices
        self.targets_index = None
        self.similars_index = None
        self.plot_backtest = False

    def plot_live(self):
        """Plot price action and indicators in real-time"""
        self._clear_axes()
        metrics = self.trading_engine.metrics
        time = list(range(len(metrics)))
        
        self._plot_price(time, metrics, include_backtest=False)
        self._plot_rsi(time, metrics)
        self._plot_zone_confidence(time, metrics)
        self._plot_ema(time, metrics)
        self.plot_all_zones()  # Add all zones from metrics_collector
        
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
        
        include_backtest = self.plot_backtest and (self.targets_index is not None or self.similars_index is not None)
        self._plot_price(time, metrics, include_backtest=include_backtest)
        self._plot_rsi(time, metrics)
        self._plot_zone_confidence(time, metrics)
        self._plot_ema(time, metrics)
        self.plot_all_zones()  # Add all zones from metrics_collector
        
        self._customize_plots('Complete Solana Token Price Action')
        plt.show()

    def add_backtesting_points(self, targets_index, similars_index):
        """Store backtesting indices that match self.trading_engine.metrics and enable plotting."""
        max_idx = len(self.trading_engine.metrics) - 1
        self.targets_index = [i for i in targets_index if 0 <= i <= max_idx]
        self.similars_index = [i for i in similars_index if 0 <= i <= max_idx]
        self.plot_backtest = True

    def _clear_axes(self):
        """Clear all axes for fresh plotting"""
        self.ax_price.clear()
        self.ax_rsi.clear()
        self.ax_confidence.clear()
        self.ax_ema.clear()

    def _plot_price(self, time, metrics, include_backtest=False):
        """Plot price data with support/resistance zones and optional backtesting points"""
        prices = [m['price'] for m in metrics]
        
        if self.initial_data_size > 0:
            end_initial = min(self.initial_data_size, len(metrics))
            self.ax_price.plot(
                time[:end_initial], prices[:end_initial], 'o-', color='grey',
                label='Initial Data', zorder=1
            )
        
        if len(metrics) > self.initial_data_size:
            start_live = max(0, self.initial_data_size - (len(self.trading_engine.metrics) - len(metrics)))
            self.ax_price.plot(
                time[start_live:], prices[start_live:], 'o-', color='blue',
                label='Live Data', zorder=1
            )
        
        self._plot_zones(metrics[-1])  # Existing zone logic
        
        if include_backtest:
            if self.targets_index:
                target_times = [time[i] for i in self.targets_index if i < len(time)]
                target_prices = [prices[i] for i in self.targets_index if i < len(time)]
                self.ax_price.scatter(
                    target_times, target_prices, color='green', alpha=0.8, label='Targets', s=50, zorder=3
                )
            if self.similars_index:
                similar_times = [time[i] for i in self.similars_index if i < len(time)]
                similar_prices = [prices[i] for i in self.similars_index if i < len(time)]
                self.ax_price.scatter(
                    similar_times, similar_prices, color='purple', alpha=0.8, label='Similars', s=50, zorder=3
                )

    def _plot_rsi(self, time, metrics):
        """Plot RSI values and RSI slope"""
        rsi_short = [m['rsi']['short'] for m in metrics]
        rsi_mid = [m['rsi']['middle_short'] for m in metrics]
        rsi_long = [m['rsi']['long'] for m in metrics]
        rsi_slope = [m['rsi']['slope'] for m in metrics]
        
        self.ax_rsi.plot(time, rsi_short, '-', color='blue', label='RSI Short')
        self.ax_rsi.plot(time, rsi_mid, '-', color='orange', label='RSI Mid-Short')
        self.ax_rsi.plot(time, rsi_long, '-', color='purple', label='RSI Long')
        self.ax_rsi.plot(time, rsi_slope, '-', color='black', alpha=0.3, label='RSI Slope')
        
        self.ax_rsi.axhline(y=70, color='r', linestyle='--', alpha=0.3)
        self.ax_rsi.axhline(y=30, color='g', linestyle='--', alpha=0.3)

    def _plot_zone_confidence(self, time, metrics):
        """Plot zone_confidence values with fill between 0 and the line"""
        confidences = [m['zone_confidence'] for m in metrics]
        
        self.ax_confidence.plot(
            time, confidences, '-', color='yellow', label='Zone Confidence', 
            linewidth=2, zorder=2
        )
        
        zero_line = np.zeros(len(time))
        self.ax_confidence.fill_between(
            time, zero_line, confidences, where=(np.array(confidences) >= 0),
            facecolor='green', alpha=0.3, interpolate=True, zorder=1
        )
        self.ax_confidence.fill_between(
            time, zero_line, confidences, where=(np.array(confidences) < 0),
            facecolor='red', alpha=0.3, interpolate=True, zorder=1
        )
        
        self.ax_confidence.axhline(y=0, color='black', linestyle='--', alpha=0.3)
        
        if len(confidences) > 0:
            current_confidence = confidences[-1]
            self.ax_confidence.text(
                0.95, 0.95, f'Confidence: {current_confidence:.2f}',
                transform=self.ax_confidence.transAxes,
                ha='right', va='top', fontsize=10, color='white',
                bbox=dict(facecolor='black', alpha=0.5)
            )

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

    def _plot_zones(self, metric):
        """Plot support, resistance, and major zones from metrics"""
        current_price = metric['price']
        
        # Plot regular support and resistance zones (existing logic, dashed lines)
        for i in range(1, 4):
            dist = metric.get(f'support_level_{i}_dist', 0)
            strength = metric.get(f'support_level_{i}_strength', 0)
            if strength > 0:
                level = current_price + (dist / 100) * current_price
                self.ax_price.axhline(
                    y=level, 
                    color='green', 
                    linestyle='--',  # Dashed line
                    alpha=strength * 0.8,
                    label=f'Support {i}' if i == 1 else None
                )
            
            dist = metric.get(f'resistance_level_{i}_dist', 0)
            strength = metric.get(f'resistance_level_{i}_strength', 0)
            if strength > 0:
                level = current_price + (dist / 100) * current_price
                self.ax_price.axhline(
                    y=level, 
                    color='red', 
                    linestyle='--',  # Dashed line
                    alpha=strength * 0.8,
                    label=f'Resistance {i}' if i == 1 else None
                )

        # Plot major support zone (continuous green line)
        major_support_dist = metric.get('major_support_level_1_dist', 0)
        major_support_strength = metric.get('major_support_level_1_strength', 0)
        print(major_support_dist, major_support_strength)
        if major_support_strength > 0:
            major_support_level = current_price + (major_support_dist / 100) * current_price
            self.ax_price.axhline(
                y=major_support_level,
                color='green',
                linestyle='-',  # Continuous line
                alpha=major_support_strength * 0.8,
                label='Major Support'
            )

        # Plot major resistance zone (continuous red line)
        major_resistance_dist = metric.get('major_resistance_level_1_dist', 0)
        major_resistance_strength = metric.get('major_resistance_level_1_strength', 0)
        print(major_resistance_dist, major_resistance_strength)
        if major_resistance_strength > 0:
            major_resistance_level = current_price + (major_resistance_dist / 100) * current_price
            self.ax_price.axhline(
                y=major_resistance_level,
                color='red',
                linestyle='-',  # Continuous line
                alpha=major_resistance_strength * 0.8,
                label='Major Resistance'
            )

    def plot_all_zones(self):
        """Plot all zones from metrics_collector.zones[] as thin dashed black lines"""
        if hasattr(self.trading_engine, 'metric_collector') and hasattr(self.trading_engine.metric_collector, 'zones'):
            for zone in self.trading_engine.metric_collector.zones:
                level = zone.get('zone_level', 0)
                strength = zone.get('strength', 0)
                if level > 0 and strength > 0:
                    # Alpha ranges from 0.1 to 0.5 based on strength (assuming strength is 0-1)
                    alpha = max(0.1, min(0.5, strength * 0.5))
                    self.ax_price.axhline(
                        y=level, 
                        color='black', 
                        linestyle=':',  # Dashed line
                        linewidth=0.8,  # Thin line
                        alpha=alpha, 
                        label='Collected Zone' if self.trading_engine.metric_collector.zones.index(zone) == 0 else None
                    )

    def _customize_plots(self, title):
        """Apply common styling to all plots"""
        self.ax_price.set_ylabel('Price')
        self.ax_price.set_title(title)
        self.ax_price.legend()
        self.ax_price.grid(True, linestyle='--', alpha=0.7)
        
        self.ax_rsi.set_ylabel('RSI')
        self.ax_rsi.legend()
        self.ax_rsi.grid(True, linestyle='--', alpha=0.7)
        self.ax_rsi.set_ylim(0, 100)
        
        self.ax_confidence.set_ylabel('Confidence')
        self.ax_confidence.legend()
        self.ax_confidence.grid(True, linestyle='--', alpha=0.7)
        
        self.ax_ema.set_xlabel('Time (index)')
        self.ax_ema.set_ylabel('EMA')
        self.ax_ema.legend()
        self.ax_ema.grid(True, linestyle='--', alpha=0.7)