import pandas as pd
import numpy as np

class FibonacciAnalyzer:
    def __init__(self, metric_collector):
        """
        Initialize the FibonacciAnalyzer.

        Args:
            metric_collector: The metric_collector object providing interval and price_data.
        """
        self.metric_collector = metric_collector
        self.interval = metric_collector.interval  # Get interval from metric_collector

        # State variables
        self.current_arc = None  # {'low': price, 'low_index': index, 'high': price, 'high_index': index, 'start_index': index, 'end_index': index}
        self.fib_levels = {}  # Current Fibonacci levels for the active arc
        self.arcs = []  # List of completed arcs with start, end, and fib levels

    def calculate_atr(self, atr_period=20):
        """
        Calculate the Average True Range (ATR) with dynamic period.

        Args:
            atr_period (int): Maximum period for ATR calculation (default: 20).

        Returns:
            float: The current ATR value, or 1e-6 if insufficient data.
        """
        prices = list(self.metric_collector.price_data)
        if not prices:
            return 1e-6

        effective_period = min(atr_period, len(prices))
        if effective_period < 2:
            return 1e-6

        close_prices = pd.Series([x["value"] for x in prices[-effective_period:]])
        price_changes = close_prices.diff().abs()
        atr = price_changes.rolling(window=effective_period).mean().iloc[-1]
        return atr if not pd.isna(atr) else 1e-6

    def calculate_overall_range(self, lookback=50):
        """
        Calculate the overall price range over a lookback period.

        Args:
            lookback (int): Number of intervals to look back for calculating the range (default: 50).

        Returns:
            float: The price range (high - low) over the lookback period, or 1e-6 if insufficient data.
        """
        prices = list(self.metric_collector.price_data)
        if not prices:
            return 1e-6

        lookback_prices = [p["value"] for x in prices[-lookback:]]
        if len(lookback_prices) < 2:
            return 1e-6

        return max(lookback_prices) - min(lookback_prices)

    def detect_price_arc(self, atr_period=20, lookback=50, fib_level_threshold=0.618):
        """
        Detect price arcs and update Fibonacci levels using the latest price from metric_collector.price_data.
        A new arc begins when the price hits the 0.618 Fibonacci retracement level of the current arc.

        Args:
            atr_period (int): Maximum period for ATR calculation (default: 20).
            lookback (int): Lookback period for calculating overall price range (default: 50).
            fib_level_threshold (float): Fibonacci level at which to start a new arc (default: 0.618).
        """
        price_data = self.metric_collector.price_data
        if not price_data:
            return

        atr = self.calculate_atr(atr_period)
        if atr is None:
            print("Warning: ATR calculation returned None")
            return

        # Get the latest price and index from price_data
        new_price = price_data[-1]["value"]
        new_index = len(price_data) - 1

        # If no current arc, start one with the latest price as the low
        if not self.current_arc:
            self.current_arc = {
                'low': new_price,
                'low_index': new_index,
                'high': new_price,
                'high_index': new_index,
                'start_index': new_index
            }
            print(f"Starting new arc at index {new_index}: low={new_price:.6f}")
            self.update_fibonacci_levels()
            return

        # Update the high if the new price is higher
        if new_price > self.current_arc['high']:
            self.current_arc['high'] = new_price
            self.current_arc['high_index'] = new_index
            self.update_fibonacci_levels()
            return

        # Calculate the range of the current arc
        range_size = self.current_arc['high'] - self.current_arc['low']

        # Check if the price has dropped to or below the 0.618 Fibonacci level
        fib_threshold_price = self.current_arc['high'] - fib_level_threshold * range_size
        if new_price <= fib_threshold_price:
            print(f"Price hit 0.618 level at index {new_index}: price={new_price:.6f}, fib_threshold={fib_threshold_price:.6f}")
            # End the current arc by setting its end_index
            self.current_arc['end_index'] = new_index
            # Calculate Fibonacci levels for the completed arc
            high = self.current_arc['high']
            low = self.current_arc['low']
            range_size = high - low
            fib_levels = {
                '0%': high,
                '23.6%': high - range_size * 0.236,
                '38.2%': high - range_size * 0.382,
                '50%': high - range_size * 0.5,
                '61.8%': high - range_size * 0.618,
                '78.6%': high - range_size * 0.786,
                '90.0%': high - range_size * 0.9,
                '100%': low
            }
            # Store the completed arc with its Fibonacci levels
            self.arcs.append({
                'start_index': self.current_arc['start_index'],
                'end_index': new_index,
                'fib_levels': fib_levels
            })
            print(f"Completed arc: start={self.current_arc['start_index']}, end={new_index}, high={high:.6f}, low={low:.6f}")
            # Start a new arc with the current price as the new low
            self.current_arc = {
                'low': new_price,
                'low_index': new_index,
                'high': new_price,
                'high_index': new_index,
                'start_index': new_index
            }
            print(f"New arc starting at index {new_index}: low={new_price:.6f}")

        # Update Fibonacci levels for the current arc
        self.update_fibonacci_levels()

    def update_fibonacci_levels(self):
        """Calculate Fibonacci retracement levels from the current arc's high."""
        if not self.current_arc:
            self.fib_levels = {}
            return

        high = self.current_arc['high']
        low = self.current_arc['low']
        range_size = high - low

        # Fibonacci levels for the current arc, including 0% and 100%
        self.fib_levels = {
            '0%': high,
            '23.6%': high - range_size * 0.236,
            '38.2%': high - range_size * 0.382,
            '50%': high - range_size * 0.5,
            '61.8%': high - range_size * 0.618,
            '78.6%': high - range_size * 0.786,
            '90.0%': high - range_size * 0.9,
            '100%': low
        }

    def get_current_levels(self):
        """Return the current Fibonacci levels."""
        return self.fib_levels

    def get_all_arcs(self):
        """Return all completed arcs with their Fibonacci levels."""
        return self.arcs

    def recalculate(self, atr_period=20, lookback=50, fib_level_threshold=0.618):
        """
        Recalculate the Fibonacci levels using the latest price data from metric_collector.

        Args:
            atr_period (int): Maximum period for ATR calculation (default: 20).
            lookback (int): Lookback period for calculating overall price range (default: 50).
            fib_level_threshold (float): Fibonacci level at which to start a new arc (default: 0.618).
        """
        self.detect_price_arc(atr_period, lookback, fib_level_threshold)