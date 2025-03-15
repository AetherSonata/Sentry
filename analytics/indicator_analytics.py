import pandas as pd


class IndicatorAnalyzer:
    def __init__(self, min_interval, price_data=[]):
        self.min_interval = min_interval
        self.price_data = price_data
        self.ema_values = {}
        self.rsi_values = {}
        self.metrics = []
        self.available_intervals = {
            "1m": 1, "5m": 5, "15m": 15, "30m": 30,
            "1h": 60, "4h": 240, "12h": 720,
            "1d": 1440, "3d": 4320, "1w": 10080
        }

    def append_price(self, new_price):
        self.price_data.append(new_price)

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

        self.metrics.append({key: new_ema}) # save in metrics for up to date calculations
        return new_ema

    def calculate_rsi(self, interval, period=15, avg_prev=False):
        
        if interval not in self.available_intervals:
            return None

        step = self.available_intervals[interval] // self.available_intervals[self.min_interval]
        prices = list(self.price_data)[-period * step::step]

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

        self.metrics.append({key : rsi})  # save in metrics for up to date calculations

        return rsi


    def calculate_indicator_slopes(self, metric_type, timeframe, n, averaged=True):
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
            return linear_slope


    def calculate_ema_crossovers(self, short_ema_list, long_ema_list, current_short, current_long):
        """
        Calculates EMA crossovers given lists of short and long EMA values plus current values.

        Args:
            short_ema_list (list): List of recent short EMA values (any length).
            long_ema_list (list): List of recent long EMA values (same length as short_ema_list).
            current_short (float): The newest short EMA value.
            current_long (float): The newest long EMA value.

        Returns:
            list: A list with length equal to input list length + 1, containing:
                - 1 (bullish crossover)
                - 0 (bearish crossover)
                - None (no crossover)
        """
        # Combine the input lists with the current values
        short_emas = short_ema_list + [current_short]
        long_emas = long_ema_list + [current_long]

        # Determine the output length based on input
        n = len(short_emas)

        # If less than 2 entries, return a list of None values
        if n < 2:
            return [None] * n

        # Initialize result list with None values
        crossovers = [None] * n

        # Check for crossovers over the available entries
        for i in range(1, n):
            prev_short = short_emas[i - 1]
            prev_long = long_emas[i - 1]
            curr_short = short_emas[i]
            curr_long = long_emas[i]

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
        if len(self.price_data) < n or len(self.metrics[rsi_type]) < n:
            return None

        # Look at the last `n` data points for divergence detection
        price_segment = self.mock_real_time_price_data[-n:]
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