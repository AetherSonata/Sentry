from testing.utils import fetch_complete_test_data, load_historical_price, save_historical_price
from analytics.price_analytics import MetricAnalyzer
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
    
    def calculate_and_collect_momentum(self, span_list=[5, 15, 30, 60, 120, 240]):
        """Calculates relative momentum for a list of spans (in minutes) and stores the results in self.metrics."""
        
        for span_in_minutes in span_list:
            num_candles = span_in_minutes // self.minutes  # Convert minutes to number of candles

            if num_candles >= len(self.ohlcv_price_data):
                self.metrics[f"{span_in_minutes}m_momentum"] = None  # Not enough data for this span
                continue  # Skip to the next span if not enough data

            current_price = self.ohlcv_price_data[-1]["close"]
            past_price = self.ohlcv_price_data[-num_candles]["close"]  # Get the past price for the interval

            # Calculate momentum
            momentum = ((current_price - past_price) / past_price) * 100

            # Store momentum in the metrics dictionary
            self.metrics[f"{span_in_minutes}m_momentum"] = momentum


    def calculate_volatility(self, window_sizes=[20, 50]):
        """Calculate the standard deviation (volatility) for custom window sizes and store in self.metrics."""
        prices = self.ohlcv_price_data['close']  # Extract the closing prices
        
        # Loop through the window sizes and calculate volatility
        for window_size in window_sizes:
            if len(prices) < window_size:
                self.metrics[f"volatility_{window_size}"] = None  # Not enough data
            else:
                # Calculate the standard deviation for the last `window_size` candles
                self.metrics[f"volatility_{window_size}"] = np.std(prices[-window_size:])

    def calculate_ema_rsi_metrics(self):
        metric_analyzer = MetricAnalyzer(MIN_INTERVAL)
        metric_analyzer.update_price_data(self.ohlcv_price_data)
        metrics = metric_analyzer.calculate_metrics_for_intervals([5,15,50,200])



metrics = {

            "price_open": None,
            "price_close": None,
            "price_high": None,
            "price_low": None,
            "current_volume": None,
            "50_previous_prices" : [],
            "price_change_percentage" : {
                "5" : None,
                "15" : None,
                "30" : None,
                "60" : None,
                "120" : None,
                "240" : None,
            },
            "volatility" : {
                "20_candles": None,
                "50_candles": None,
            },
            "ema": {
                "current_ema" : {
                    "ema-5": None,
                    "ema-15": None,
                    "ema-50": None,
                    "ema-200": None,
                },
                "ema_slope": {
                    "ema-5": {
                        "5_candles": None,
                        "10_candles": None},
                    "ema-15": {
                        "5_candles": None,
                        "10_candles": None},
                    "ema-50": {
                        "5_candles": None,
                        "10_candles": None},
                    "ema-200": {
                        "5_candles": None,
                        "10_candles": None},
                "ema_crossovers": {
                    "ema-5-15": {
                        "2_candles": None,
                        "5_candles": None,
                        "10_candles": None,
                        }  , 
                    "ema-15-50": {
                        "2_candles": None,
                        "5_candles": None,
                        "10_candles": None
                        },
                    "ema-50-200": {
                        "2_candles": None,
                        "5_candles": None,
                        "10_candles": None,
                    }
                },
            "rsi": {
                "current_rsi": {
                    "rsi-5": {
                        "5_min": None,
                        "15_min": None,
                        "30_min": None,
                        "60_min": None,
                        "120_min": None,
                        "240_min": None,
                    },
                    "rsi-15": {
                        "5_min": None,
                        "15_min": None,
                        "30_min": None,
                        "60_min": None,
                        "120_min": None,
                        "240_min": None,
                    },
                    "rsi-50": {
                        "5_min": None,
                        "15_min": None,
                        "30_min": None,
                        "60_min": None,
                        "120_min": None,
                        "240_min": None,
                    }
                    },
                    
            },


   }
        

    

    

