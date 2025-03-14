import pandas as pd

class MetricAnalyzer:
    def __init__(self, min_interval):
        """Initialize the metric analyzer with price data and the smallest sampling interval."""
        self.price_data = None  # Historical price data to be appended
        self.min_interval = min_interval  # The smallest sampling interval (e.g., 1m, 5m, 15m, etc.)
        self.intervals_available_for_calculation = []  # List of intervals that can be calculated
        
        # Define the available intervals and the conversion map
        self.available_intervals = {
            "1m": 1,
            "5m": 5,
            "15m": 15,
            "30m": 30,
            "1h": 60,
            "4h": 240,
            "12h": 720,
            "1d": 1440,
            "3d": 4320,
            "1w": 10080
        }
    
    def _generate_intervals_to_calculate(self):
        """Generate the list of intervals to calculate based on the available price data."""
        self.intervals_available_for_calculation = []  # Reset before calculating

        if self.price_data is None or len(self.price_data) == 0:
            return  # No data, no intervals can be calculated

        min_interval_minutes = self.available_intervals[self.min_interval]
        available_data_points = len(self.price_data)

        # Determine which intervals can be calculated based on the available data points
        for interval, minutes in self.available_intervals.items():
            if minutes % min_interval_minutes == 0:
                possible_intervals = available_data_points / (minutes / min_interval_minutes)
                if possible_intervals >= 15:  # Ensure at least 15 data points for calculations
                    self.intervals_available_for_calculation.append((interval, minutes))
        
        

    def calculate_metrics_for_intervals(self, ema_periods=[5, 15, 50, 200]):
        """Calculates RSI and different EMAs for all the calculated intervals."""
        if not self.intervals_available_for_calculation:
            return None

        metrics = {}
        min_interval_minutes = self.available_intervals[self.min_interval]

        for interval, interval_minutes in self.intervals_available_for_calculation:
            step = interval_minutes // min_interval_minutes  # How many smaller intervals to skip
            
            # Fetch the required data points for each metric
            ema_periods = ema_periods

            for period in ema_periods:
                required_points = period  # EMA needs at least `period` number of points
                interval_data = self.price_data[::-1][::step][:required_points][::-1]

                if len(interval_data) < required_points:
                    continue  # Skip calculation if we don't have enough data

                ema_value = self.calculate_ema(interval_data, required_points)
                metrics[f"{period}-Point-EMA_{interval}"] = ema_value

            # Always calculate RSI with 15 points
            required_points = 15
            interval_data = self.price_data[::-1][::step][:required_points][::-1]
            if len(interval_data) >= required_points:
                rsi = self.calculate_rsi(interval_data, required_points)
                metrics[f"RSI_{interval}"] = rsi

        return metrics
    
    def calculate_rsi(self, price_data, period):
        """Calculate the RSI (Relative Strength Index) for a given price data."""
        price_series = pd.Series([x['value'] for x in price_data])
        delta = price_series.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]  # Return the latest RSI value

    def calculate_ema(self, price_data, period):
        """Calculate the Exponential Moving Average (EMA) for a given price data."""
        price_series = pd.Series([x['value'] for x in price_data])
        
        # Calculate the EMA using pandas' built-in ewm (exponentially weighted moving average) function
        ema = price_series.ewm(span=period, adjust=False).mean()
        return ema.iloc[-1]  # Return the latest EMA value
    
    def update_price_data(self, new_price_data):
        """Update the price data with a new dataset and determine intervals that can be calculated."""
        self.price_data = new_price_data
        self._generate_intervals_to_calculate()




class MetricAnalyzer_2:
    def __init__(self, min_interval, price_data=[]):
        self.min_interval = min_interval
        self.price_data = price_data
        self.ema_values = {}
        self.rsi_values = {}
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

        return rsi

    def calculate_ema_crossovers(self, short_ema, long_ema, interval, lookback=5):
        if interval not in self.available_intervals:
            return None

        step = self.available_intervals[interval] // self.available_intervals[self.min_interval]
        prices = list(self.price_data)[-lookback * step::step]

        if len(prices) < lookback:
            return None

        short_ema_values = [self.calculate_ema(interval, short_ema) for _ in range(lookback)]
        long_ema_values = [self.calculate_ema(interval, long_ema) for _ in range(lookback)]

        if None in short_ema_values or None in long_ema_values:
            return None

        crossovers = [None] * lookback
        for i in range(1, lookback):
            if short_ema_values[i - 1] <= long_ema_values[i - 1] and short_ema_values[i] > long_ema_values[i]:
                crossovers[i] = 1
            elif short_ema_values[i - 1] >= long_ema_values[i - 1] and short_ema_values[i] < long_ema_values[i]:
                crossovers[i] = 0

        return crossovers
