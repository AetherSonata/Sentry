import numpy as np

class FibonacciAnalyzer:
    def __init__(self, interval, price_data=[]):
        self.interval = interval  # e.g., '5m'
        self.price_data = price_data  # List of {'value': float} entries
        self.last_ath_idx = -1  # Index of the last all-time high
        self.fib_time_indices = []  # List of Fibonacci time reversal indices

    def append_price_data(self, price_data):
        """Append new price data and check Fibonacci reversal."""
        self.price_data.append(price_data)
        self.check_fibonacci_time_update()  # Update on every append

    def check_fibonacci_time_update(self):
        """
        Check for ATH and update Fibonacci time indices based on internal current step.

        Returns:
            int or None: The current step if it matches a Fibonacci index, None otherwise.
        """
        if len(self.price_data) < 2:  # Need at least 2 points to analyze
            return None

        # Derive current step from price_data length (index of latest entry)
        current_step = len(self.price_data) - 1

        # Extract current price
        current_price = self.price_data[-1]['value']
        prices = [entry['value'] for entry in self.price_data]

        # Check if current price is a new ATH
        if current_price > max(prices[:-1], default=0):  # Compare with all previous prices
            self.last_ath_idx = current_step
            # Calculate Fibonacci indices starting from the ATH as the first step
            self._calculate_fibonacci_time_reversal()

        # Return the current step if it matches a Fibonacci index
        if current_step in self.fib_time_indices:
            return current_step
        return None

    def _calculate_fibonacci_time_reversal(self):
        """
        Calculate and store Fibonacci time reversal indices starting from the last ATH as step 0.
        """
        if self.last_ath_idx == -1:  # No ATH yet
            self.fib_time_indices = []
            return

        # Fibonacci sequence for time intervals (starting from 0 at the ATH)
        fib_intervals = [0, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]  # ATH is 0
        
        # Calculate Fibonacci time indices starting from last_ath_idx
        self.fib_time_indices = [self.last_ath_idx + interval for interval in fib_intervals]
        
        # Filter out indices beyond current data length
        prices = len(self.price_data)
        self.fib_time_indices = [idx for idx in self.fib_time_indices if idx < prices]