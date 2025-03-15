from testing.utils import fetch_complete_test_data, load_historical_price, save_historical_price
from analytics.price_analytics import MetricAnalyzer_2
from analytics.chart_analyzer import ChartAnalyzer
import numpy as np
import datetime

TOKEN_ADDRESS = "9m3nh7YDoF1WSYpNxCjKVU8D1MrXsWRic4HqRaTdcTYB"

MIN_INTERVAL = "5m"    # birdeye fetching max 1000 data points of historic data
SPAN_IN_DAYS = 20


class TestDataCollector:
    def __init__(self, token_address, interval, price_data):
        self.token_address = token_address
        self.interval = interval
        self.interval_in_minutes = self.get_interval_in_minutes(interval)
        self.price_data = price_data
        self.metrics = None

        self.data_feed = None

        self.metrics_analyzer = MetricAnalyzer_2(interval)
        self.chart_analyzer = ChartAnalyzer(interval)

    
    def get_interval_in_minutes(self, interval):
        """Converts time interval (like 1m, 5m, 1H, 1D) to minutes."""
        interval_mapping = {
            "1m": 1,
            "3m": 3,
            "5m": 5,
            "15m": 15,
            "30m": 30,
            "1H": 60,
            "2H": 120,
            "4H": 240,
            "6H": 360,
            "8H": 480,
            "12H": 720,
            "1D": 1440,
            "3D": 4320,
            "1W": 10080,
            "1M": 43200  # Assuming 30 days in a month
        }
        
        return interval_mapping.get(interval, None)  # Returns None if the interval is invalid


    def calculate_price_momentum(self, span_in_minutes, interval_in_minutes):
        """Calculates relative momentum (price change percentage) for a given span in minutes."""
        # Convert span to number of candles based on interval
        num_candles = span_in_minutes // interval_in_minutes

        # Current index is the length of data_feed minus 1 (last entry)
        i = len(self.data_feed) - 1

        # Check if there's enough historical data
        if i < num_candles or i >= len(self.data_feed):
            return 0.0  # Return 0 for RL consistency if not enough data

        # Current price is the last entry in self.data_feed
        current_price = self.data_feed[-1]["value"]
        
        # Past price is num_candles ago from the current index
        past_price = self.data_feed[i - num_candles]["value"]

        # Calculate momentum (percentage change)
        momentum = ((current_price - past_price) / past_price) * 100 if past_price != 0 else 0.0

        return momentum

    def calculate_volatility(self, window_sizes=[20, 50]):
        """Calculate the standard deviation (volatility) for custom window sizes and store in self.metrics."""
        prices = self.ohlcv_price_data['close']  # Extract the closing prices
        
        # Loop through the window sizes and calculate volatility
        for window_size in window_sizes:
            if len(prices) < window_size:
                return None  # Not enough data
            else:
                # Calculate the standard deviation for the last `window_size` candles
                return np.std(prices[-window_size:])


    def collect_last_20_prices(self, end_index):
        """
        Collects up to the last 20 prices from historical data up to the given index.
        Stores (close price) and (average of high/low) for volatility analysis.
        """
        start_index = max(0, end_index - 19)  # Ensure we don't go below index 0
        last_20_prices = [
            {
                "price_close": self.ohlcv_price_data[i]["c"],
                "avg_price": (self.ohlcv_price_data[i]["h"] + self.ohlcv_price_data[i]["l"]) / 2
            }
            for i in range(start_index, end_index + 1)
        ]
        return last_20_prices
    

    def calculate_avg_volume(self, end_index, lookback):
        """
        Computes the average volume over a given lookback period.
        Returns None if not enough candles are available.
        """
        if end_index < lookback:  # Not enough data
            return None

        volume_data = [x["v"] for x in self.ohlcv_price_data[end_index - lookback:end_index]]
        
        return np.mean(volume_data) if volume_data else None
    
    def calculate_volume_change_percentage(self, end_index, lookback):
        """
        Calculates the volume change percentage compared to the lookback period.
        Returns None if there is not enough data for the lookback.
        """
        # Ensure there is enough data for the lookback
        if end_index < lookback:
            return None
        
        # Get the volume at current index and the volume at the lookback period
        current_volume = self.ohlcv_price_data[end_index]["v"]
        past_volume = self.ohlcv_price_data[end_index - lookback]["v"]
        
        # Calculate the percentage change
        volume_change_percentage = ((current_volume - past_volume) / past_volume) * 100
        
        return volume_change_percentage
    
    def calculate_pseudo_atr(self, i, window):
        if i < window:
            return 0.0
        window_data = self.data_feed["value"][i-window:i]
        return np.mean(np.abs(np.diff(window_data)))  # Average absolute price change
        
    def calculate_vwap(self, period_candles, end_index):
        """
        Calculates the Volume Weighted Average Price (VWAP) from (end_index - period_candles + 1) to end_index.
        If not enough data is available, returns None.
        """
        start_index = max(0, end_index - period_candles + 1)  # Ensure we don't go below index 0

        if end_index < start_index:
            return None

        total_volume = 0
        total_price_volume = 0

        for i in range(start_index, end_index + 1):
            # Calculate the typical price for the candle
            typical_price = (self.ohlcv_price_data[i]["h"] + self.ohlcv_price_data[i]["l"] + self.ohlcv_price_data[i]["c"]) / 3
            volume = self.ohlcv_price_data[i]["v"]

            # Volume-weighted price
            total_price_volume += typical_price * volume
            total_volume += volume

        # VWAP calculation
        if total_volume == 0:
            return None  # Avoid division by zero if there's no volume

        vwap = total_price_volume / total_volume
        return vwap
    
    def calculate_volatility(self, i, window):
        if i < window:
            return 0.0
        window_data = self.mock_real_time_data_feed["c"][i-window:i]
        return np.std(window_data)
    
    def calculate_metric_slopes(self, metric_type, timeframe, n, averaged=True):
        # Get the last `n` metrics from the list
        last_n_metrics = self.metrics[-n:]

        # Ensure we have enough data points
        if len(last_n_metrics) < 2:
            return None  

        # Extract metric values while handling missing keys
        metric_values = []
        for metric in last_n_metrics:
            try:
                metric_values.append(metric[metric_type][timeframe])
            except KeyError:
                return None  # Return None if the requested metric type or timeframe is missing

        # Ensure there are at least two valid metric values
        if len(metric_values) < 2:
            return None  

        # If we want the average slope (using the change between each consecutive value)
        if averaged:
            slopes = [(metric_values[i] - metric_values[i - 1]) for i in range(1, len(metric_values))]
            avg_slope = sum(slopes) / len(slopes)  # Rolling average slope
            return avg_slope

        # If we want the linear slope (using the first and last value over the period)
        else:
            linear_slope = (metric_values[-1] - metric_values[0]) / (n - 1)  # Linear slope
            return avg_slope


    def calculate_ema_crossovers(self, short_key, long_key, n):
        """
        Calculates EMA crossovers for the last `n` metrics using nested 'ema' keys.

        Args:
            short_key (str): The subkey for the shorter EMA (e.g., "short").
            long_key (str): The subkey for the longer EMA (e.g., "medium").
            n (int): The number of recent candles to analyze.

        Returns:
            list: A list of length `n` with values:
                - 1 (bullish crossover)
                - 0 (bearish crossover)
                - None (no crossover)
        """
        last_n_metrics = self.metrics[-n:]
        if len(last_n_metrics) < 2:
            return [None] * max(n, len(last_n_metrics))  # Pad to n if too short

        crossovers = [None] * max(n, len(last_n_metrics))  # Fixed length n
        short_ema_values = []
        long_ema_values = []

        for metric in last_n_metrics:
            try:
                short_ema_values.append(metric["ema"][short_key])
                long_ema_values.append(metric["ema"][long_key])
            except (KeyError, TypeError):
                return [None] * n  # Return None list if data is missing

        for i in range(1, len(last_n_metrics)):
            prev_short = short_ema_values[i - 1]
            prev_long = long_ema_values[i - 1]
            curr_short = short_ema_values[i]
            curr_long = long_ema_values[i]

            if prev_short <= prev_long and curr_short > curr_long:
                crossovers[i] = 1  # Bullish crossover
            elif prev_short >= prev_long and curr_short < curr_long:
                crossovers[i] = 0  # Bearish crossover

        return crossovers
    
    def calculate_rsi_divergence(self, rsi_type, n, interval, min_interval=5, rsi_overbought=70, rsi_oversold=30):
        """
        Detects RSI divergence (bullish or bearish) and evaluates the strength of the divergence, with an option for time interval-based analysis.

        Args:
            rsi_type (str): The key for the RSI type (e.g., "5-point-rsi").
            n (int): Number of candles to look back.
            interval (int): The time interval in minutes for which we want to calculate divergence (e.g., 15, 30).
            min_interval (int): The smallest time step in minutes (default is 5).
            rsi_overbought (float): RSI level considered overbought (default 70).
            rsi_oversold (float): RSI level considered oversold (default 30).

        Returns:
            dict: Contains:
                - "divergence_signal": 1 for bullish, 0 for bearish.
                - "divergence_strength": A value between 0 and 1 representing the strength of the divergence.
        """

        # Calculate the number of steps to take based on the interval and min_interval
        steps_to_take = interval // min_interval

        # Ensure we have enough data
        if len(self.mock_real_time_data_feed) < n or len(self.metrics[rsi_type]) < n:
            return None

        # Look at the last `n` data points for divergence detection
        price_segment = self.mock_real_time_data_feed[-n:]
        rsi_segment = self.metrics[rsi_type][-n:]

        # Initialize the divergence signal and strength
        divergence_signal = None
        divergence_strength = 0

        # Look for price lows/highs and RSI lows/highs
        price_lows, rsi_lows = [], []
        price_highs, rsi_highs = [], []

        # Find price lows and highs, and the corresponding RSI values
        for i in range(1, n - 1, steps_to_take):  # Adjusted to skip based on the interval
            if price_segment[i] < price_segment[i - 1] and price_segment[i] < price_segment[i + 1]:
                price_lows.append((i, price_segment[i]))
                rsi_lows.append(rsi_segment[i])
            elif price_segment[i] > price_segment[i - 1] and price_segment[i] > price_segment[i + 1]:
                price_highs.append((i, price_segment[i]))
                rsi_highs.append(rsi_segment[i])

        # Check for bullish divergence (price makes lower lows, RSI makes higher lows)
        if len(price_lows) >= 2 and len(rsi_lows) >= 2:
            for i in range(1, len(price_lows)):
                price_low1, price_low2 = price_lows[i - 1][1], price_lows[i][1]
                rsi_low1, rsi_low2 = rsi_lows[i - 1], rsi_lows[i]

                if price_low1 > price_low2 and rsi_low1 < rsi_low2:
                    # Calculate divergence strength
                    distance_price = abs(price_low1 - price_low2)
                    distance_rsi = abs(rsi_low1 - rsi_low2)
                    divergence_strength = max(divergence_strength, distance_rsi / distance_price)

                    if rsi_low2 < rsi_oversold:
                        divergence_signal = 1  # Bullish divergence
                    else:
                        divergence_signal = 1  # Bullish divergence (weak)

        # Check for bearish divergence (price makes higher highs, RSI makes lower highs)
        if len(price_highs) >= 2 and len(rsi_highs) >= 2:
            for i in range(1, len(price_highs)):
                price_high1, price_high2 = price_highs[i - 1][1], price_highs[i][1]
                rsi_high1, rsi_high2 = rsi_highs[i - 1], rsi_highs[i]

                if price_high1 < price_high2 and rsi_high1 > rsi_high2:
                    # Calculate divergence strength
                    distance_price = abs(price_high1 - price_high2)
                    distance_rsi = abs(rsi_high1 - rsi_high2)
                    divergence_strength = max(divergence_strength, distance_rsi / distance_price)

                    if rsi_high2 > rsi_overbought:
                        divergence_signal = 0  # Bearish divergence
                    else:
                        divergence_signal = 0  # Bearish divergence (weak)

        # If no divergence is detected, return None
        if divergence_signal is None:
            return None

        # Normalize divergence strength to a value between 0 and 1
        divergence_strength = min(1, max(0, divergence_strength))

        return {"divergence_signal": divergence_signal, "divergence_strength": divergence_strength}
    from datetime import datetime


    def get_time_features(self, unix_time):
        """
        Extracts minute of the day and day of the week from a Unix timestamp in UTC.
        Args:
            unix_time (int): Unix timestamp in seconds (e.g., 1741124400).
        Returns:
            dict: {"minute_of_day": int (0-1439), "day_of_week": int (0-6)}
        """
        # Convert Unix timestamp to UTC datetime
        utc_dt = datetime.fromtimestamp(unix_time, tz=timezone.utc)
        
        # Minute of the day: hours * 60 + minutes (0-1439)
        minute_of_day = utc_dt.hour * 60 + utc_dt.minute
        
        # Day of the week: 0 (Monday) to 6 (Sunday)
        day_of_week = utc_dt.weekday()
        
        return {
            "minute_of_day": minute_of_day,
            "day_of_week": day_of_week
        }
    
    def calculate_peak_distance(self):
        """
        Calculates the percentage distance from the all-time peak price using all data in self.data_feed.

        Returns:
            float: Percentage difference from the peak price (negative if below, positive if above).
                Returns 0.0 if insufficient data or peak is 0.
        """
        # Ensure data exists
        if not self.data_feed:
            return 0.0
        
        # Extract all prices from self.data_feed
        prices = [entry["value"] for entry in self.data_feed]
        
        # Current price is the last entry
        current_price = self.data_feed[-1]["value"]
        # Peak price is the maximum of all data
        peak_price = max(prices)
        
        # Calculate percentage distance from peak
        if peak_price == 0:
            return 0.0  # Avoid division by zero
        peak_distance = ((current_price - peak_price) / peak_price) * 100
        
        return peak_distance
    
    def calculate_token_age(self):
        """
        Calculates the token age in minutes from the earliest to the latest entry in self.data_feed.

        Returns:
            float: Token age in minutes. Returns 0.0 if insufficient data.
        """
        # Ensure there’s at least one entry
        if not self.data_feed or len(self.data_feed) < 1:
            return 0.0
        
        # Get Unix timestamps
        earliest_time = self.data_feed[0]["unixTime"]
        current_time = self.data_feed[-1]["unixTime"]
        
        # Calculate age in seconds, then convert to minutes
        age_seconds = current_time - earliest_time
        age_minutes = age_seconds / 60.0  # Float for precision
        
        # Ensure non-negative result
        return max(0.0, age_minutes)
    
 
    def calculate_drawdown(self, lookback_short=48, lookback_long=288):
        """
        Calculates percentage drawdown from peak prices over short and long lookback periods.

        Args:
            lookback_short (int): Short-term lookback in candles (e.g., 48 = 4hr on 5min chart).
            lookback_long (int): Long-term lookback in candles (e.g., 288 = 24hr on 5min chart).

        Returns:
            dict: {"short": float, "long": float} - % drop from peaks, 0.0 if insufficient data.
        """
        if not self.data_feed or len(self.data_feed) < 2:
            return {"short": 0.0, "long": 0.0}
        
        # Current price is the latest entry
        current_price = self.data_feed[-1]["value"]
        
        # Short-term drawdown (e.g., 4hr)
        start_idx_short = max(0, len(self.data_feed) - lookback_short)
        prices_short = [entry["value"] for entry in self.data_feed[start_idx_short:]]
        peak_short = max(prices_short)
        drawdown_short = ((current_price - peak_short) / peak_short) * 100 if peak_short != 0 else 0.0
        
        # Long-term drawdown (e.g., 24hr)
        start_idx_long = max(0, len(self.data_feed) - lookback_long)
        prices_long = [entry["value"] for entry in self.data_feed[start_idx_long:]]
        peak_long = max(prices_long)
        drawdown_long = ((current_price - peak_long) / peak_long) * 100 if peak_long != 0 else 0.0
        
        return {
            "short": drawdown_short,
            "long": drawdown_long
        }

    def collect_all_metrics_and_store(self):
        if not hasattr(self, 'data_feed'):
            self.data_feed = self.price_data.copy()
        
        for i in range(len(self.price_data)):
            if i < len(self.data_feed):
                self.data_feed[i] = self.price_data[i]
            else:
                self.data_feed.append(self.price_data[i])
            
            self.metrics_analyzer.append_price(self.data_feed[-1])
            self.chart_analyzer.append_price_data(self.data_feed[-1])
            
            current_price = self.data_feed[-1]["value"]
            zones = self.chart_analyzer.find_support_resistance_zones(i)
            support_zones_raw = [zone for zone in zones["support_zones"] if zone["zone_level"] < current_price]
            resistance_zones_raw = [zone for zone in zones["resistance_zones"] if zone["zone_level"] > current_price]
            
            def normalize_zones(zone_list, max_zones=3):
                zone_list.sort(key=lambda x: x["strength"], reverse=True)
                normalized = {}
                for j in range(max_zones):
                    prefix = f"level_{j+1}"
                    if j < len(zone_list) and current_price != 0:
                        level = zone_list[j]["zone_level"]
                        strength = zone_list[j]["strength"]
                        normalized[f"{prefix}_dist"] = ((level - current_price) / current_price) * 100
                        normalized[f"{prefix}_strength"] = strength
                    else:
                        normalized[f"{prefix}_dist"] = 0.0
                        normalized[f"{prefix}_strength"] = 0.0
                return normalized
            
            support_zones = normalize_zones(support_zones_raw)
            resistance_zones = normalize_zones(resistance_zones_raw)
            time_features = self.get_time_features(self.data_feed[-1]["unixTime"])
            
            self.metrics.append({})
            self.metrics[-1] = {
                "price": current_price,
                "momentum": {
                    "short": self.calculate_price_momentum(15, 5),
                    "medium": self.calculate_price_momentum(60, 5),
                    "long": self.calculate_price_momentum(240, 5),
                },
                "volatility": {
                    "pseudo_atr": (self.calculate_pseudo_atr(i, 14) / current_price * 100) if current_price != 0 else 0.0,  # % of price / 100 absolute alternative
                    "short": (self.calculate_volatility(i, 6) / current_price * 100) if current_price != 0 else 0.0,       # % of price
                },
                "rsi": {
                    "short": self.metrics_analyzer.calculate_rsi("5m", 15),
                    "middle_short": self.metrics_analyzer.calculate_rsi("15m", 15),
                    "long": self.metrics_analyzer.calculate_rsi("1h", 15),
                    "slope": self.calculate_metric_slopes("rsi", "short", 6),
                },
                "ema": {
                    "short": self.metrics_analyzer.calculate_ema("5m", 10),
                    "medium": self.metrics_analyzer.calculate_ema("5m", 50),
                    "long": self.metrics_analyzer.calculate_ema("5m", 100),
                    "crossover_short_medium": self.calculate_ema_crossovers("short", "medium", 6),
                    "crossover_medium_long": self.calculate_ema_crossovers("medium", "long", 12),
                },
                "support_level_1_dist": support_zones["level_1_dist"],
                "support_level_1_strength": support_zones["level_1_strength"],
                "support_level_2_dist": support_zones["level_2_dist"],
                "support_level_2_strength": support_zones["level_2_strength"],
                "support_level_3_dist": support_zones["level_3_dist"],
                "support_level_3_strength": support_zones["level_3_strength"],
                "resistance_level_1_dist": resistance_zones["level_1_dist"],
                "resistance_level_1_strength": resistance_zones["level_1_strength"],
                "resistance_level_2_dist": resistance_zones["level_2_dist"],
                "resistance_level_2_strength": resistance_zones["level_2_strength"],
                "resistance_level_3_dist": resistance_zones["level_3_dist"],
                "resistance_level_3_strength": resistance_zones["level_3_strength"],
                "token_age": self.calculate_token_age() / 1440,  # Days, uncapped
                "peak_distance": self.calculate_peak_distance(),
                "drawdown_tight": self.calculate_drawdown(3, 288)["short"],
                "drawdown_short": self.calculate_drawdown(12, 288)["short"],
                "drawdown_long": self.calculate_drawdown(12, 288)["long"],
                "time": {
                    "minute_of_day": time_features["minute_of_day"],  # Raw: 0-1439
                    "day_of_week": time_features["day_of_week"],      # Raw: 0-6
                }
            }