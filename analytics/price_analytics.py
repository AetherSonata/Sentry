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

    def calculate_metrics_for_intervals(self):
        """Calculates RSI and different EMAs for all the calculated intervals."""
        if not self.intervals_available_for_calculation:
            return None

        metrics = {}
        last_index = len(self.price_data) - 1
        min_interval_minutes = self.available_intervals[self.min_interval]

        for interval, interval_minutes in self.intervals_available_for_calculation:
            step = interval_minutes // min_interval_minutes  # How many smaller intervals to skip
            
            # Fetch the required data points for each metric
            ema_periods = [15, 50, 200]

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
