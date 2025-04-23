import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
import pandas as pd

class PricePlotter:
    def __init__(self, trading_engine):
        self.trading_engine = trading_engine
        self.initial_data_size = len(trading_engine.price_data)
        
        plt.ion()
        self.fig = plt.figure(figsize=(12, 15))
        
        self.ax_price = self.fig.add_subplot(511)
        self.ax_rsi = self.fig.add_subplot(512, sharex=self.ax_price)
        self.ax_combined = self.fig.add_subplot(513, sharex=self.ax_price)
        self.ax_macd = self.fig.add_subplot(514, sharex=self.ax_price)
        self.ax_fib = self.fig.add_subplot(515, sharex=self.ax_price)
        
        self.fig.subplots_adjust(hspace=0.3)
        self.ax_price.set_position([0.15, 0.75, 0.75, 0.2])
        self.ax_rsi.set_position([0.15, 0.66, 0.75, 0.08])
        self.ax_combined.set_position([0.15, 0.44, 0.75, 0.2])
        self.ax_macd.set_position([0.15, 0.35, 0.75, 0.08])
        self.ax_fib.set_position([0.15, 0.15, 0.75, 0.2])
        
        self.targets_index = None
        self.similars_index = None
        self.plot_backtest = False

    def plot_live(self):
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
        max_idx = len(self.trading_engine.metric_collector.metrics) - 1
        self.targets_index = [i for i in targets_index if 0 <= i <= max_idx]
        self.similars_index = [i for i in similars_index if 0 <= i <= max_idx]
        self.plot_backtest = True

    def _clear_axes(self):
        self.ax_price.clear()
        self.ax_rsi.clear()
        self.ax_combined.clear()
        self.ax_macd.clear()
        self.ax_fib.clear()

    def _plot_price(self, time, metrics, include_backtest=False):
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
        """Plot 60-minute OHLCV candlesticks with EMA, SMA, Bollinger Bands, and crossovers"""
        # Plot RSI divergence crossovers (background)
        divergence_strengths = [m['divergence'] for m in metrics]
        prices = [m['price'] for m in metrics]
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
                    zorder=0
                )
            elif divergence_strengths[i] < 0:  # Bearish
                self.ax_combined.axvspan(
                    time[i-1], time[i], 
                    ymin=0, ymax=1,
                    color='red', 
                    alpha=min(0.05, abs(divergence_strengths[i])),
                    zorder=0
                )
        
        # Fetch 5-minute price data timestamps for alignment
        price_data = self.trading_engine.metric_collector.price_data
        price_timestamps = [entry['unixTime'] for entry in price_data]
        print("First few 5-minute price timestamps:", price_timestamps[:3])
        
        # Calculate the first full-hour timestamp after the first price point
        interval_seconds = 60 * 60  # 60 minutes in seconds
        first_timestamp = price_timestamps[0]
        first_full_hour = ((first_timestamp // interval_seconds) * interval_seconds) + interval_seconds
        print(f"First full hour: {first_full_hour}")
        
        # Fetch 60-minute OHLCV data
        ohlcv_data = self.trading_engine.metric_collector.interval_data_aggregator.get_interval_data(60)
        if ohlcv_data:
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv_data)
            
            # Debug: Print the first few 60-minute OHLCV entries
            print("First few 60-minute OHLCV entries:")
            for i in range(min(5, len(df))):
                print(f"Timestamp: {df['timestamp'].iloc[i]}, Open: {df['open'].iloc[i]}, Close: {df['close'].iloc[i]}")
            
            # Calculate time_index based on the difference from the first timestamp
            df['time_index'] = df['timestamp'].apply(
                lambda t: int((t - first_timestamp) / 300)  # 300 seconds = 5 minutes
            )
            
            # Filter out candles before the first full hour
            df = df[df['timestamp'] >= first_full_hour]
            
            # Debug: Print the first few time indices
            print("First few time indices for 60-minute candles:")
            print(df[['timestamp', 'time_index']].head(5))
            
            # Filter candles within the current time range
            df = df[(df['time_index'] >= time[0]) & (df['time_index'] <= time[-1])]
            
            # Remove duplicates by keeping the latest candle for each time_index
            df = df.groupby('time_index').last().reset_index()
            
            if not df.empty:
                # Use a single rectangle per 60-minute candlestick
                candle_width = 12.0  # 12 x 5-minute intervals (60 minutes)
                half_width = candle_width / 2
                
                for _, row in df.iterrows():
                    x_center = row['time_index']
                    open_price, high, low, close = row['open'], row['high'], row['low'], row['close']
                    
                    print(f"Candlestick at time_index {x_center}: Open={open_price}, High={high}, Low={low}, Close={close}")
                    
                    color = (0, 0.5, 0, 0.7) if close >= open_price else (1, 0, 0, 0.7)
                    body_height = abs(open_price - close)
                    body_bottom = min(open_price, close)
                    
                    rect = Rectangle(
                        (x_center - half_width, body_bottom),
                        candle_width, body_height,
                        color=color,
                        zorder=1
                    )
                    self.ax_combined.add_patch(rect)
                    
                    wick = Line2D(
                        [x_center, x_center], [low, high],
                        color='black',
                        zorder=1
                    )
                    self.ax_combined.add_line(wick)
        
        # Set y-axis limits based on price data
        padding = (price_max - price_min) * 0.1
        self.ax_combined.set_ylim(price_min - padding, price_max + padding)
        
        # Debug: Print the first few 5-minute prices and EMA values
        print("First few 5-minute prices and EMA values:")
        for i in range(min(3, len(metrics))):
            ema = metrics[i].get('ema', {})
            price = prices[i]
            ema_short = (ema.get('short', 0) or 0) * price
            print(f"Time index {time[i]}: Price={price}, EMA Short={ema_short}")
        
        # Plot EMA prices (foreground)
        ema_short = []
        ema_medium = []
        ema_long = []
        ema_longterm = []
        
        for i, m in enumerate(metrics):
            ema = m.get('ema', {})
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

    def _plot_zones(self, metric):
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
        macd_line = [m['macd']['macd'] if m['macd']['macd'] is not None else np.nan for m in metrics]
        signal_line = [m['macd']['signal'] if m['macd']['signal'] is not None else np.nan for m in metrics]
        histogram = [m['macd']['histogram'] if m['macd']['histogram'] is not None else np.nan for m in metrics]
        
        colors = ['lightblue' if h > 0 else 'pink' if h < 0 else 'gray' for h in histogram]
        self.ax_macd.bar(time, histogram, color=colors, alpha=0.5)
        
        self.ax_macd.plot(time, macd_line, color='purple', label='MACD')
        self.ax_macd.plot(time, signal_line, color='yellow', label='Signal')
        self.ax_macd.axhline(0, color='gray', linestyle='--')

    def _plot_fibonacci_price(self, time, metrics):
        prices = [m['price'] for m in metrics]
        self.ax_fib.plot(time, prices, 'b-', label='Price')
        price_min, price_max = min(prices), max(prices)
        padding = (price_max - price_min) * 0.1
        self.ax_fib.set_ylim(price_min - padding, price_max + padding)

    def _plot_fibonacci_zones(self, time, start_position=0):
        fib_colors = {
            '23.6%': 'red',
            '38.2%': 'orange',
            '50%': 'green',
            '61.8%': 'blue',
            '78.6%': 'purple',
            '90.0%': 'magenta'
        }

        arcs = self.trading_engine.metric_collector.fibonacci_analyzer.get_all_arcs()
        print(f"Number of completed arcs: {len(arcs)}")
        print(f"Current arc: {self.trading_engine.metric_collector.fibonacci_analyzer.current_arc}")

        labeled_levels = set()
        for arc in arcs:
            start_index = arc['start_index'] - start_position
            end_index = arc['end_index'] - start_position
            fib_levels = arc['fib_levels']

            if 0 <= start_index < len(time) and 0 <= end_index < len(time):
                for level, price in fib_levels.items():
                    color = 'black' if level in ['0%', '100%'] else fib_colors.get(level, 'purple')
                    label = f'Fib {level}' if level not in labeled_levels else None
                    self.ax_fib.hlines(y=price, xmin=time[start_index], xmax=time[end_index],
                                    color=color, linestyle='--', alpha=0.5, label=label)
                    if label:
                        labeled_levels.add(level)

        current_arc = self.trading_engine.metric_collector.fibonacci_analyzer.current_arc
        if current_arc and 'start_index' in current_arc:
            start_index = current_arc['start_index'] - start_position
            end_index = len(time) - 1
            fib_levels = self.trading_engine.metric_collector.fibonacci_analyzer.get_current_levels()

            if 0 <= start_index < len(time) and 0 <= end_index < len(time):
                for level, price in fib_levels.items():
                    color = 'black' if level in ['0%', '100%'] else fib_colors.get(level, 'purple')
                    label = f'Fib {level}' if level not in labeled_levels else None
                    self.ax_fib.hlines(y=price, xmin=time[start_index], xmax=time[end_index],
                                    color=color, linestyle='--', alpha=0.5, label=label)
                    if label:
                        labeled_levels.add(level)

    def _plot_fibonacci_levels(self, time, metrics, start_position=0):
        self._plot_fibonacci_price(time, metrics)
        self._plot_fibonacci_zones(time, start_position)

    def _customize_plots(self, title):
        legend_params = {
            'loc': 'center left',
            'bbox_to_anchor': (-0.1, 0.5),
            'fontsize': 6,
            'frameon': True,
            'borderaxespad': 0.,
            'labelspacing': 0.2,
            'handlelength': 1.0,
            'handletextpad': 0.4
        }

        self.ax_price.set_ylabel('Price')
        self.ax_price.set_title(title)
        self.ax_price.legend(**legend_params)
        self.ax_price.grid(True, linestyle='--', alpha=0.7)

        self.ax_rsi.set_ylabel('RSI')
        self.ax_rsi.legend(**legend_params)
        self.ax_rsi.grid(True, linestyle='--', alpha=0.7)
        self.ax_rsi.set_ylim(0, 100)

        self.ax_combined.set_ylabel('Price/EMA')
        self.ax_combined.legend(**legend_params)
        self.ax_combined.grid(True, linestyle='--', alpha=0.7)

        self.ax_macd.set_ylabel('MACD')
        self.ax_macd.legend(**legend_params)
        self.ax_macd.grid(True, linestyle='--', alpha=0.7)

        self.ax_fib.set_ylabel('Fibonacci Levels')
        self.ax_fib.legend(**legend_params)
        self.ax_fib.grid(True, linestyle='--', alpha=0.7)