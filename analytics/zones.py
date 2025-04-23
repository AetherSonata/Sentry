import numpy as np
from scipy.signal import find_peaks
from dataclasses import dataclass
from typing import Dict, Tuple, List

@dataclass
class ZoneConfig:
    """Configuration for zone calculation parameters."""
    k_strong_distance: float
    k_prominence: float
    k_peak_distance: float
    k_width: float
    k_pivot: float
    interval_in_minutes: int  # Added interval for specific OHLCV data

class ZoneAnalyzer:
    def __init__(self, metric_collector):
        """
        Initialize the ZoneAnalyzer with a metric_collector object.

        Args:
            metric_collector: An object containing interval_data_aggregator with OHLCV data.
        """
        self.metric_collector = metric_collector
        self.support_zones = []  # List of lists of zone dicts
        self.resistance_zones = []  # List of lists of zone dicts

    def calculate_std_dev(self, window: int, interval_in_minutes: int) -> float:
        """
        Calculate the coefficient of variation of close prices over the window for a specific interval.

        Args:
            window: Number of intervals to consider from the end of OHLCV data.
            interval_in_minutes: Interval in minutes (e.g., 5 for 5m, 60 for 1h).

        Returns:
            float: Coefficient of variation (std_dev / mean_price), or 0.3 if insufficient data.
        """
        # Fetch OHLCV data for the specified interval
        data = self.metric_collector.interval_data_aggregator.get_interval_data(interval_in_minutes, window)
        prices = [entry["close"] for entry in data]
        if len(prices) < 2:
            return 0.3
        std_dev = np.std(prices, ddof=1)
        mean_price = np.mean(prices)
        return std_dev / mean_price if mean_price != 0 else 0.3

    def get_dynamic_zones(self, window: int, zone_type: str) -> Tuple[Dict, Dict]:
        """
        Calculate and return one dynamic support and one resistance zone based on zone type.

        Args:
            window: Number of intervals to consider (e.g., 80 for 5-minute candles).
            zone_type: 'short_term', 'mid_term', or 'long_term' to determine tuning factors.

        Returns:
            Tuple: (support_zone, resistance_zone), each a dict with 'level' and 'strength',
                or empty dicts {} if no zones are found or insufficient data.
        """
        # Define tuning factors for each zone type
        zone_configs: Dict[str, ZoneConfig] = {
            "short_term": ZoneConfig(
                k_strong_distance=0.2,
                k_prominence=0.05,
                k_peak_distance=0.1,
                k_width=0.1,
                k_pivot=0.01,
                interval_in_minutes=5  # 5m
            ),
            "mid_term": ZoneConfig(
                k_strong_distance=0.15,  # Adjusted to allow more strong peaks
                k_prominence=0.02,      # Reduced to detect less prominent peaks
                k_peak_distance=0.05,   # Reduced to allow closer general peaks
                k_width=0.05,           # Increased to widen binning range
                k_pivot=0.005,          # Reduced to lower the pivot rank threshold
                interval_in_minutes=60  # 1h
            ),
            "long_term": ZoneConfig(
                k_strong_distance=1,
                k_prominence=0.1,
                k_peak_distance=0.2,
                k_width=0.1,
                k_pivot=0.015,
                interval_in_minutes=240  # 4h
            )
        }

        config = zone_configs.get(zone_type, zone_configs["mid_term"])
        interval_in_minutes = config.interval_in_minutes

        # Fetch OHLCV data for the specified interval
        data = self.metric_collector.interval_data_aggregator.get_interval_data(interval_in_minutes, window)
        if len(data) < 2:
            return {}, {}

        # Extract high, low, and close prices
        highs = [entry["high"] for entry in data]
        lows = [entry["low"] for entry in data]
        close_prices = [entry["close"] for entry in data]

        # Ensure window is valid
        window = min(window, len(data))
        windowed_highs = highs[-window:] if len(highs) >= window else highs
        windowed_lows = lows[-window:] if len(lows) >= window else lows
        windowed_close_prices = close_prices[-window:] if len(close_prices) >= window else close_prices
        if len(windowed_highs) < 2:
            return {}, {}

        # Calculate dynamic parameters
        mean_price = np.mean(windowed_close_prices)
        cv = self.calculate_std_dev(window, interval_in_minutes)

        strong_distance = max(1, int(config.k_strong_distance * window * cv))
        strong_prominence = max(0.01, config.k_prominence * mean_price * cv)
        peak_distance = max(1, int(config.k_peak_distance * window * cv))
        peak_rank_width = max(0.0001, config.k_width * mean_price * cv)  # Use float for precision
        min_pivot_rank = max(2, int(config.k_pivot * window))

        # Calculate ATH and ATL within the window
        ath = max(windowed_highs)
        atl = min(windowed_lows)

        # Resistance Zones Calculation (using highs)
        strong_peaks, _ = find_peaks(windowed_highs, distance=strong_distance, prominence=strong_prominence)
        strong_peak_values = [{'level': windowed_highs[i], 'strength': 50.0} for i in strong_peaks]
        if ath not in [p['level'] for p in strong_peak_values]:
            strong_peak_values.append({'level': ath, 'strength': 100.0})

        peaks, _ = find_peaks(windowed_highs, distance=peak_distance)
        peak_to_rank = {peak: 0 for peak in peaks}
        for i, curr_peak in enumerate(peaks):
            curr_price = windowed_highs[curr_peak]
            for prev_peak in peaks[:i]:
                if abs(curr_price - windowed_highs[prev_peak]) <= peak_rank_width:
                    peak_to_rank[curr_peak] += 1
        general_resistances = [
            {'level': windowed_highs[peak], 'strength': 10.0 * (rank + 1)}
            for peak, rank in peak_to_rank.items() if rank >= min_pivot_rank
        ]

        resistances = strong_peak_values + general_resistances
        resistances.sort(key=lambda x: x['level'])

        resistance_bins = []
        if resistances:
            current_bin = [resistances[0]]
            for r in resistances[1:]:
                if r['level'] - current_bin[-1]['level'] < peak_rank_width:
                    current_bin.append(r)
                else:
                    resistance_bins.append(current_bin)
                    current_bin = [r]
            resistance_bins.append(current_bin)
        resistance_zones = [
            {'level': np.mean([z['level'] for z in bin]), 'strength': sum(z['strength'] for z in bin)}
            for bin in resistance_bins
        ]

        # Select the resistance zone with the highest strength
        resistance_zone = max(resistance_zones, key=lambda x: x['strength'], default={})

        # Support Zones Calculation (using lows)
        neg_lows = [-p for p in windowed_lows]
        strong_troughs, _ = find_peaks(neg_lows, distance=strong_distance, prominence=strong_prominence)
        strong_trough_values = [{'level': windowed_lows[i], 'strength': 50.0} for i in strong_troughs]
        if atl not in [p['level'] for p in strong_trough_values]:
            strong_trough_values.append({'level': atl, 'strength': 100.0})

        troughs, _ = find_peaks(neg_lows, distance=peak_distance)
        trough_to_rank = {trough: 0 for trough in troughs}
        for i, curr_trough in enumerate(troughs):
            curr_price = windowed_lows[curr_trough]
            for prev_trough in troughs[:i]:
                if abs(curr_price - windowed_lows[prev_trough]) <= peak_rank_width:
                    trough_to_rank[curr_trough] += 1
        general_supports = [
            {'level': windowed_lows[trough], 'strength': 10.0 * (rank + 1)}
            for trough, rank in trough_to_rank.items() if rank >= min_pivot_rank
        ]

        supports = strong_trough_values + general_supports
        supports.sort(key=lambda x: x['level'])

        support_bins = []
        if supports:
            current_bin = [supports[0]]
            for s in supports[1:]:
                if s['level'] - current_bin[-1]['level'] < peak_rank_width:
                    current_bin.append(s)
                else:
                    support_bins.append(current_bin)
                    current_bin = [s]
            support_bins.append(current_bin)
        support_zones = [
            {'level': np.mean([z['level'] for z in bin]), 'strength': sum(z['strength'] for z in bin)}
            for bin in support_bins
        ]

        # Select the support zone with the highest strength
        support_zone = max(support_zones, key=lambda x: x['strength'], default={})

        return support_zone, resistance_zone

    # def get_zones(self, strong_distance=60, strong_prominence=20, peak_distance=10,
    #               peak_rank_width=5, min_pivot_rank=3, window=100) -> Tuple[Dict, Dict]:
    #     """Original method retained for compatibility."""
    #     return self.get_dynamic_zones(window, "mid_term")