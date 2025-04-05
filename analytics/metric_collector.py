from analytics.indicator_analytics import IndicatorAnalyzer, normalize_ema_relative_to_price
from analytics.chart_analytics import ChartAnalyzer, normalize_zones
from analytics.price_analytics import PriceAnalytics
from analytics.time_utils import get_interval_in_minutes, get_time_features, calculate_token_age
from analytics.fibonacci_analyzer import FibonacciAnalyzer
from interpretation.confidence import ConfidenceCalculator
from analytics.zones import ZoneAnalyzer

class MetricCollector:
    def __init__(self, interval):
        self.interval = interval
        self.interval_in_minutes = get_interval_in_minutes(interval)
        self.price_data = []  # List of dicts: [{"value": price, "unixTime": ts}, ...]
        self.metrics = []

        self.key_zone_1 = []
        self.key_zone_2 = []
        self.key_zone_3 = []
        self.key_zone_4 = []
        self.key_zone_5 = []
        self.key_zone_6 = []

        self.indicator_analyzer = IndicatorAnalyzer(self)
        self.chart_analyzer = ChartAnalyzer(interval)
        self.price_analyzer = PriceAnalytics()
        self.fibonacci_analyzer = FibonacciAnalyzer(self)
        self.zone_analyzer = ZoneAnalyzer(self)
        self.confidence_calculator = ConfidenceCalculator(self,  
                                                          alpha=0.08, 
                                                          threshold=0.1, 
                                                          decay_rate=0.05)
        self.confidence_settings = self.confidence_calculator



    def add_new_price_point_and_calculate_metrics(self, new_price_point):
        self.price_data.append(new_price_point)
        self.chart_analyzer.append_price_data(new_price_point)
        self.price_analyzer.append(new_price_point)
        self.metrics.append(self.collect_all_metrics_for_current_point(len(self.price_data) - 1))
        

    def collect_all_metrics_for_current_point(self, i):
        current_price = self.price_data[-1]["value"]

        # Calculate window sizes
        quarter_window = max(50, len(self.price_data) // 4)  # Short-term
        half_window = max(50, len(self.price_data) // 2)     # Mid-term
        three_quarters_window = max(200, len(self.price_data) // 4 * 3)  # Mid-term
        full_window = max(200, len(self.price_data))          # Long-term
        #4/5th of the data
        four_fifth_window = max(200, len(self.price_data) // 5 * 4)  # Mid-term


        # Short-term zones (intraday, quick moves)
        self.key_zone_1, self.key_zone_2 = self.zone_analyzer.get_dynamic_zones(
            window=quarter_window,
            zone_type="short_term"
        )

        # Mid-term zones (balanced intraday and swing)
        self.key_zone_3, self.key_zone_4 = self.zone_analyzer.get_dynamic_zones(
            window=half_window,
            zone_type="mid_term"
        )

        # Long-term zones (swing, significant moves)
        self.key_zone_5, self.key_zone_6 = self.zone_analyzer.get_dynamic_zones(
            window=four_fifth_window,
            zone_type="long_term"
        )

        # self.confidence_calculator.settings.set_parameters(                
        #     "key_zone_1", alpha=0.25, threshold=0.11, decay_rate=0.15     # Green Zone 1 tweaks "SHORT TERM SUPPORT"
        # )

        self.confidence_calculator.settings.set_parameters(                
            "key_zone_2", alpha=0.2, threshold=0.15, decay_rate=0.15     # Red Zone 2 tweaks "SHORT TERM WEAK RESISTANCE"
        )

        self.confidence_calculator.settings.set_parameters(                
            "key_zone_5", alpha=0.15, threshold=0.30, decay_rate=0.08     # Brown Zone 5 tweaks "STRONG SUPPORT"
        )


        time_features = get_time_features(self.price_data[-1]["unixTime"])  # Corrected to use last price data point

        # Pre-compute dependent values
        momentum_short = self.price_analyzer.calculate_price_momentum(15, 5) #span in min / interval in min  
        momentum_medium = self.price_analyzer.calculate_price_momentum(60, 5) #span in min / interval in min 
        momentum_long = self.price_analyzer.calculate_price_momentum(240, 5) #span in min / interval in min
        
        data_idx = len(self.price_data) - 1  # Always use the end of price_data
        pseudo_atr = (self.price_analyzer.calculate_pseudo_atr(data_idx, 14) / current_price * 100) if current_price != 0 else 0.0
        volatility_short = (self.price_analyzer.calculate_volatility(data_idx, 6) / current_price * 100) if current_price != 0 else 0.0

        rsi_short = self.indicator_analyzer.calculate_rsi("5m", 15)
        rsi_middle_short = self.indicator_analyzer.calculate_rsi("15m", 15)
        rsi_long = self.indicator_analyzer.calculate_rsi("1h", 15)
        rsi_slope = self.indicator_analyzer.calculate_indicator_slopes("RSI", "5m", 6) # in class IndicatorAnalyzer
        
        ema_short = self.indicator_analyzer.calculate_ema("5m", 10)
        ema_medium = self.indicator_analyzer.calculate_ema("5m", 50)
        ema_long = self.indicator_analyzer.calculate_ema("5m", 100)
        ema_longterm = self.indicator_analyzer.calculate_ema("5m", 200)

        sma_short = self.indicator_analyzer.calculate_sma("1h", 5)
        sma_medium = self.indicator_analyzer.calculate_sma("1h", 10)
        sma_long = self.indicator_analyzer.calculate_sma("1h", 20)

        boilinger_bands = self.indicator_analyzer.calculate_bollinger_bands("1h", 20, 2, sma_long)
 

        normalized_ema_short = normalize_ema_relative_to_price(ema_short, current_price)
        normalized_ema_medium = normalize_ema_relative_to_price(ema_medium, current_price)
        normalized_ema_long = normalize_ema_relative_to_price(ema_long, current_price)
        normalized_ema_longterm = normalize_ema_relative_to_price(ema_longterm, current_price)

        # Extract EMA histories from MetricCollectoss self.metrics
        short_ema_values = [m["ema"]["short"] for m in self.metrics if "ema" in m and "short" in m["ema"]][-5:]
        medium_ema_values = [m["ema"]["medium"] for m in self.metrics if "ema" in m and "medium" in m["ema"]][-5:]
        medium_ema_values11 = [m["ema"]["long"] for m in self.metrics if "ema" in m and "medium" in m["ema"]][-11:]
        long_ema_values = [m["ema"]["longterm"] for m in self.metrics if "ema" in m and "long" in m["ema"]][-11:]

        crossover_short_medium = self.indicator_analyzer.calculate_ma_crossovers(
            short_ema_values, medium_ema_values, ema_short, ema_medium
        )
        crossover_medium_long = self.indicator_analyzer.calculate_ma_crossovers(
            medium_ema_values11, long_ema_values, ema_medium, ema_long
        )

        rsi_divergence_signal = self.indicator_analyzer.analyze_rsi_divergence(
            latest_rsi=rsi_long,
            rsi_key= ["rsi", "long"],
            lookback=100,
            peak_distance=15
        )

        macd = self.indicator_analyzer.calculate_macd("1h")
        # print(macd)

        self.fibonacci_analyzer.recalculate()
        print(self.fibonacci_analyzer.fib_levels)

        # Build and return metrics dict
        return {
            "price": current_price,
            "momentum": {
                "short": momentum_short,
                "medium": momentum_medium,
                "long": momentum_long,
            },
            "volatility": {
                "pseudo_atr": pseudo_atr,
                "short": volatility_short,
            },
            "rsi": {
                "short": rsi_short,
                "middle_short": rsi_middle_short,
                "long": rsi_long,
                "slope": rsi_slope,
            },
            "ema": {
                "short": normalized_ema_short,
                "medium": normalized_ema_medium,
                "long": normalized_ema_long,
                "longterm": normalized_ema_longterm,
                "crossover_short_medium": crossover_short_medium,
                "crossover_medium_long": crossover_medium_long,
            },
            "sma": {
                "short": sma_short,
                "medium": sma_medium,
                "long": sma_long,
            },
            "divergence": rsi_divergence_signal,

            "boilinger_bands": {
                "upper": boilinger_bands["upper_band"],
                "middle": boilinger_bands["middle_band"],
                "lower": boilinger_bands["lower_band"],
            },
            "macd": {
                "macd": macd["macd"],
                "signal": macd["signal"],
                "histogram": macd["histogram"],
            },

            "key_zone_1": self.key_zone_1,
            "key_zone_2": self.key_zone_2,
            "key_zone_3": self.key_zone_3,
            "key_zone_4": self.key_zone_4,
            "key_zone_5": self.key_zone_5,
            "key_zone_6": self.key_zone_6,
            "token_age": calculate_token_age(self.price_data) / 1440,
            "peak_distance": self.chart_analyzer.calculate_peak_distance(),
            "drawdown_tight": self.chart_analyzer.calculate_drawdown(3, 288)["short"],
            "drawdown_short": self.chart_analyzer.calculate_drawdown(12, 288)["short"],
            "drawdown_long": self.chart_analyzer.calculate_drawdown(12, 288)["long"],
            "zone_confidence": self.confidence_calculator.calculate_zone_confidence(current_price),
            "zone_confidence_slope": self.confidence_calculator.calculate_confidence_slope(),      
            "time": {
                "minute_of_day": time_features["minute_of_day"],
                "day_of_week": time_features["day_of_week"],
            }
        }

    
   