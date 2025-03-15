

# Kept for later implementation, reduces pointer memory usage

class PriceWindow:
    """Manages a sliding window of price data for efficient metric calculation."""
    def __init__(self, price_data, max_window):
        self.price_data = price_data
        self.max_window = max_window  # Largest lookback needed (e.g., 288 for drawdown_long)
        self.start_idx = max(0, len(price_data) - max_window) if price_data else 0

    def get_window(self, size, offset=0):
        """Returns a window of `size` candles ending at offset from latest."""
        end_idx = len(self.price_data) - 1 - offset
        start_idx = max(self.start_idx, end_idx - size + 1)
        return self.price_data[start_idx:end_idx + 1]

    def get_latest(self):
        """Returns the latest price entry."""
        return self.price_data[-1] if self.price_data else None

    def append(self, new_point):
        """Appends a new price point, adjusts window."""
        self.price_data.append(new_point)
        self.start_idx = max(0, len(self.price_data) - self.max_window)