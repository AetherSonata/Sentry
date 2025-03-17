from analytics.indicator_analytics import IndicatorAnalyzer, normalize_ema_relative_to_price
from analytics.chart_analytics import ChartAnalyzer, normalize_zones
from analytics.price_analytics import PriceAnalytics
from analytics.time_utils import get_interval_in_minutes, get_time_features, calculate_token_age
from analytics.fibonacci_analyzer import FibonacciAnalyzer

class MetricCollector:
    def __init__(self, interval, historical_price_data):
        self.interval = interval
        self.interval_in_minutes = get_interval_in_minutes(interval)
        self.price_data = historical_price_data  # List of dicts: [{"value": price, "unixTime": ts}, ...]

        self.indicator_analyzer = IndicatorAnalyzer(interval)
        self.chart_analyzer = ChartAnalyzer(interval)
        self.price_analyzer = PriceAnalytics()
        self.fibonacci_analyzer = FibonacciAnalyzer(interval)

        self.zones = []  # Support and resistance zones

        self.metrics = []
        if historical_price_data:
            self.initialize_prior_metrics()


    def initialize_prior_metrics(self):
        # Process all historical data without appending—already in self.price_data
        for i in range(len(self.price_data)):
            self.indicator_analyzer.append_price(self.price_data[i])
            self.chart_analyzer.append_price_data(self.price_data[i])
            self.price_analyzer.append(self.price_data[i])
            self.fibonacci_analyzer.append_price_data(self.price_data[i])
            self.metrics.append(self.collect_all_metrics_for_current_point(i))

    def add_new_price_point_and_calculate_metrics(self, new_price_point):
        self.price_data.append(new_price_point)
        self.indicator_analyzer.append_price(new_price_point)
        self.chart_analyzer.append_price_data(new_price_point)
        self.price_analyzer.append(new_price_point)
        self.metrics.append(self.collect_all_metrics_for_current_point(len(self.price_data) - 1))

    def collect_all_metrics_for_current_point(self, i):
        current_price = self.price_data[-1]["value"]
        zones = self.chart_analyzer.find_key_zones(
            current_step=i,
            max_zones=6,
            volatility_window=20,
            filter_percentage=100
        )

        self.zones.append(zones)

        # Split zones based on current price
        support_zones_raw = [zone for zone in zones if zone["zone_level"] < current_price]
        resistance_zones_raw = [zone for zone in zones if zone["zone_level"] > current_price]

        # Normalize and filter zones 3 support and 3 resistance zones, sort them by proximity to current price
        support_zones = normalize_zones(support_zones_raw, current_price=current_price, max_zones=3, include_major_flag=True)
        resistance_zones = normalize_zones(resistance_zones_raw,current_price=current_price, max_zones=3, include_major_flag=True)

        # check fibonacci levels
        fib_match_step = self.fibonacci_analyzer.check_fibonacci_time_update()


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

        normalized_ema_short = normalize_ema_relative_to_price(ema_short, current_price)
        normalized_ema_medium = normalize_ema_relative_to_price(ema_medium, current_price)
        normalized_ema_long = normalize_ema_relative_to_price(ema_long, current_price)
        normalized_ema_longterm = normalize_ema_relative_to_price(ema_longterm, current_price)

        # Extract EMA histories from MetricCollectoss self.metrics
        short_ema_values = [m["ema"]["short"] for m in self.metrics if "ema" in m and "short" in m["ema"]][-5:]
        medium_ema_values = [m["ema"]["medium"] for m in self.metrics if "ema" in m and "medium" in m["ema"]][-5:]
        medium_ema_values11 = [m["ema"]["medium"] for m in self.metrics if "ema" in m and "medium" in m["ema"]][-11:]
        long_ema_values = [m["ema"]["long"] for m in self.metrics if "ema" in m and "long" in m["ema"]][-11:]

        crossover_short_medium = self.indicator_analyzer.calculate_ema_crossovers(
            short_ema_values, medium_ema_values, ema_short, ema_medium
        )
        crossover_medium_long = self.indicator_analyzer.calculate_ema_crossovers(
            medium_ema_values11, long_ema_values, ema_medium, ema_long
        )

        # Use past metrics (e.g., last 5 points) and append latest rsi_short
        lookback = 5  # 25 minutes, adjust as needed
        past_metrics = self.metrics[-lookback:] if len(self.metrics) >= lookback else self.metrics
        divergence = self.indicator_analyzer.analyze_rsi_divergence(
            past_metrics=past_metrics,
            latest_rsi=rsi_short,
            rsi_key= ["rsi", "short"],  # Use short-term RSI
            price_key="price"
        )

        # Prepare divergence for metrics dict
        divergence_signal = divergence["divergence_signal"] if divergence else None
        divergence_strength = divergence["divergence_strength"] if divergence else 0.0

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
            "divergence": {
                "signal": divergence_signal,
                "strength": divergence_strength,
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
            "token_age": calculate_token_age(self.price_data) / 1440,
            "peak_distance": self.chart_analyzer.calculate_peak_distance(),
            "drawdown_tight": self.chart_analyzer.calculate_drawdown(3, 288)["short"],
            "drawdown_short": self.chart_analyzer.calculate_drawdown(12, 288)["short"],
            "drawdown_long": self.chart_analyzer.calculate_drawdown(12, 288)["long"],
            "time": {
                "minute_of_day": time_features["minute_of_day"],
                "day_of_week": time_features["day_of_week"],
            "fibonacci_time_reversal": fib_match_step           
            }
        }

    
   