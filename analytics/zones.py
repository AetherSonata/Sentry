import numpy as np
from scipy.signal import find_peaks
from dataclasses import dataclass
from typing import Dict, Tuple

@dataclass
class ZoneConfig:
    """Configuration for zone calculation parameters."""
    k_strong_distance: float
    k_prominence: float
    k_peak_distance: float
    k_width: float
    k_pivot: float

class ZoneAnalyzer:
    def __init__(self, metrics_analyzer):
        """
        Initialize the ZoneAnalyzer with a metrics_analyzer object.

        Args:
            metrics_analyzer: An object containing price_data, a list of dictionaries
                             with a "value" key representing price at each interval.
        """
        self.metrics_analyzer = metrics_analyzer
        self.support_zones = []  # List of lists of zone dicts
        self.resistance_zones = []  # List of lists of zone dicts

    def calculate_std_dev(self, window: int) -> float:
        """
        Calculate the coefficient of variation of prices over the window.

        Args:
            window: Number of intervals to consider from the end of price data.

        Returns:
            float: Coefficient of variation (std_dev / mean_price), or 0.3 if insufficient data.
        """
        prices = [entry["value"] for entry in self.metrics_analyzer.price_data]
        if len(prices) < 2:
            return 0.3
        windowed_prices = prices[-window:] if len(prices) >= window else prices
        if len(windowed_prices) <= 1:
            return 0.3
        std_dev = np.std(windowed_prices, ddof=1)
        mean_price = np.mean(windowed_prices)
        return std_dev / mean_price if mean_price != 0 else 0.3

    def get_dynamic_zones(self, window: int, zone_type: str) -> Tuple[Dict, Dict]:
        """
        Calculate and return one dynamic support and one resistance zone based on zone type.

        Args:
            window: Number of intervals to consider.
            zone_type: 'short_term', 'mid_term', or 'long_term' to determine tuning factors.

        Returns:
            Tuple: (support_zone, resistance_zone), each a dict with 'level' and 'strength',
                   or empty dicts {} if no zones are found.
        """
        # Define tuning factors for each zone type
        zone_configs: Dict[str, ZoneConfig] = {
            "short_term": ZoneConfig(
                k_strong_distance=0.2,
                k_prominence=0.05,
                k_peak_distance=0.1,
                k_width=0.1,
                k_pivot=0.005
            ),
            "mid_term": ZoneConfig(
                k_strong_distance=0.1,
                k_prominence=0.1,
                k_peak_distance=0.22,
                k_width=0.1,
                k_pivot=0.015
            ),
            "long_term": ZoneConfig(
                k_strong_distance=1,
                k_prominence=0.1,
                k_peak_distance=0.25,
                k_width=0.1,
                k_pivot=0.02
            )
        }

        config = zone_configs.get(zone_type, zone_configs["mid_term"])
        prices = [entry["value"] for entry in self.metrics_analyzer.price_data]
        if len(prices) < 2:
            return {}, {}

        # Calculate dynamic parameters
        window = max(200, window)
        mean_price = np.mean(prices[-window:])
        cv = self.calculate_std_dev(window)
        
        strong_distance = max(1, int(config.k_strong_distance * window * cv))
        strong_prominence = max(0.01, config.k_prominence * mean_price * cv)
        peak_distance = max(1, int(config.k_peak_distance * window * cv))
        peak_rank_width = max(1, int(config.k_width * mean_price * cv))
        min_pivot_rank = max(2, int(config.k_pivot * window))

        # Calculate ATH and ATL within the window
        ath = max(prices[-window:]) if len(prices) >= window else max(prices)
        atl = min(prices[-window:]) if len(prices) >= window else min(prices)

        # Resistance Zones Calculation
        strong_peaks, _ = find_peaks(prices, distance=strong_distance, prominence=strong_prominence)
        strong_peak_values = [{'level': prices[i], 'strength': 50.0} for i in strong_peaks]
        if ath not in [p['level'] for p in strong_peak_values]:
            strong_peak_values.append({'level': ath, 'strength': 100.0})

        peaks, _ = find_peaks(prices, distance=peak_distance)
        peak_to_rank = {peak: 0 for peak in peaks}
        for i, curr_peak in enumerate(peaks):
            curr_price = prices[curr_peak]
            for prev_peak in peaks[:i]:
                if abs(curr_price - prices[prev_peak]) <= peak_rank_width:
                    peak_to_rank[curr_peak] += 1
        general_resistances = [
            {'level': prices[peak], 'strength': 10.0 * (rank + 1)}
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

        # Support Zones Calculation
        neg_prices = [-p for p in prices]
        strong_troughs, _ = find_peaks(neg_prices, distance=strong_distance, prominence=strong_prominence)
        strong_trough_values = [{'level': prices[i], 'strength': 50.0} for i in strong_troughs]
        if atl not in [p['level'] for p in strong_trough_values]:
            strong_trough_values.append({'level': atl, 'strength': 100.0})

        troughs, _ = find_peaks(neg_prices, distance=peak_distance)
        trough_to_rank = {trough: 0 for trough in troughs}
        for i, curr_trough in enumerate(troughs):
            curr_price = prices[curr_trough]
            for prev_trough in troughs[:i]:
                if abs(curr_price - prices[prev_trough]) <= peak_rank_width:
                    trough_to_rank[curr_trough] += 1
        general_supports = [
            {'level': prices[trough], 'strength': 10.0 * (rank + 1)}
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

    def get_zones(self, strong_distance=60, strong_prominence=20, peak_distance=10, 
                  peak_rank_width=5, min_pivot_rank=3, window=100):
        """Original method retained for compatibility."""
        return self.get_dynamic_zones(window, "mid_term")