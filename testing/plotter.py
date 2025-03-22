import matplotlib.pyplot as plt
import numpy as np

class PricePlotter:
    def __init__(self, trading_engine):
        self.trading_engine = trading_engine
        self.initial_data_size = len(trading_engine.price_data)
        
        # Initialize figure with three subplots (removed confidence subplot)
        plt.ion()
        self.fig = plt.figure(figsize=(12, 10))  # Adjusted height
        
        # Main price plot (larger)
        self.ax_price = self.fig.add_subplot(311)
        # RSI subplot
        self.ax_rsi = self.fig.add_subplot(312, sharex=self.ax_price)
        # EMA subplot
        self.ax_ema = self.fig.add_subplot(313, sharex=self.ax_price)
        
        # Adjust subplot positions
        self.fig.subplots_adjust(hspace=0.6)
        self.ax_price.set_position([0.1, 0.65, 0.8, 0.3])  # Top: Price, height 0.3
        self.ax_rsi.set_position([0.1, 0.40, 0.8, 0.2])    # Middle: RSI, height 0.2
        self.ax_ema.set_position([0.1, 0.10, 0.8, 0.2])    # Bottom: EMA, height 0.2
        
        # Backtesting indices
        self.targets_index = None
        self.similars_index = None
        self.plot_backtest = False

    def plot_live(self):
        """Plot price action and indicators in real-time"""
        self._clear_axes()
        metrics = self.trading_engine.metric_collector.metrics
        time = list(range(len(metrics)))
        
        self._plot_price(time, metrics, include_backtest=False)
        self._plot_rsi(time, metrics)
        self._plot_ema(time, metrics)
        
        self._customize_plots('Simulated Price Environment')
        plt.draw()
        plt.pause(0.001)

    def plot_static(self, start_position=0, end_position=None):
        """Plot complete price action and indicators with specified range"""
        plt.ioff()
        self._clear_axes()
        
        metrics = self.trading_engine.metric_collector.metrics
        end_position = end_position if end_position is not None else len(metrics)
        time = list(range(start_position, end_position))
        metrics = metrics[start_position:end_position]
        
        include_backtest = self.plot_backtest and (self.targets_index is not None or self.similars_index is not None)
        self._plot_price(time, metrics, include_backtest=include_backtest)
        self._plot_rsi(time, metrics)
        self._plot_ema(time, metrics)
        
        self._customize_plots('Complete Solana Token Price Action')
        plt.show()

    def add_backtesting_points(self, targets_index, similars_index):
        """Store backtesting indices that match self.trading_engine.metric_collector.metrics and enable plotting."""
        max_idx = len(self.trading_engine.metric_collector.metrics) - 1
        self.targets_index = [i for i in targets_index if 0 <= i <= max_idx]
        self.similars_index = [i for i in similars_index if 0 <= i <= max_idx]
        self.plot_backtest = True

    def _clear_axes(self):
        """Clear all axes for fresh plotting"""
        self.ax_price.clear()
        self.ax_rsi.clear()
        self.ax_ema.clear()

    def _plot_price(self, time, metrics, include_backtest=False):
        """Plot price data with support/resistance zones, confidence underlay, and optional backtesting points"""
        prices = [m['price'] for m in metrics]
        
        # Plot initial and live data
        if self.initial_data_size > 0:
            end_initial = min(self.initial_data_size, len(metrics))
            self.ax_price.plot(
                time[:end_initial], prices[:end_initial], 'o-', color='grey',
                label='Initial Data', zorder=2
            )
        
        if len(metrics) > self.initial_data_size:
            start_live = max(0, self.initial_data_size - (len(self.trading_engine.metric_collector.metrics) - len(metrics)))
            self.ax_price.plot(
                time[start_live:], prices[start_live:], 'o-', color='blue',
                label='Live Data', zorder=2
            )
        
        # Plot zones
        self._plot_zones(metrics[-1])
        
        # Underlay zone confidence
        confidences = [m.get('zone_confidence', 0) for m in metrics]  # Default to 0 if missing
        if confidences:
            # Get y-axis limits from price data to scale confidence
            price_min, price_max = min(prices), max(prices)
            if price_max == price_min:  # Avoid division by zero
                price_max = price_min + 1
            # Scale confidence from 0 (price_min) to 1 (price_max)
            scaled_confidences = [price_min + (price_max - price_min) * c for c in confidences]
            self.ax_price.fill_between(
                time, price_min, scaled_confidences,
                color='green', alpha=0.2, zorder=1, label='Zone Confidence'
            )
        
        # Plot backtesting points if applicable
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
        """Plot support and resistance zones from metrics."""
        current_price = metric['price']
        
        key_zone_1 = self.trading_engine.metric_collector.key_zone_1
        key_zone_2 = self.trading_engine.metric_collector.key_zone_2
        key_zone_3 = self.trading_engine.metric_collector.key_zone_3
        key_zone_4 = self.trading_engine.metric_collector.key_zone_4
        key_zone_5 = self.trading_engine.metric_collector.key_zone_5
        key_zone_6 = self.trading_engine.metric_collector.key_zone_6

        def plot_zone(zone_data, color, label):
            if not zone_data or 'level' not in zone_data:
                return
            level = zone_data['level']
            strength = zone_data.get('strength', 1)
            self.ax_price.axhline(
                y=level,
                color=color,
                linestyle='--',
                label=label
            )

        plot_zone(key_zone_1, 'green', 'key_zone_1')
        plot_zone(key_zone_2, 'red', 'key_zone_2')
        plot_zone(key_zone_3, 'purple', 'key_zone_3')
        plot_zone(key_zone_4, 'yellow', 'key LICzone_4')
        plot_zone(key_zone_5, 'brown', 'key_zone_5')
        plot_zone(key_zone_6, 'pink', 'key_zone_6')

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
        
        self.ax_ema.set_xlabel('Time (index)')
        self.ax_ema.set_ylabel('EMA')
        self.ax_ema.legend()
        self.ax_ema.grid(True, linestyle='--', alpha=0.7)