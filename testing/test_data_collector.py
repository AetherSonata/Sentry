from testing.utils import fetch_complete_test_data, load_historical_price, save_historical_price
from analytics.price_analytics import MetricAnalyzer
from analytics.chart_analyzer import ChartAnalyzer
import numpy as np

TOKEN_ADDRESS = "9m3nh7YDoF1WSYpNxCjKVU8D1MrXsWRic4HqRaTdcTYB"

MIN_INTERVAL = "5m"    # birdeye fetching max 1000 data points of historic data
SPAN_IN_DAYS = 20

class TestDataCollector:
    def __init__(self, token_address, interval):
        self.token_address = token_address
        self.interval = interval
        self.interval_in_minutes = self.get_interval_in_minutes(interval)
        self.ohlcv_price_data = self.collect_historic_ohlcv_price_data()
        self.metrics = None

        self.mock_real_time_data_feed = None

    
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

    def collect_historic_ohlcv_price_data(self):
        try: 
            ohlcv_price_data = load_historical_price(filename= f"\chart_data\histocal_price_data_{self.token_address}_{self.interval}_{SPAN_IN_DAYS}_ohlcv.json")
        except Exception as e:
            print(f"Error loading data: {e}")
        
        if not self.ohlcv_price_data:
            print("no data found, fetching from API")
            ohlcv_price_data = fetch_complete_test_data(self.token_address, MIN_INTERVAL, SPAN_IN_DAYS, ohlcv=True)
            print("Data fetched from API.")
            try:
                save_historical_price(ohlcv_price_data, filename= f"\chart_data\histocal_price_data_{self.token_address}_{self.interval}_{SPAN_IN_DAYS}_ohlcv.json")
            except Exception as e:
                print(f"Error saving data: {e}")

        return ohlcv_price_data
        
    def calculate_price_momentum(self, i, span_in_minutes):
        """Calculates relative momentum (price change percentage) for a given span in minutes."""

        num_candles = span_in_minutes // self.minutes  # Convert minutes to number of candles

        if num_candles >= i:  # Not enough historical data available
            return None

        current_price = self.ohlcv_price_data[i]["close"]
        past_price = self.ohlcv_price_data[i - num_candles]["close"]  # Get the past price for the interval

        # Calculate momentum (percentage change)
        momentum = ((current_price - past_price) / past_price) * 100

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

    def calculate_ema_rsi_metrics(self):
        metric_analyzer = MetricAnalyzer(MIN_INTERVAL)
        metric_analyzer.update_price_data(self.ohlcv_price_data)
        metrics = metric_analyzer.calculate_metrics_for_intervals([5,15,50,200])


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
    
    def calculate_ema_slopes(self, ema_type, timeframe, n):
        # Ensure the requested EMA type and timeframe are valid
        valid_ema_types = ["5-point-ema", "15-point-ema", "50-point-ema"]
        valid_timeframes = ["5", "15", "30"]
        
        if ema_type not in valid_ema_types or timeframe not in valid_timeframes:
            raise ValueError(f"Invalid ema_type or timeframe: {ema_type}, {timeframe}")

        # Get the last `n` metrics from the list
        last_n_metrics = self.metrics[-n:]

        # List to store EMA values for the given type and timeframe
        ema_values = [metric[ema_type][timeframe] for metric in last_n_metrics]

        # Ensure we have enough data to calculate slope
        if len(ema_values) < 2:
            return None  # Can't calculate slope with less than 2 points

        # Calculate the slope as the difference between the most recent and the earliest EMA value
        slope = (ema_values[-1] - ema_values[0]) / (n - 1)  # Change in value per step

        # Return the calculated slope
        return {f"{ema_type}_{timeframe}_slope": slope}
    
    def calculate_ema_crossovers(self, short_ema, long_ema, timeframe, n):
        """
        Calculates EMA crossovers for the last `n` metrics.

        Args:
            short_ema (str): The key for the shorter EMA (e.g., "5-point-ema").
            long_ema (str): The key for the longer EMA (e.g., "15-point-ema").
            timeframe (str): The timeframe to check crossovers (e.g., "5", "15", "30").
            n (int): The number of recent candles to analyze.

        Returns:
            list: A list of length `n` with values:
                - 1 (bullish crossover)
                - 0 (bearish crossover)
                - None (no crossover)
        """

        # Get the last `n` metrics from the list
        last_n_metrics = self.metrics[-n:]

        # Ensure there is enough data to process
        if len(last_n_metrics) < 2:
            return [None] * len(last_n_metrics)  # Return all None if not enough data

        crossovers = [None] * len(last_n_metrics)  # Initialize list with None

        # Extract EMA values
        short_ema_values = [metric[short_ema][timeframe] for metric in last_n_metrics]
        long_ema_values = [metric[long_ema][timeframe] for metric in last_n_metrics]

        # Loop through and check crossovers
        for i in range(1, len(last_n_metrics)):  # Start from the second value to compare with the previous one
            prev_short = short_ema_values[i - 1]
            prev_long = long_ema_values[i - 1]
            curr_short = short_ema_values[i]
            curr_long = long_ema_values[i]

            if prev_short <= prev_long and curr_short > curr_long:
                crossovers[i] = 1  # Bullish crossover

            elif prev_short >= prev_long and curr_short < curr_long:
                crossovers[i] = 0  # Bearish crossover

        return crossovers




    def collect_all_metrics_and_store(self):
        for i in range(0, len(self.ohlcv_price_data)):
            self.mock_real_time_data_feed = self.ohlcv_price_data[i]
            current_metric = METRIC_POINT
            current_metric["price_close"] = self.mock_real_time_data_feed["c"]
            current_metric["avg_price"] = (self.mock_real_time_data_feed["h"] + self.mock_real_time_data_feed["l"]) / 2
            current_metric["price_high"] = self.mock_real_time_data_feed["h"]
            current_metric["price_low"] = self.mock_real_time_data_feed["l"]
            current_metric["price_open"] = self.mock_real_time_data_feed["o"]
            current_metric["last_20_prices"] = self.collect_last_20_prices(i)
        
            current_metric["volume"]["current_volume"] = self.mock_real_time_data_feed["v"]
            current_metric["volume"]["avg_volume_last_10_candles"] = self.calculate_avg_volume(i, 10)
            current_metric["volume"]["avg_volume_last_50_candles"] = self.calculate_avg_volume(i, 50)
            current_metric["volume"]["avg_volume_last_100_candles"] = self.calculate_avg_volume(i, 100)
            current_metric["volume"]["volume_change_percentage"]["5"] = self.calculate_volume_change_percentage(i, 5)
            current_metric["volume"]["volume_change_percentage"]["15"] = self.calculate_volume_change_percentage(i, 15)
            current_metric["volume"]["volume_change_percentage"]["30"] = self.calculate_volume_change_percentage(i, 30)
            current_metric["volume"]["volume_change_percentage"]["60"] = self.calculate_volume_change_percentage(i, 60)
            current_metric["volume"]["volume_change_percentage"]["120"] = self.calculate_volume_change_percentage(i, 120)
            current_metric["volume"]["volume_change_percentage"]["240"] = self.calculate_volume_change_percentage(i, 240)

            current_metric["VWAP_last_10_candles"] = self.calculate_vwap(10, i)
            current_metric["VWAP_last_50_candles"] = self.calculate_vwap(50, i)

            chart_analyzer = ChartAnalyzer(self.ohlcv_price_data[:i+1], self.interval)
            current_metric["support_resistances"] = chart_analyzer.find_support_resistance_zones()["support_zones"]

            current_metric["price_change_percentage"]["5"] = self.calculate_price_momentum(i, 5)
            current_metric["price_change_percentage"]["15"] = self.calculate_price_momentum(i, 15)
            current_metric["price_change_percentage"]["30"] = self.calculate_price_momentum(i, 30)
            current_metric["price_change_percentage"]["60"] = self.calculate_price_momentum(i, 60)
            current_metric["price_change_percentage"]["120"] = self.calculate_price_momentum(i, 120)
            current_metric["price_change_percentage"]["240"] = self.calculate_price_momentum(i, 240)

            current_metric["volatility"]["20_candles"] = self.calculate_volatility(i, 20)
            current_metric["volatility"]["50_candles"] = self.calculate_volatility(i, 50)

            metric_analyzer = MetricAnalyzer(self.ohlcv_price_data[:i+1], self.interval)
            price_metrics = metric_analyzer.calculate_metrics_for_intervals()

            current_metric["ema"]["5-point-ema"]["5"] = price_metrics["5-Point-EMA-5m"]
            current_metric["ema"]["15-point-ema"]["5"] = price_metrics["15-Point-EMA-5m"]
            current_metric["ema"]["50-point-ema"]["5"] = price_metrics["50-Point-EMA-5m"]

            current_metric["ema"]["5-point-ema"]["15"] = price_metrics["5-Point-EMA-15m"]
            current_metric["ema"]["15-point-ema"]["15"] = price_metrics["15-Point-EMA-15m"]
            current_metric["ema"]["50-point-ema"]["15"] = price_metrics["50-Point-EMA-15m"]

            current_metric["ema"]["5-point-ema"]["30"] = price_metrics["5-Point-EMA-30m"]  
            current_metric["ema"]["15-point-ema"]["30"] = price_metrics["15-Point-EMA-30m"]
            current_metric["ema"]["50-point-ema"]["30"] = price_metrics["50-Point-EMA-30m"]

            current_metric["ema"]["ema_slope_5min"]["5"]["5_candles"] = self.calculate_ema_slopes("5-point-ema", "5", 5)
            current_metric["ema"]["ema_slope_5min"]["15"]["5_candles"] = self.calculate_ema_slopes("15-point-ema", "5", 5)
            current_metric["ema"]["ema_slope_5min"]["50"]["5_candles"] = self.calculate_ema_slopes("50-point-ema", "5", 5)

            current_metric["ema"]["ema_slope_15min"]["5"]["5_candles"] = self.calculate_ema_slopes("5-point-ema", "15", 5)
            current_metric["ema"]["ema_slope_15min"]["15"]["5_candles"] = self.calculate_ema_slopes("15-point-ema", "15", 5)
            current_metric["ema"]["ema_slope_15min"]["50"]["5_candles"] = self.calculate_ema_slopes("50-point-ema", "15", 5)
            current_metric["ema"]["ema_slope-15min"]["5"]["10_candles"] = self.calculate_ema_slopes("5-point-ema", "15", 10)

            current_metric["ema"]["ema_slope_30min"]["5"]["5_candles"] = self.calculate_ema_slopes("5-point-ema", "30", 5)
            current_metric["ema"]["ema_slope_30min"]["15"]["5_candles"] = self.calculate_ema_slopes("15-point-ema", "30", 5)
            current_metric["ema"]["ema_slope_30min"]["50"]["5_candles"] = self.calculate_ema_slopes("50-point-ema", "30", 5)

            current_metric["ema"]["ema_crossovers"]["ema-5-15"]["10_candles"] = self.calculate_ema_crossovers("5-point-ema", "15-point-ema", "5", 10)
            current_metric["ema"]["ema_crossovers"]["ema-5-15"]["5_candles"] = self.calculate_ema_crossovers("5-point-ema", "15-point-ema", "15", 10)
            current_metric["ema"]["ema_crossovers"]["ema-5-15"]["5_candles"] = self.calculate_ema_crossovers("5-point-ema", "15-point-ema", "30", 10)

            current_metric["ema"]["ema_crossovers"]["ema-15-50"]["10_candles"] = self.calculate_ema_crossovers("15-point-ema", "50-point-ema", "5", 10)
            current_metric["ema"]["ema_crossovers"]["ema-15-50"]["5_candles"] = self.calculate_ema_crossovers("15-point-ema", "50-point-ema", "15", 10)
            current_metric["ema"]["ema_crossovers"]["ema-15-50"]["5_candles"] = self.calculate_ema_crossovers("15-point-ema", "50-point-ema", "30", 10)

            current_metric["rsi"]["current_rsi"]["rsi-5"]["5_min"] = price_metrics["5-RSI-5m"]
            current_metric["rsi"]["current_rsi"]["rsi-5"]["15_min"] = price_metrics["5-RSI-15m"]
            current_metric["rsi"]["current_rsi"]["rsi-15"]["5_min"] = price_metrics["5-RSI-5m"]
            current_metric["rsi"]["current_rsi"]["rsi-15"]["15_min"] = price_metrics["15-RSI-5m"]
            current_metric["rsi"]["current_rsi"]["rsi-15"]["30_min"] = price_metrics["15-RSI-30m"]
            current_metric["rsi"]["current_rsi"]["rsi-15"]["60_min"] = price_metrics["15-RSI-60m"]

            current_metric["rsi"]["rsi_slope"]["rsi-5"]["5_candles"] = self.calculate_rsi_slopes("rsi-5", "5", 5)
            current_metric["rsi"]["rsi_slope"]["rsi-15"]["5_candles"] = self.calculate_rsi_slopes("rsi-15", "5", 5)

            current_metric["rsi"]["rsi_divergence"]["rsi-5"] = self.calculate_rsi_divergence("rsi-5", 5) #returns divergence direction and strength
            current_metric["rsi"]["rsi_divergence"]["rsi-15"] = self.calculate_rsi_divergence("rsi-15", 5)
            current_metric["rsi"]["rsi_divergence"]["rsi-15"] = self.calculate_rsi_divergence("rsi-15", 15)
            current_metric["rsi"]["rsi_divergence"]["rsi-15"] = self.calculate_rsi_divergence("rsi-15", 30)

            current_metric["additional_metrics"] = self.cal




            self.metrics.append(current_metric)
            print(f"Metrics collected for index {i}")






