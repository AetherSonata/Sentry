import pandas as pd
import numpy as np

class FibonacciAnalyzer:
    def __init__(self, metric_collector):
        """
        Initialize the DrawdownAnalyzer.

        Args:
            metric_collector: The metric_collector object providing interval and price_data.
        """
        self.metric_collector = metric_collector
        self.interval = metric_collector.interval  # Get interval from metric_collector
        self.price_data = metric_collector.price_data  # Get price_data from metric_collector

        # State variables
        self.current_arc = None  # {'low': price, 'low_index': index, 'high': price, 'high_index': index}
        self.fib_levels = {}  # Current Fibonacci levels
        self.arcs = []  # List of completed arcs

    def calculate_atr(self, atr_period=14):
        """
        Calculate the Average True Range (ATR).

        Args:
            atr_period (int): Period for ATR calculation (default: 14).

        Returns:
            float: The current ATR value, or None if insufficient data.
        """
        prices = list(self.price_data)[-atr_period:]

        if len(prices) < atr_period:
            return None

        # Approximate ATR using absolute price changes (since we only have "value")
        close_prices = pd.Series([x["value"] for x in prices])
        price_changes = close_prices.diff().abs()
        atr = price_changes.rolling(window=atr_period).mean().iloc[-1]
        return atr

    def detect_price_arc(self, new_price, new_index, atr_period=14, atr_multiplier=2):
        """
        Detect price arcs and update Fibonacci levels. The lowest price point is always the new low.

        Args:
            new_price (float): The latest price.
            new_index (int): The index of the latest price in price_data.
            atr_period (int): Period for ATR calculation (default: 14).
            atr_multiplier (float): Multiplier for ATR to define significant drawdowns (default: 2).
        """
        atr = self.calculate_atr(atr_period)
        if atr is None:
            return

        # If no current arc, start one with the first price as the low
        if not self.current_arc:
            self.current_arc = {
                'low': new_price,
                'low_index': new_index,
                'high': new_price,
                'high_index': new_index
            }
            self.update_fibonacci_levels()
            return

        # Update the low if the new price is lower
        if new_price < self.current_arc['low']:
            # End the current arc
            self.arcs.append(self.current_arc.copy())
            # Start a new arc with the new low
            self.current_arc = {
                'low': new_price,
                'low_index': new_index,
                'high': new_price,
                'high_index': new_index
            }
        # Update the high if the new price is higher
        elif new_price > self.current_arc['high']:
            self.current_arc['high'] = new_price
            self.current_arc['high_index'] = new_index
        # Check if the arc has ended (significant drop from high)
        else:
            drawdown = (self.current_arc['high'] - new_price) / self.current_arc['high']
            if drawdown > atr_multiplier * atr / self.current_arc['high']:
                # End the current arc
                self.arcs.append(self.current_arc.copy())
                # Start a new arc with the new low
                self.current_arc = {
                    'low': new_price,
                    'low_index': new_index,
                    'high': new_price,
                    'high_index': new_index
                }

        # Update Fibonacci levels and 90% drawdown
        self.update_fibonacci_levels()

    def update_fibonacci_levels(self):
        """Calculate Fibonacci retracement levels and 90% drawdown from the current arc's high."""
        if not self.current_arc:
            self.fib_levels = {}
            self.drawdown_90 = None
            return

        high = self.current_arc['high']
        low = self.current_arc['low']
        range_size = high - low

        # Fibonacci levels
        self.fib_levels = {
            '23.6%': high - range_size * 0.236,
            '38.2%': high - range_size * 0.382,
            '50%': high - range_size * 0.5,
            '61.8%': high - range_size * 0.618,
            '78.6%': high - range_size * 0.786,
            '90.0%': high - range_size * 0.9,
        }


    def get_current_levels(self):
        """Return the current Fibonacci levels and 90% drawdown level."""
        return self.fib_levels, self.drawdown_90

    def update(self, new_price, new_index, atr_period=14, atr_multiplier=2):
        """
        Update the analyzer with a new price point.

        Args:
            new_price (float): The latest price.
            new_index (int): The index of the latest price in price_data.
            atr_period (int): Period for ATR calculation (default: 14).
            atr_multiplier (float): Multiplier for ATR to define significant drawdowns (default: 2).
        """
        self.price_data.append({"value": new_price})
        self.detect_price_arc(new_price, new_index, atr_period, atr_multiplier)