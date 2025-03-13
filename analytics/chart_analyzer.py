import numpy as np
import pandas as pd
from scipy import signal as sp
from collections import Counter

class ChartAnalyzer:
    def __init__(self, price_data, interval):
        self.price_data = price_data
        self.interval = interval
        self.prices = [entry['value'] for entry in price_data]
        self.price_series = pd.Series(self.prices)
    
    def find_support_resistance_zones(self, peak_distance=22, peak_rank_width=4, min_pivot_rank=3, max_touches=15):
        """Identify support and resistance zones using only price points."""
        
        # Identify resistance peaks
        peaks, _ = sp.find_peaks(self.price_series, distance=peak_distance)
        peak_to_rank = {peak: 0 for peak in peaks}
        
        # Rank peaks based on proximity
        for i, current_peak in enumerate(peaks):
            current_price = self.price_series.iloc[current_peak]
            for previous_peak in peaks[:i]:
                if abs(current_price - self.price_series.iloc[previous_peak]) <= peak_rank_width:
                    peak_to_rank[current_peak] += 1
        
        resistances = [self.price_series.iloc[peak] for peak, rank in peak_to_rank.items() if rank >= min_pivot_rank]
        resistances.sort()
        
        # Identify support troughs
        troughs, _ = sp.find_peaks(-self.price_series, distance=peak_distance)  # Inverted to detect troughs
        trough_to_rank = {trough: 0 for trough in troughs}
        
        for i, current_trough in enumerate(troughs):
            current_price = self.price_series.iloc[current_trough]
            for previous_trough in troughs[:i]:
                if abs(current_price - self.price_series.iloc[previous_trough]) <= peak_rank_width:
                    trough_to_rank[current_trough] += 1
        
        supports = [self.price_series.iloc[trough] for trough, rank in trough_to_rank.items() if rank >= min_pivot_rank]
        supports.sort()

        # Cluster the support and resistance levels
        supports = self.cluster_levels(supports, max_touches=max_touches)
        resistances = self.cluster_levels(resistances, max_touches=max_touches)
        
        return {'support_zones': supports, 'resistance_zones': resistances}
    
    def cluster_levels(self, levels, relative_threshold=0.022, min_touch_count=2, max_touches=15):
        """
        Clusters similar price levels to reduce noise while preserving key support and resistance zones.
        Returns the clustered zones along with their strength (normalized touches and importance).
        """
        if not levels:
            return []

        levels = sorted(levels)  # Ensure levels are in ascending order
        price_range = max(levels) - min(levels)  # Calculate the range of prices
        threshold = relative_threshold * price_range  # Dynamic threshold based on price range

        clustered = []
        current_cluster = []
        zone_touch_counts = {}  # Dictionary to store touch counts for each zone

        for lvl in levels:
            if not current_cluster or abs(current_cluster[-1] - lvl) <= threshold:
                current_cluster.append(lvl)
            else:
                if len(current_cluster) >= min_touch_count:
                    # Calculate the average of the cluster to represent the zone
                    avg_cluster_price = np.mean(current_cluster)
                    clustered.append(avg_cluster_price)
                    # Store how many times this zone was touched
                    zone_touch_counts[avg_cluster_price] = len(current_cluster)
                current_cluster = [lvl]

        if current_cluster and len(current_cluster) >= min_touch_count:
            avg_cluster_price = np.mean(current_cluster)
            clustered.append(avg_cluster_price)
            zone_touch_counts[avg_cluster_price] = len(current_cluster)

        # Find the max touch count to normalize strength values
        max_touches_count = max(zone_touch_counts.values()) if zone_touch_counts else 1
        
        # Simplified return: Zone level and normalized strength (between 0 and 1)
        zones_with_strength = [{'zone_level': zone, 'strength': zone_touch_counts[zone] / max_touches_count} for zone in clustered]

        return zones_with_strength
