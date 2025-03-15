        
            
            
            
            
        #     {
        #         "price_close" : self.mock_real_time_data_feed["c"],
        #         "avg_price" : (self.mock_real_time_data_feed["h"] + self.mock_real_time_data_feed["l"]) / 2,
        #         "price_high" : self.mock_real_time_data_feed["h"],
        #         "price_low" : self.mock_real_time_data_feed["l"],
        #         "price_open" : self.mock_real_time_data_feed["o"],
        #         "last_20_prices" : self.collect_last_20_prices(i),
        #         "price_change_percentage_per_period" : {
        #             "5" : self.calculate_price_momentum(i, 5),
        #             "15" : self.calculate_price_momentum(i, 15),
        #             "30" : self.calculate_price_momentum(i, 30),
        #             "60" : self.calculate_price_momentum(i, 60),
        #             "120" : self.calculate_price_momentum(i, 120),
        #             "240" : self.calculate_price_momentum(i, 240),
        #         }, 
        #         "volatility" : {
        #             "20_candles" : self.calculate_volatility(i, 5),
        #             "50_candles" : self.calculate_volatility(i, 15),
        #         },
        #         "volume" : {
        #             "current_volume" : self.data_feed["v"],
        #             "avg_volume_last_10_candles" : self.calculate_avg_volume(i, 10),
        #             "avg_volume_last_50_candles" : self.calculate_avg_volume(i, 50),
        #             "avg_volume_last_100_candles" : self.calculate_avg_volume(i, 100),
        #             "avg_volume_last_200_candles" : self.calculate_avg_volume(i, 200),
        #         },
        #         "VWAP_last_10_candles" : self.calculate_vwap(10, i),
        #         "VWAP_last_50_candles" : self.calculate_vwap(50, i),
        #         "VWAP_last_100_candles" : self.calculate_vwap(100, i),
        #         "support_resistances" : self.chart_analyzer.find_support_resistance_zones(),
        #         "ema" : {
        #             "current_ema" : {
        #                 "5-point-ema" : {
        #                     "5" : MetricAnalyzer_2.calculate_ema("5m", "5-point-ema"),
        #                     "15" : MetricAnalyzer_2.calculate_ema("15m", "5-point-ema"),
        #                     "30" : MetricAnalyzer_2.calculate_ema("30m", "5-point-ema"),
        #                 },
        #                 "15-point-ema" : {
        #                     "5" : MetricAnalyzer_2.calculate_ema("5m", "15-point-ema"),
        #                     "15" : MetricAnalyzer_2.calculate_ema("15m", "15-point-ema"),
        #                     "30" : MetricAnalyzer_2.calculate_ema("30m", "15-point-ema"),
        #                 },
        #                 "50-point-ema" : {
        #                     "5" : MetricAnalyzer_2.calculate_ema("5m", "50-point-ema"),
        #                     "15" : MetricAnalyzer_2.calculate_ema("15m", "50-point-ema"),
        #                     "30" : MetricAnalyzer_2.calculate_ema("30m", "50-point-ema"),
        #                 },
        #             },
        #             "ema_slope" : {
        #                 "5-point-ema_slope" : {
        #                     "5" : self.calculate_metric_slopes("5m", "5-point-ema"),
        #                     "15" : self.calculate_metric_slopes("15m", "5-point-ema"),
        #                     "30" : self.calculate_metric_slopes("30m", "5-point-ema"),
        #                 },
        #                 "15-point-ema_slope" : {
        #                     "5" : self.calculate_metric_slopes("5m", "15-point-ema"),
        #                     "15" : self.calculate_metric_slopes("15m", "15-point-ema"),
        #                     "30" : self.calculate_metric_slopes("30m", "15-point-ema"),
        #                 },
        #                 "50-point-ema_slope" : {
        #                     "5" : self.calculate_metric_slopes("5m", "50-point-ema"),
        #                     "15" : self.calculate_metric_slopes("15m", "50-point-ema"),
        #                     "30" : self.calculate_metric_slopes("30m", "50-point-ema"),
        #                 },
        #             },
                
        #             "ema_crossovers" : {
        #                 "5-15-ema" : MetricAnalyzer_2.calculate_ema_crossovers("5m", "15m", "5-point-ema", "15-point-ema"),
        #                 "15-50-ema" : MetricAnalyzer_2.calculate_ema_crossovers("15m", "30m", "15-point-ema", "30-point-ema"),
        #         },
        #         "rsi" : {
        #             "current_rsi" : {
        #                 "5-rsi" : {
        #                     "5" : MetricAnalyzer_2.calculate_rsi("5m", 5),
        #                     "15" : MetricAnalyzer_2.calculate_rsi("15m", 5),
        #                 },
        #                 "15-rsi" : {
        #                     "5" : MetricAnalyzer_2.calculate_rsi("5m", 15),
        #                     "15" : MetricAnalyzer_2.calculate_rsi("15m", 15),
        #                     "30" : MetricAnalyzer_2.calculate_rsi("30m", 15),
        #                     "60" : MetricAnalyzer_2.calculate_rsi("1h", 15),
        #                     "240" : MetricAnalyzer_2.calculate_rsi("4h", 15),
        #                 },
        #                 "30-rsi" : {
        #                     "5" : MetricAnalyzer_2.calculate_rsi("5m", 30),
        #                     "15" : MetricAnalyzer_2.calculate_rsi("15m", 30),
        #                     "30" : MetricAnalyzer_2.calculate_rsi("30m", 30),
        #                 },
        #             },
        #             "rsi_slope" : {
        #                 "5-rsi_slope" : {
        #                     "5" : self.calculate_metric_slopes("5m", "5-rsi"),
        #                 },
        #                 "15-rsi_slope" : {
        #                     "5" : self.calculate_metric_slopes("5m", "15-rsi"),           
        #                 }
        #             },
        #             "rsi_divergence" : {
        #                 "rsi-5" : {
        #                     "5" : self.calculate_rsi_divergence("rsi-5", 5, 5),
        #                 },
        #                 "rsi-15" : {
        #                     "5" : self.calculate_rsi_divergence("rsi-15", 10, 5),
        #                     "15" : self.calculate_rsi_divergence("rsi-15", 10, 15),
        #                     "30" : self.calculate_rsi_divergence("rsi-15", 10, 30),
        #                 }
        #             },
        #             "additional" :{
        #                 "minute_of_day" : self.calculate_minute_of_day(),
        #                 "day_of_week" : self.calculate_day_of_week(),
        #                 "token_age" : self.calculate_token_age(),
        #             }
        #         }
        #         }



        # return self.metrics


