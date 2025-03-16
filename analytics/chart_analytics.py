import numpy as np
import pandas as pd
from scipy import signal as sp

class ChartAnalyzer:
    def __init__(self, interval, price_data=[]):
        self.interval = interval  # Base interval, e.g., '5m'
        self.price_data = price_data  # List of {'value': float} entries
        self.prices = [entry['value'] for entry in price_data]
        self.price_series = pd.Series(self.prices)
        self.last_update = -1  # Last step when zones were updated
        self.support_zones = []
        self.resistance_zones = []
        self.min_update_interval = 12  # 1hr (12 candles at 5min) for young tokens
        self.max_update_interval = 288  # 24hr (288 candles) for mature tokens

    def append_price_data(self, price_data):
        """Append new price data and update price_series."""
        self.prices.append(price_data['value'])
        self.price_data.append(price_data)
        self.price_series = pd.Series(self.prices)  # Rebuild series (simpler than concat for now)

    def find_support_resistance_zones(self, current_step, peak_distance=22, peak_rank_width=4, min_pivot_rank=3, max_zones=3):
        """Identify fixed support/resistance zones with dynamic update intervals."""
        available_candles = len(self.price_series)
        
        # Determine update interval based on token age
        if available_candles < 48:  # Less than 4 hours
            update_interval = self.min_update_interval  # 1hr updates
        elif available_candles < 288:  # 4-24 hours
            update_interval = 48  # 4hr updates
        else:  # 24+ hours
            update_interval = self.max_update_interval  # 24hr updates

        # Update zones if: first run, interval passed, or forced for young tokens
        if (self.last_update == -1 or 
            current_step - self.last_update >= update_interval or 
            (available_candles < update_interval and not self.support_zones)):
            # Use all available data up to max interval
            lookback = min(available_candles, update_interval * 2)  # Double interval for better structure
            price_window = self.price_series[-lookback:] if lookback < len(self.price_series) else self.price_series
            
            supports, resistances = self._calculate_zones(price_window, peak_distance, peak_rank_width, min_pivot_rank)
            self.support_zones = self.cluster_levels(supports, max_zones=max_zones)
            self.resistance_zones = self.cluster_levels(resistances, max_zones=max_zones)
            self.last_update = current_step

        # Pad zones to ensure fixed length for RL
        support_padded = self.support_zones + [{"zone_level": 0.0, "strength": 0.0}] * (max_zones - len(self.support_zones))
        resistance_padded = self.resistance_zones + [{"zone_level": 0.0, "strength": 0.0}] * (max_zones - len(self.resistance_zones))
        
        return {
            "support_zones": support_padded[:max_zones],  # Always 3
            "resistance_zones": resistance_padded[:max_zones]  # Always 3
        }

    def _calculate_zones(self, price_window, peak_distance, peak_rank_width, min_pivot_rank):
        """Identify peaks and troughs from price window (close prices only)."""
        peaks, _ = sp.find_peaks(price_window, distance=peak_distance)
        peak_to_rank = {peak: 0 for peak in peaks}
        for i, current_peak in enumerate(peaks):
            current_price = price_window.iloc[current_peak]
            for previous_peak in peaks[:i]:
                if abs(current_price - price_window.iloc[previous_peak]) <= peak_rank_width:
                    peak_to_rank[current_peak] += 1
        resistances = [price_window.iloc[peak] for peak, rank in peak_to_rank.items() if rank >= min_pivot_rank]

        troughs, _ = sp.find_peaks(-price_window, distance=peak_distance)
        trough_to_rank = {trough: 0 for trough in troughs}
        for i, current_trough in enumerate(troughs):
            current_price = price_window.iloc[current_trough]
            for previous_trough in troughs[:i]:
                if abs(current_price - price_window.iloc[previous_trough]) <= peak_rank_width:
                    trough_to_rank[current_trough] += 1
        supports = [price_window.iloc[trough] for trough, rank in trough_to_rank.items() if rank >= min_pivot_rank]

        

        return sorted(supports), sorted(resistances)

    def cluster_levels(self, levels, relative_threshold=0.022, min_touch_count=2, max_touches=15, max_zones=3):
        """Cluster levels and limit to top N by strength."""
        if not levels:
            return []

        levels = sorted(levels)
        price_range = max(levels) - min(levels) if levels else 1
        threshold = relative_threshold * price_range

        clustered = []
        current_cluster = []
        zone_touch_counts = {}

        for lvl in levels:
            if not current_cluster or abs(current_cluster[-1] - lvl) <= threshold:
                current_cluster.append(lvl)
            else:
                if len(current_cluster) >= min_touch_count:
                    avg_cluster_price = np.mean(current_cluster)
                    clustered.append(avg_cluster_price)
                    zone_touch_counts[avg_cluster_price] = min(len(current_cluster), max_touches)
                current_cluster = [lvl]

        if current_cluster and len(current_cluster) >= min_touch_count:
            avg_cluster_price = np.mean(current_cluster)
            clustered.append(avg_cluster_price)
            zone_touch_counts[avg_cluster_price] = min(len(current_cluster), max_touches)

        max_touches_count = max(zone_touch_counts.values()) if zone_touch_counts else 1
        zones_with_strength = [
            {"zone_level": zone, "strength": zone_touch_counts[zone] / max_touches_count}
            for zone in clustered
        ]
        
        zones_with_strength.sort(key=lambda x: x["strength"], reverse=True)
        return zones_with_strength[:max_zones]
    

    def calculate_peak_distance(self):
        """Calculates percentage distance from the all-time peak price."""
        price_data = self.price_data
        if not price_data:
            return 0.0
        prices = [entry["value"] for entry in price_data]
        current_price = price_data[-1]["value"]
        peak_price = max(prices)
        return ((current_price - peak_price) / peak_price) * 100 if peak_price != 0 else 0.0


    def calculate_drawdown(self, lookback_short=48, lookback_long=288):
        price_data = self.price_data
        """Calculates percentage drawdown from peak prices over short and long lookbacks."""
        if not price_data or len(price_data) < 2:
            return {"short": 0.0, "long": 0.0}
        current_price = price_data[-1]["value"]
        start_idx_short = max(0, len(price_data) - lookback_short)
        prices_short = [entry["value"] for entry in price_data[start_idx_short:]]
        peak_short = max(prices_short)
        drawdown_short = ((current_price - peak_short) / peak_short) * 100 if peak_short != 0 else 0.0
        start_idx_long = max(0, len(price_data) - lookback_long)
        prices_long = [entry["value"] for entry in price_data[start_idx_long:]]
        peak_long = max(prices_long)
        drawdown_long = ((current_price - peak_long) / peak_long) * 100 if peak_long != 0 else 0.0
        return {"short": drawdown_short, "long": drawdown_long}