METRIC_POINT = {
    # Price-related features
    "price_close": None,
    "price_open": None,
    "price_high": None,
    "price_low": None,
    "avg_price": None,
    "last_20_prices": [],  # A smaller historical window for quick reactions

    # Volume-related features
    "volume": {
        "current_volume": None,
        "avg_volume_last_10_candles": None,
        "avg_volume_last_50_candles": None,
        "avg_volume_last_100_candles": None,
        "volume_change_percentage": {
            "5": None, "15": None, "30": None, "60": None, "120": None, "240": None
        }
    },

    # Price-Volume weighted average price
    "VWAP_last_10_candles": None,
    "VWAP_last_50_candles": None,

    # Support and resistance levels (with strength indicating how often they've been tested)
    "support_resistance": None,

    # Relative momentum (price change percentages) for various spans
    "price_change_percentage": {
        "5": None, "15": None, "30": None, "60": None, "120": None, "240": None
    },

    # Volatility (using standard deviation of the last 20 and 50 candles)
    "volatility": {
        "20_candles": None, "50_candles": None
    },

    # EMA-related features
    "ema": {
        "current_ema": {
            "ema-5": None,
            "ema-15": None,
            "ema-50": None,
            "ema-200": None
        },
        "ema_slope": {
            # Using a 5-candle lookback for the short-term EMAs; for longer-term, a 10-candle slope may be more stable.
            "ema-5": {"5_candles": None},
            "ema-15": {"5_candles": None},
            "ema-50": {"5_candles": None, "10_candles": None},
        },
        "ema_crossovers": {
            # Only using 5 and 10 candle lookbacks for crossovers to capture quick shifts
            "ema-5-15": {"5_candles": None, "10_candles": None},
            "ema-15-50": {"5_candles": None, "10_candles": None}, 
        }
    },

    # RSI-related features (focusing on more responsive timeframes)
    "rsi": {
        "current_rsi": {
            # Use 5-minute RSI for very responsive signals and 15-minute RSI for a slightly broader view.
            "rsi-5": {"5_min": None},
            "rsi-15": {"15_min": None}
        },
        "rsi_slope": {
            "rsi-5": {"5_candles": None},
            "rsi-15": {"5_candles": None}
        },
        "rsi_divergence": {
            # For divergence, include a lookback (which can be dynamic) and signal strength.
            "rsi-5": {"divergence_direction": None, "divergence_strength": None, "lookback": None},
            "rsi-15": {"divergence_direction": None, "divergence_strength": None, "lookback": None}
        }
    }
}


    

    