# METRIC_POINT = {
#     # Price-related features
#     "price_close": None,
#     "price_open": None,
#     "price_high": None,
#     "price_low": None,
#     "avg_price": None,
#     "last_20_prices": [],  # A smaller historical window for quick reactions

#     # Volume-related features
#     "volume": {
#         "current_volume": None,
#         "avg_volume_last_10_candles": None,
#         "avg_volume_last_50_candles": None,
#         "avg_volume_last_100_candles": None,
#         "volume_change_percentage": {
#             "5": None, "15": None, "30": None, "60": None, "120": None, "240": None
#         }
#     },

#     # Price-Volume weighted average price
#     "VWAP_last_10_candles": None,
#     "VWAP_last_50_candles": None,

#     # Support and resistance levels (with strength indicating how often they've been tested)
#     "support_resistance": None,

#     # Relative momentum (price change percentages) for various spans
#     "price_change_percentage": {
#         "5": None, "15": None, "30": None, "60": None, "120": None, "240": None
#     },

#     # Volatility (using standard deviation of the last 20 and 50 candles)
#     "volatility": {
#         "20_candles": None, "50_candles": None
#     },

#     # EMA-related features
#     "ema": {
#         "current_ema": {
#             "ema-5": None,
#             "ema-15": None,
#             "ema-50": None,
#             "ema-200": None
#         },
#         "ema_slope": {
#             # Using a 5-candle lookback for the short-term EMAs; for longer-term, a 10-candle slope may be more stable.
#             "ema-5": {"5_candles": None},
#             "ema-15": {"5_candles": None},
#             "ema-50": {"5_candles": None, "10_candles": None},
#         },
#         "ema_crossovers": {
#             # Only using 5 and 10 candle lookbacks for crossovers to capture quick shifts
#             "ema-5-15": {"5_candles": None, "10_candles": None},
#             "ema-15-50": {"5_candles": None, "10_candles": None}, 
#         }
#     },

#     # RSI-related features (focusing on more responsive timeframes)
#     "rsi": {
#         "current_rsi": {
#             # Use 5-minute RSI for very responsive signals and 15-minute RSI for a slightly broader view.
#             "rsi-5": {"5_min": None},
#             "rsi-15": {"15_min": None}
#         },
#         "rsi_slope": {
#             "rsi-5": {"5_candles": None},
#             "rsi-15": {"5_candles": None}
#         },
#         "rsi_divergence": {
#             # For divergence, include a lookback (which can be dynamic) and signal strength.
#             "rsi-5": {"divergence_direction": None, "divergence_strength": None, "lookback": None},
#             "rsi-15": {"divergence_direction": None, "divergence_strength": None, "lookback": None}
#         }
#     }
# }


    

    

