
import numpy as np
class PriceAnalytics:
    def __init__(self, initial_price_data=[], max_window=288):
        self.max_window = max_window
        # Start with last max_window entries if initial data exceeds it
        self.price_data = initial_price_data[-max_window:] if initial_price_data and len(initial_price_data) > max_window else initial_price_data or []

    def append(self, price_point):
        """Append a new price point, cap at max_window."""
        self.price_data.append(price_point)
        if len(self.price_data) > self.max_window:
            self.price_data.pop(0)

    def calculate_price_momentum(self, span_in_minutes, interval_in_minutes):
        """Calculates relative momentum (price change percentage) for a given span in minutes."""
        num_candles = span_in_minutes // interval_in_minutes
        i = len(self.price_data) - 1
        if i < num_candles or i >= len(self.price_data):
            return 0.0
        current_price = self.price_data[-1]["value"]
        past_price = self.price_data[i - num_candles]["value"]
        return ((current_price - past_price) / past_price) * 100 if past_price != 0 else 0.0

    def calculate_volatility(self, i, window):
        """Calculate standard deviation (volatility) over a window, using latest data."""
        if len(self.price_data) < 2:
     
            return 0.0
        # Cap i at the last index
        effective_i = min(i, len(self.price_data) - 1) if i >= 0 else 0
        start_idx = max(0, effective_i - window + 1)
        window_data = [entry["value"] for entry in self.price_data[start_idx:effective_i + 1]]
       
        if len(window_data) < 2:
   
            return 0.0
        result = np.std(window_data, ddof=1)

        return result

    def calculate_pseudo_atr(self, i, window):
        """Calculate average true range approximation, using latest data."""

        if len(self.price_data) < 2:
     
            return 0.0
        # Cap i at the last index
        effective_i = min(i, len(self.price_data) - 1) if i >= 0 else 0
        start_idx = max(0, effective_i - window + 1)
        window_data = [entry["value"] for entry in self.price_data[start_idx:effective_i + 1]]
       
        if len(window_data) < 2:

            return 0.0
        diff_data = np.abs(np.diff(window_data))
    
        result = np.mean(diff_data)
   
        return result