import numpy as np
from scipy.signal import find_peaks

class ZoneAnalyzer:
    def __init__(self, metrics_analyzer):
        """
        Initialize the ZoneAnalyzer with a metrics_analyzer object.

        Args:
            metrics_analyzer: An object containing price_data, a list of dictionaries
                             with a "value" key representing price at each interval.
        """
        self.metrics_analyzer = metrics_analyzer
        # Persistent storage for zones
        self.support_zones = []  # List of lists of zone dicts
        self.resistance_zones = []  # List of lists of zone dicts


    def get_zones(self, strong_distance=60, strong_prominence=20, peak_distance=10, peak_rank_width=5, min_pivot_rank=3, window=100):
        """
        Calculate and return the current support and resistance zones as lists.

        Returns:
            tuple: (support_zones, resistance_zones), where each is a list of dicts
                   with 'level' (float) and 'strength' (float) keys.
        """
                # Configuration parameters

        # strong_distance = 60      # Min intervals between strong peaks/troughs
        # strong_prominence = 20    # Min prominence for strong peaks/troughs
        # peak_distance =  10        # Min distance for general peaks/troughs
        # peak_rank_width = 5       # Width to consider nearby peaks for merging/ranking
        # min_pivot_rank = 3        # Min rejections to qualify as a general zone
        # window = 100              # Window size for ATH/ATL calculation

        # Extract price data
        prices = [entry["value"] for entry in self.metrics_analyzer.price_data]
        if len(prices) < 2:
            return [], []

        # Calculate ATH and ATL within the window
        ath = max(prices[-window:]) if len(prices) >= window else max(prices)
        atl = min(prices[-window:]) if len(prices) >= window else min(prices)

        ### Resistance Zones Calculation
        # Find strong peaks
        strong_peaks, _ = find_peaks(prices, distance=strong_distance, prominence=strong_prominence)
        strong_peak_values = [{'level': prices[i], 'strength': 50.0} for i in strong_peaks]
        if ath not in [p['level'] for p in strong_peak_values]:
            strong_peak_values.append({'level': ath, 'strength': 100.0})

        # Find general peaks
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

        # Combine all resistance zones
        resistances = strong_peak_values + general_resistances
        resistances.sort(key=lambda x: x['level'])

        # Merge nearby resistances
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
            {
                'level': np.mean([z['level'] for z in bin]),
                'strength': sum(z['strength'] for z in bin)
            }
            for bin in resistance_bins
        ]

        ### Support Zones Calculation
        # Negate prices to find troughs
        neg_prices = [-p for p in prices]
        # Find strong troughs
        strong_troughs, _ = find_peaks(neg_prices, distance=strong_distance, prominence=strong_prominence)
        strong_trough_values = [{'level': prices[i], 'strength': 50.0} for i in strong_troughs]
        if atl not in [p['level'] for p in strong_trough_values]:
            strong_trough_values.append({'level': atl, 'strength': 100.0})

        # Find general troughs
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

        # Combine all support zones
        supports = strong_trough_values + general_supports
        supports.sort(key=lambda x: x['level'])

        # Merge nearby supports
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
            {
                'level': np.mean([z['level'] for z in bin]),
                'strength': sum(z['strength'] for z in bin)
            }
            for bin in support_bins
        ]

        # Store zones for persistence
        # self.support_zones.append(support_zones)
        # self.resistance_zones.append(resistance_zones)

        # Return as lists for plotting
        return support_zones, resistance_zones

    def update_zones(self, new_price):
        """
        Update the strength of existing zones based on a new price.

        Args:
            new_price (float): The latest price to check against zones.
        """
        tolerance = peak_rank_width  # Price range to consider a zone "revisited"
        decay_factor = 0.95  # Reduce strength by 5% if not revisited

        if not self.support_zones or not self.resistance_zones:
            self.get_zones()  # Initialize zones if empty

        # Update the latest support zones
        latest_support = self.support_zones[-1]
        for zone in latest_support:
            if abs(new_price - zone['level']) <= tolerance:
                zone['strength'] += 10.0  # Boost strength if revisited
            else:
                zone['strength'] *= decay_factor  # Decay if not revisited
        self.support_zones[-1] = [z for z in latest_support if z['strength'] >= 5.0]

        # Update the latest resistance zones
        latest_resistance = self.resistance_zones[-1]
        for zone in latest_resistance:
            if abs(new_price - zone['level']) <= tolerance:
                zone['strength'] += 10.0
            else:
                zone['strength'] *= decay_factor
        self.resistance_zones[-1] = [z for z in latest_resistance if z['strength'] >= 5.0]