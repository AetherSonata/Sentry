import matplotlib.pyplot as plt
import numpy as np

class PricePlotter:
    def __init__(self, trading_engine):
        self.trading_engine = trading_engine
        self.initial_data_size = len(trading_engine.price_data)
        
        # Initialize figure with five subplots
        plt.ion()
        self.fig = plt.figure(figsize=(12, 15))
        
        # Main price plot (larger)
        self.ax_price = self.fig.add_subplot(511)
        # RSI subplot (slim)
        self.ax_rsi = self.fig.add_subplot(512, sharex=self.ax_price)
        # Combined plot (larger)
        self.ax_combined = self.fig.add_subplot(513, sharex=self.ax_price)
        # MACD subplot (slim, same size as RSI)
        self.ax_macd = self.fig.add_subplot(514, sharex=self.ax_price)
        # New Fibonacci levels subplot (slim, below MACD)
        self.ax_fib = self.fig.add_subplot(515, sharex=self.ax_price)
        
        # Adjust subplot positions
        self.fig.subplots_adjust(hspace=0.3)
        self.ax_price.set_position([0.1, 0.75, 0.8, 0.2])     # Price: height 0.2 (larger)
        self.ax_rsi.set_position([0.1, 0.66, 0.8, 0.08])      # RSI: height 0.08 (slim)
        self.ax_combined.set_position([0.1, 0.44, 0.8, 0.2])  # Combined: height 0.2 (larger)
        self.ax_macd.set_position([0.1, 0.35, 0.8, 0.08])     # MACD: height 0.08 (slim, matches RSI)
        self.ax_fib.set_position([0.1, 0.15, 0.8, 0.2])      # Fibonacci: height 0.08 (slim, below MACD)
        
        # Backtesting indices (if applicable)
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
        self._plot_combined(time, metrics, include_backtest=False)
        self._plot_macd(time, metrics)
        self._plot_fibonacci_levels(time, metrics, start_position=0)
        
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
        self._plot_combined(time, metrics, include_backtest=include_backtest)
        self._plot_macd(time, metrics)
        self._plot_fibonacci_levels(time, metrics, start_position=start_position)
        
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
        self.ax_combined.clear()
        self.ax_macd.clear()
        self.ax_fib.clear()

    def _plot_price(self, time, metrics, include_backtest=False):
        """Plot price data with support/resistance zones, confidence underlay, and optional backtesting points"""
        prices = [m['price'] for m in metrics]
        
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
        
        self._plot_zones(metrics[-1])
        
        confidences = [m.get('zone_confidence', 0) for m in metrics]
        if confidences:
            price_min, price_max = min(prices), max(prices)
            if price_max == price_min:
                price_max = price_min + 1
            scaled_confidences = [price_min + (price_max - price_min) * c for c in confidences]
            self.ax_price.fill_between(
                time, price_min, scaled_confidences,
                color='green', alpha=0.2, zorder=1, label='Zone Confidence'
            )
        
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
        """Plot RSI values and RSI slope - unchanged functionality"""
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

    def _plot_combined(self, time, metrics, include_backtest=False):
        """Plot combined price action with EMA values, Bollinger Bands, SMAs, and crossovers"""
        prices = [m['price'] for m in metrics]
        
        # Plot RSI divergence crossovers first (background, lowest zorder)
        divergence_strengths = [m['divergence'] for m in metrics]
        price_min, price_max = min(prices), max(prices)
        if price_max == price_min:
            price_max = price_min + 1
        
        for i in range(1, len(time)):
            if divergence_strengths[i] > 0:  # Bullish
                self.ax_combined.axvspan(
                    time[i-1], time[i], 
                    ymin=0, ymax=1,
                    color='green', 
                    alpha=min(0.05, divergence_strengths[i]),
                    zorder=1  # Background
                )
            elif divergence_strengths[i] < 0:  # Bearish
                self.ax_combined.axvspan(
                    time[i-1], time[i], 
                    ymin=0, ymax=1,
                    color='red', 
                    alpha=min(0.05, abs(divergence_strengths[i])),
                    zorder=1  # Background
                )
        
        # Calculate and plot EMA prices (middle layer)
        ema_short = []
        ema_medium = []
        ema_long = []
        ema_longterm = []
        
        for i, m in enumerate(metrics):
            ema = m.get('ema', {})  # Safely get ema dict, default to empty dict
            price = prices[i]
            ema_short.append((ema.get('short', 0) or 0) * price)
            ema_medium.append((ema.get('medium', 0) or 0) * price)
            ema_long.append((ema.get('long', 0) or 0) * price)
            ema_longterm.append((ema.get('longterm', 0) or 0) * price)
        
        self.ax_combined.plot(time, ema_short, '-', color='blue', label='EMA Short', alpha=0.8, zorder=2)
        self.ax_combined.plot(time, ema_medium, '-', color='orange', label='EMA Medium', alpha=0.8, zorder=2)
        self.ax_combined.plot(time, ema_long, '-', color='purple', label='EMA Long', alpha=0.8, zorder=2)
        self.ax_combined.plot(time, ema_longterm, '-', color='green', label='EMA Long-term', alpha=0.8, zorder=2)
        
        # Plot Bollinger Bands
        upper_bands = [m['boilinger_bands']['upper'] for m in metrics]
        middle_bands = [m['boilinger_bands']['middle'] for m in metrics]
        lower_bands = [m['boilinger_bands']['lower'] for m in metrics]
        
        self.ax_combined.plot(time, upper_bands, '--', color='red', label='BB Upper', alpha=0.8, zorder=2)
        self.ax_combined.plot(time, middle_bands, '-', color='black', label='BB Middle (SMA)', alpha=0.8, zorder=2)
        self.ax_combined.plot(time, lower_bands, '--', color='green', label='BB Lower', alpha=0.8, zorder=2)
        
        # Plot additional SMAs
        sma_short = [m['sma']['short'] for m in metrics]
        sma_medium = [m['sma']['medium'] for m in metrics]
        sma_long = [m['sma']['long'] for m in metrics]
        
        self.ax_combined.plot(time, sma_short, '-', color='cyan', label='SMA Short', alpha=0.5, zorder=2)
        self.ax_combined.plot(time, sma_medium, '-', color='magenta', label='SMA Medium', alpha=0.5, zorder=2)
        self.ax_combined.plot(time, sma_long, '-', color='yellow', label='SMA Long', alpha=0.5, zorder=2)
        
        # Plot price action last (foreground, highest zorder)
        if self.initial_data_size > 0:
            end_initial = min(self.initial_data_size, len(metrics))
            self.ax_combined.plot(
                time[:end_initial], prices[:end_initial], 'o-', color='grey',
                label='Initial Price', zorder=3  # Increased to 3 to be on top
            )
        
        if len(metrics) > self.initial_data_size:
            start_live = max(0, self.initial_data_size - (len(self.trading_engine.metric_collector.metrics) - len(metrics)))
            self.ax_combined.plot(
                time[start_live:], prices[start_live:], 'o-', color='black',
                label='Live Price', zorder=3  # Increased to 3 to be on top
            )
        
        # Set y-axis limits based on price range, with some padding
        padding = (price_max - price_min) * 0.1  # 10% padding
        self.ax_combined.set_ylim(price_min - padding, price_max + padding)

    def _plot_zones(self, metric):
        """Plot support and resistance zones from metrics"""
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
            self.ax_price.axhline(
                y=level,
                color=color,
                linestyle='--',
                label=label
            )

        plot_zone(key_zone_1, 'green', 'key_zone_1')
        plot_zone(key_zone_2, 'red', 'key_zone_2')
        plot_zone(key_zone_3, 'purple', 'key_zone_3')
        plot_zone(key_zone_4, 'yellow', 'key_zone_4')
        plot_zone(key_zone_5, 'brown', 'key_zone_5')
        plot_zone(key_zone_6, 'pink', 'key_zone_6')

    def _plot_macd(self, time, metrics):
        """Plot MACD line, Signal line, and Histogram"""
        # Extract MACD data, replacing None with np.nan
        macd_line = [m['macd']['macd'] if m['macd']['macd'] is not None else np.nan for m in metrics]
        signal_line = [m['macd']['signal'] if m['macd']['signal'] is not None else np.nan for m in metrics]
        histogram = [m['macd']['histogram'] if m['macd']['histogram'] is not None else np.nan for m in metrics]
        
        # Plot histogram with conditional colors
        colors = ['lightblue' if h > 0 else 'pink' if h < 0 else 'gray' for h in histogram]
        self.ax_macd.bar(time, histogram, color=colors, alpha=0.5)
        
        # Plot MACD line
        self.ax_macd.plot(time, macd_line, color='purple', label='MACD')
        
        # Plot Signal line
        self.ax_macd.plot(time, signal_line, color='yellow', label='Signal')
        
        # Add zero line
        self.ax_macd.axhline(0, color='gray', linestyle='--')

    def _plot_fibonacci_price(self, time, metrics):
        """
        Plot the price action in the Fibonacci subplot.

        Args:
            time (list): List of time indices.
            metrics (list): List of metric dictionaries containing price data.
        """
        # Extract price data from metrics
        prices = [m['price'] for m in metrics]

        # Plot price action
        self.ax_fib.plot(time, prices, 'b-', label='Price')

        # Adjust y-axis to fit price
        price_min, price_max = min(prices), max(prices)
        padding = (price_max - price_min) * 0.1  # 10% padding
        self.ax_fib.set_ylim(price_min - padding, price_max + padding)

    def _plot_fibonacci_zones(self, time, start_position=0):
        """
        Overlay Fibonacci levels for each arc as horizontal lines from start to end.

        Args:
            time (list): List of time indices.
            start_position (int): The starting index of the sliced data (for static mode).
        """
        # Get all completed arcs
        arcs = self.trading_engine.metric_collector.fibonacci_analyzer.get_all_arcs()
        print(f"Number of completed arcs: {len(arcs)}")
        print(f"Current arc: {self.trading_engine.metric_collector.fibonacci_analyzer.current_arc}")

        # Track which Fibonacci levels have been labeled to avoid legend clutter
        labeled_levels = set()

        # Plot Fibonacci levels for each completed arc
        for arc in arcs:
            start_index = arc['start_index'] - start_position
            end_index = arc['end_index'] - start_position
            fib_levels = arc['fib_levels']

            # Ensure indices are within the time range
            if 0 <= start_index < len(time) and 0 <= end_index < len(time):
                # Draw horizontal lines for each Fibonacci level
                for level, price in fib_levels.items():
                    label = f'Fib {level}' if level not in labeled_levels else None
                    self.ax_fib.hlines(y=price, xmin=time[start_index], xmax=time[end_index],
                                      color='purple', linestyle='--', alpha=0.5, label=label)
                    if label:
                        labeled_levels.add(level)

        # Plot Fibonacci levels for the current arc (if it exists)
        current_arc = self.trading_engine.metric_collector.fibonacci_analyzer.current_arc
        if current_arc and 'start_index' in current_arc:
            start_index = current_arc['start_index'] - start_position
            end_index = len(time) - 1  # Current arc extends to the latest time point
            fib_levels = self.trading_engine.metric_collector.fibonacci_analyzer.get_current_levels()

            if 0 <= start_index < len(time) and 0 <= end_index < len(time):
                for level, price in fib_levels.items():
                    label = f'Fib {level}' if level not in labeled_levels else None
                    self.ax_fib.hlines(y=price, xmin=time[start_index], xmax=time[end_index],
                                      color='purple', linestyle='--', alpha=0.5, label=label)
                    if label:
                        labeled_levels.add(level)

    def _plot_fibonacci_levels(self, time, metrics, start_position=0):
        """
        Plot the Fibonacci subplot by first plotting the price and then overlaying Fibonacci levels.

        Args:
            time (list): List of time indices.
            metrics (list): List of metric dictionaries containing price data.
            start_position (int): The starting index of the sliced data (for static mode).
        """
        self._plot_fibonacci_price(time, metrics)
        self._plot_fibonacci_zones(time, start_position)
        self.ax_fib.legend()

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
        
        self.ax_combined.set_ylabel('Price/EMA')
        self.ax_combined.legend()
        self.ax_combined.grid(True, linestyle='--', alpha=0.7)
        
        self.ax_macd.set_ylabel('MACD')
        self.ax_macd.legend()
        self.ax_macd.grid(True, linestyle='--', alpha=0.7)
        
        self.ax_fib.set_xlabel('Time (index)')
        self.ax_fib.set_ylabel('Price/Fib Levels')
        self.ax_fib.legend()
        self.ax_fib.grid(True, linestyle='--', alpha=0.7)