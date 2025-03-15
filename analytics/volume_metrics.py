class VolumeMetrics:
    def __init__(self, price_point, window_data=None):
        self.current_volume = price_point.get("v", 0)  # Assumes OHLCV with "v" key
        self.window_data = window_data or []  # Optional historical window

    def calculate_avg_volume(self, lookback):
        if not self.window_data or len(self.window_data) < lookback:
            return None
        volume_data = [x["v"] for x in self.window_data[-lookback:]]
        return np.mean(volume_data) if volume_data else None

    def calculate_volume_change_percentage(self, lookback):
        if not self.window_data or len(self.window_data) < lookback:
            return None
        past_volume = self.window_data[-lookback]["v"]
        return ((self.current_volume - past_volume) / past_volume) * 100 if past_volume != 0 else 0.0

    def calculate_vwap(self, period_candles):
        if not self.window_data or len(self.window_data) < period_candles:
            return None
        total_volume = 0
        total_price_volume = 0
        for entry in self.window_data[-period_candles:]:
            typical_price = (entry["h"] + entry["l"] + entry["c"]) / 3
            volume = entry["v"]
            total_price_volume += typical_price * volume
            total_volume += volume
        return total_price_volume / total_volume if total_volume != 0 else None