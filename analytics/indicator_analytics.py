import pandas as pd
import numpy as np
from scipy.signal import find_peaks


class IndicatorAnalyzer:
    def __init__(self, metric_collector):
        self.min_interval = metric_collector.interval
        self.price_data = metric_collector.price_data
        self.ema_values = {}
        self.rsi_values = {}
        self.metrics = metric_collector.metrics
        self.available_intervals = {
            "1m": 1, "5m": 5, "15m": 15, "30m": 30,
            "1h": 60, "4h": 240, "12h": 720,
            "1d": 1440, "3d": 4320, "1w": 10080
        }

    def calculate_ema(self, interval, period, avg_prev=False):
        if interval not in self.available_intervals:
            return None

        step = self.available_intervals[interval] // self.available_intervals[self.min_interval]
        prices = list(self.price_data)[-period * step::step]

        if len(prices) < period:
            return None

        price_series = pd.Series([x["value"] for x in prices])
        key = f"{period}-{interval}"

        if key in self.ema_values and self.ema_values[key] is not None:
            prev_ema = self.ema_values[key]
            multiplier = 2 / (period + 1)
            new_ema = (price_series.iloc[-1] - prev_ema) * multiplier + prev_ema
        else:
            new_ema = price_series.ewm(span=period, adjust=False).mean().iloc[-1]

        self.ema_values[key] = new_ema
        
        if avg_prev:
            self.ema_values[key] = None  #turn on off if current should be calculated with previous

        # self.metrics.append({key: new_ema}) # save in metrics for up to date calculations
        return new_ema

    def calculate_rsi(self, interval, period=15, avg_prev=False):
        
        if interval not in self.available_intervals:
            return None

        step = self.available_intervals[interval] // self.available_intervals[self.min_interval]
        prices = list(self.price_data)[-period * step::step]

        # if interval == "5m":
        #     print(f"interval: {interval}")
        #     print(f"step: {step}")
        #     print(f"prices: {prices}")
            

        if len(prices) < period:
            return None

        price_series = pd.Series([x["value"] for x in prices])
        delta = price_series.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        key = f"RSI-{interval}"

        if key in self.rsi_values and self.rsi_values[key] is not None:
            prev_avg_gain, prev_avg_loss = self.rsi_values[key]
            avg_gain = ((prev_avg_gain * (period - 1)) + gain.iloc[-1]) / period
            avg_loss = ((prev_avg_loss * (period - 1)) + loss.iloc[-1]) / period
        else:
            avg_gain = gain.rolling(window=period).mean().iloc[-1]
            avg_loss = loss.rolling(window=period).mean().iloc[-1]

        if avg_loss == 0:
            rs = 0  # Prevent division by zero
        else:
            rs = avg_gain / avg_loss

        rsi = 100 - (100 / (1 + rs))
        self.rsi_values[key] = (avg_gain, avg_loss)

        if avg_prev:
            self.rsi_values[key] = None  #turn on off if current should be calculated with previous

        # self.metrics.append({key : rsi})  # save in metrics for up to date calculations

        return rsi

    #TODO might need to change to accept ema values
    def calculate_indicator_slopes(self, metric_type, interval, n, averaged=True):
        """Calculate the slope of indicator values over the last n points from self.metrics."""
        # Construct the key used in self.metrics
        key = f"{metric_type}-{interval}" if metric_type == "RSI" else f"{n}-{interval}"

        # Extract values from self.metrics for the given metric_type and interval
        metric_values = [metric[key] for metric in self.metrics if key in metric]

        # Ensure we have enough data points (at least 2 for a slope)
        if len(metric_values) < 2:
            return None  

        # Take the last n values
        last_n_values = metric_values[-n:]

        # If averaged, calculate the average slope between consecutive values
        if averaged:
            slopes = [(last_n_values[i] - last_n_values[i - 1]) for i in range(1, len(last_n_values))]
            avg_slope = sum(slopes) / len(slopes)  # Rolling average slope
            return avg_slope

        # If not averaged, calculate the linear slope using first and last values
        else:
            linear_slope = (last_n_values[-1] - last_n_values[0]) / (len(last_n_values) - 1)  # Linear slope
            return linear_slope

    def calculate_ema_crossovers(self, short_ema_list, long_ema_list, current_short, current_long):
        """
        Calculates EMA crossovers given lists of short and long EMA values plus current values.

        Args:
            short_ema_list (list): List of recent short EMA values (any length, may contain None).
            long_ema_list (list): List of recent long EMA values (same length as short_ema_list, may contain None).
            current_short (float): The newest short EMA value.
            current_long (float): The newest long EMA value.

        Returns:
            list: A list with length equal to input list length + 1, containing:
                - 1 (bullish crossover)
                - 0 (bearish crossover)
                - None (no crossover or invalid data)
        """
        # Filter out None values from input lists, keeping pairs aligned
        valid_pairs = [(s, l) for s, l in zip(short_ema_list, long_ema_list) if s is not None and l is not None]
        short_valid = [pair[0] for pair in valid_pairs]
        long_valid = [pair[1] for pair in valid_pairs]

        # Add current values (assume they're valid floats)
        short_emas = short_valid + [current_short]
        long_emas = long_valid + [current_long]

        # Original input length including current values
        n = len(short_ema_list) + 1

        # If less than 2 valid entries, return None list of original length
        if len(short_emas) < 2:
            return [None] * n

        # Adjust to minimum length of valid data
        n_valid = min(len(short_emas), len(long_emas))
        short_emas = short_emas[-n_valid:]
        long_emas = long_emas[-n_valid:]

        # Initialize result with None, matching original input length
        crossovers = [None] * n

        # Check crossovers only on valid data
        for i in range(1, n_valid):
            prev_short = short_emas[i - 1]
            prev_long = long_emas[i - 1]
            curr_short = short_emas[i]
            curr_long = long_emas[i]

            # Ensure all values are numeric (redundant with filter, but safe)
            if any(x is None for x in [prev_short, prev_long, curr_short, curr_long]):
                continue

            if prev_short <= prev_long and curr_short > curr_long:
                # Map valid index to original list position
                orig_idx = n - (n_valid - i)
                crossovers[orig_idx] = 1  # Bullish crossover
            elif prev_short >= prev_long and curr_short < curr_long:
                orig_idx = n - (n_valid - i)
                crossovers[orig_idx] = 0  # Bearish crossover

            return crossovers

    def analyze_rsi_divergence(self, latest_rsi, rsi_key=["rsi", "short"], lookback=30, peak_distance=5):
        """
        Analyzes RSI divergence based on past metrics and latest RSI value.

        Args:
            latest_rsi (float): The current RSI value to append.
            rsi_key (list): Nested key for RSI in metrics (e.g., ["rsi", "middle_short"]).
            lookback (int): Number of past periods to analyze (default: 30).
            peak_distance (int): Minimum distance between peaks/troughs for detection (default: 5).

        Returns:
            float: Divergence strength between -1 (bearish) and 1 (bullish), 0 if no divergence.
        """
        # Default return if insufficient data
        if not self.metrics or len(self.metrics) < 2:
            return 0.0

        # Extract lookback period from metrics
        past_metrics = self.metrics[-lookback:] if len(self.metrics) >= lookback else self.metrics
        prices = [metric["price"] for metric in past_metrics]
        rsi_values = [metric[rsi_key[0]][rsi_key[1]] for metric in past_metrics]

        # Append latest values
        rsi_values.append(latest_rsi)
        latest_price = self.price_data[-1]["value"] if self.price_data else prices[-1]
        prices.append(latest_price)

        # Convert to numpy arrays, handle None values
        price_array = np.array(prices)
        rsi_array = np.array(rsi_values) if latest_rsi is not None and all(v is not None for v in rsi_values) else None

        if rsi_array is None:
            return 0.0

        # Calculate ranges for normalization
        price_range = np.max(price_array) - np.min(price_array) if len(price_array) > 1 else 1.0
        rsi_range = np.max(rsi_array) - np.min(rsi_array) if len(rsi_array) > 1 else 1.0

        # Find peaks and troughs with configurable peak_distance
        price_highs_idx, _ = find_peaks(price_array, distance=peak_distance)
        price_lows_idx, _ = find_peaks(-price_array, distance=peak_distance)
        rsi_highs_idx, _ = find_peaks(rsi_array, distance=peak_distance)
        rsi_lows_idx, _ = find_peaks(-rsi_array, distance=peak_distance)

        # Check if enough points for divergence
        if len(price_highs_idx) < 2 or len(price_lows_idx) < 2 or len(rsi_highs_idx) < 2 or len(rsi_lows_idx) < 2:
            return 0.0

        # Strength calculation
        def calc_strength(price1, price2, rsi1, rsi2, price_range, rsi_range):
            price_diff = abs(price1 - price2) / price_range
            rsi_diff = abs(rsi1 - rsi2) / rsi_range
            raw_strength = rsi_diff / (price_diff + 1e-6)  # Divergence ratio
            strength = 2 / (1 + np.exp(-raw_strength)) - 1  # Sigmoid scaling to -1 to 1
            return min(1.0, max(-1.0, strength))

        # Initialize strength
        strength = 0.0

        # Bullish divergence: Lower price lows, higher RSI lows
        if len(price_lows_idx) >= 2 and len(rsi_lows_idx) >= 2:
            p_idx1, p_idx2 = price_lows_idx[-2], price_lows_idx[-1]
            price_low1, price_low2 = price_array[p_idx1], price_array[p_idx2]
            r_idx1 = min(rsi_lows_idx, key=lambda x: abs(x - p_idx1))
            r_idx2 = min(rsi_lows_idx, key=lambda x: abs(x - p_idx2))
            rsi_low1, rsi_low2 = rsi_array[r_idx1], rsi_array[r_idx2]

            if price_low1 > price_low2 and rsi_low1 < rsi_low2:
                strength = calc_strength(price_low1, price_low2, rsi_low1, rsi_low2, price_range, rsi_range)
                if rsi_low2 < 30:  # Boost in oversold region
                    strength = min(1.0, strength + (1.0 - strength) * 0.5)

        # Bearish divergence: Higher price highs, lower RSI highs
        if len(price_highs_idx) >= 2 and len(rsi_highs_idx) >= 2:
            p_idx1, p_idx2 = price_highs_idx[-2], price_highs_idx[-1]
            price_high1, price_high2 = price_array[p_idx1], price_array[p_idx2]
            r_idx1 = min(rsi_highs_idx, key=lambda x: abs(x - p_idx1))
            r_idx2 = min(rsi_highs_idx, key=lambda x: abs(x - p_idx2))
            rsi_high1, rsi_high2 = rsi_array[r_idx1], rsi_array[r_idx2]

            if price_high1 < price_high2 and rsi_high1 > rsi_high2:
                strength = -calc_strength(price_high1, price_high2, rsi_high1, rsi_high2, price_range, rsi_range)
                if rsi_high2 > 70:  # Boost in overbought region
                    strength = max(-1.0, strength - (1.0 + strength) * 0.5)

        return strength
    
    def analyze_rsi_crossovers(self, latest_rsi_short, latest_rsi_long, short_key=["rsi", "short"], long_key=["rsi", "long"], lookback=5):
        """
        Analyzes RSI crossovers between short and long RSI values.

        Args:
            latest_rsi_short (float): Latest value of the short-period RSI.
            latest_rsi_long (float): Latest value of the long-period RSI.
            short_key (list): Nested key for short RSI in metrics (e.g., ["rsi", "short"]).
            long_key (list): Nested key for long RSI in metrics (e.g., ["rsi", "long"]).
            lookback (int): Number of past periods to check for crossover (default: 5).

        Returns:
            int: 1 (bullish crossover), -1 (bearish crossover), 0 (no crossover).
        """
        # Need at least 2 points (current and previous) to detect a crossover
        if not self.metrics or len(self.metrics) < 1:
            return 0

        # Extract lookback period from metrics
        past_metrics = self.metrics[-lookback:] if len(self.metrics) >= lookback else self.metrics
        rsi_short_values = [metric[short_key[0]][short_key[1]] for metric in past_metrics]
        rsi_long_values = [metric[long_key[0]][long_key[1]] for metric in past_metrics]

        # Append latest values
        rsi_short_values.append(latest_rsi_short)
        rsi_long_values.append(latest_rsi_long)

        # Ensure we have at least 2 points
        if len(rsi_short_values) < 2:
            return 0

        # Check for crossover between the last two points
        prev_short, curr_short = rsi_short_values[-2], rsi_short_values[-1]
        prev_long, curr_long = rsi_long_values[-2], rsi_long_values[-1]

        # Bullish crossover: short RSI crosses above long RSI
        if prev_short <= prev_long and curr_short > curr_long:
            return 1
        # Bearish crossover: short RSI crosses below long RSI
        elif prev_short >= prev_long and curr_short < curr_long:
            return -1
        # No crossover
        else:
            return 0
    
def normalize_ema_relative_to_price(ema_value, price):
    """Normalize EMA value relative to current price."""
    if ema_value == 0 or ema_value is None:
        return None  # Avoid division by zero
    return price / ema_value