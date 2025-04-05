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

    def calculate_atr(self, atr_period=14):
        """
        Calculate the Average True Range (ATR).

        Args:
            atr_period (int): Period for ATR calculation (default: 14).

        Returns:
            float: The current ATR value, or None if insufficient data.
        """
        prices = list(self.metric_collector.price_data)[-atr_period:]

        if len(prices) < atr_period:
            return None

        # Approximate ATR using absolute price changes (since we only have "value")
        close_prices = pd.Series([x["value"] for x in prices])
        price_changes = close_prices.diff().abs()
        atr = price_changes.rolling(window=atr_period).mean().iloc[-1]
        return atr

    def detect_price_arc(self, atr_period=14, atr_multiplier=2):
        """
        Detect price arcs and update Fibonacci levels using the latest price from metric_collector.price_data.

        Args:
            atr_period (int): Period for ATR calculation (default: 14).
            atr_multiplier (float): Multiplier for ATR to define significant drawdowns (default: 2).
        """
        price_data = self.metric_collector.price_data
        if not price_data:
            return

        atr = self.calculate_atr(atr_period)
        if atr is None:
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
                'start_index': new_index  # Track the start of the arc
            }
            self.update_fibonacci_levels()
            return

        # Update the low if the new price is lower
        if new_price < self.current_arc['low']:
            # End the current arc by setting its end_index
            self.current_arc['end_index'] = new_index
            # Calculate Fibonacci levels for the completed arc
            high = self.current_arc['high']
            low = self.current_arc['low']
            range_size = high - low
            fib_levels = {
                '23.6%': high - range_size * 0.236,
                '38.2%': high - range_size * 0.382,
                '50%': high - range_size * 0.5,
                '61.8%': high - range_size * 0.618,
                '78.6%': high - range_size * 0.786,
                '90.0%': high - range_size * 0.9
            }
            # Store the completed arc with its Fibonacci levels
            self.arcs.append({
                'start_index': self.current_arc['start_index'],
                'end_index': new_index,
                'fib_levels': fib_levels
            })
            # Start a new arc with the new low
            self.current_arc = {
                'low': new_price,
                'low_index': new_index,
                'high': new_price,
                'high_index': new_index,
                'start_index': new_index
            }
        # Update the high if the new price is higher
        elif new_price > self.current_arc['high']:
            self.current_arc['high'] = new_price
            self.current_arc['high_index'] = new_index
        # Check if the arc has ended (significant drop from high)
        else:
            drawdown = (self.current_arc['high'] - new_price) / self.current_arc['high']
            if drawdown > atr_multiplier * atr / self.current_arc['high']:
                # End the current arc by setting its end_index
                self.current_arc['end_index'] = new_index
                # Calculate Fibonacci levels for the completed arc
                high = self.current_arc['high']
                low = self.current_arc['low']
                range_size = high - low
                fib_levels = {
                    '23.6%': high - range_size * 0.236,
                    '38.2%': high - range_size * 0.382,
                    '50%': high - range_size * 0.5,
                    '61.8%': high - range_size * 0.618,
                    '78.6%': high - range_size * 0.786,
                    '90.0%': high - range_size * 0.9
                }
                # Store the completed arc with its Fibonacci levels
                self.arcs.append({
                    'start_index': self.current_arc['start_index'],
                    'end_index': new_index,
                    'fib_levels': fib_levels
                })
                # Start a new arc with the new low
                self.current_arc = {
                    'low': new_price,
                    'low_index': new_index,
                    'high': new_price,
                    'high_index': new_index,
                    'start_index': new_index
                }

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

        # Fibonacci levels for the current arc
        self.fib_levels = {
            '23.6%': high - range_size * 0.236,
            '38.2%': high - range_size * 0.382,
            '50%': high - range_size * 0.5,
            '61.8%': high - range_size * 0.618,
            '78.6%': high - range_size * 0.786,
            '90.0%': high - range_size * 0.9
        }

    def get_current_levels(self):
        """Return the current Fibonacci levels."""
        return self.fib_levels

    def get_all_arcs(self):
        """Return all completed arcs with their Fibonacci levels."""
        return self.arcs

    def recalculate(self, atr_period=14, atr_multiplier=2):
        """
        Recalculate the Fibonacci levels using the latest price data from metric_collector.

        Args:
            atr_period (int): Period for ATR calculation (default: 14).
            atr_multiplier (float): Multiplier for ATR to define significant drawdowns (default: 2).
        """
        self.detect_price_arc(atr_period, atr_multiplier)