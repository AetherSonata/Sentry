import numpy as np
import pandas as pd
from scipy import signal as sp
from collections import deque

class ChartAnalyzer:
    def __init__(self, interval, price_data=[]):
        self.interval = interval
        self.price_data = price_data
        self.prices = [entry['value'] for entry in price_data]
        self.price_series = pd.Series(self.prices)
        self.last_update = -1
        self.zones = deque(maxlen=50)  # Persistent: {"level": float, "touches": int, "last_touched": int, "is_major": bool}
        self.min_update_interval = 12
        self.max_update_interval = 144

    def append_price_data(self, price_data):
        self.prices.append(price_data['value'])
        self.price_data.append(price_data)
        self.price_series = pd.Series(self.prices)


        # OUTDATED CODE

    # def find_key_zones(self, current_step, max_zones=6, volatility_window=20, filter_percentage_minor=50.0, filter_percentage_major=200.0, min_strength=0.3, decay_period=144):
    #     available_candles = len(self.price_series)
    #     if available_candles < 12:
    #         return [{"zone_level": 0.0, "strength": 0.0, "is_major": False}] * max_zones

    #     current_price = self.price_series.iloc[-1]
    #     volatility = self.price_series[-volatility_window:].pct_change().std() * 100 if available_candles >= volatility_window else 1.0
    #     price_range = max(self.price_series) - min(self.price_series) if self.price_series.any() else current_price * 0.01

    #     # Adjust peak detection parameters based on token age and price level
    #     age_factor = min(available_candles / 1728, 1.0)  # Scale up to 9 days (1728 intervals at 5m)

    #     # Update minor zones every interval
    #     lookback_minor = min(available_candles, int(volatility * 12))
    #     price_window_minor = self.price_series[-lookback_minor:]
    #     # Scale peak distance with price range and current price
    #     peak_distance_minor = max(10, int((price_range / current_price) * 20 * (1 + age_factor) + volatility * 5))
    #     self._update_zones(price_window_minor, peak_distance_minor, current_step, is_major=False, prominence_factor=1.0)

    #     # Update major zones periodically (every 12 hours)
    #     if current_step % 144 == 0 or self.last_update == -1:
    #         lookback_major = min(available_candles, 576)  # 48 hours
    #         price_window_major = self.price_series[-lookback_major:]
    #         # Larger scaling for major zones
    #         peak_distance_major = max(20, int((price_range / current_price) * 40 * (1 + age_factor) + volatility * 10))
    #         self._update_zones(price_window_major, peak_distance_major, current_step, is_major=True, prominence_factor=2.0)
    #         self._cluster_persistent_zones(cluster_threshold=0.01 * price_range)  # Tighter clustering
    #         self.last_update = current_step

    #     # Decay untouched zones (every 12 hours, more aggressive)
    #     for zone in self.zones:
    #         if current_step - zone["last_touched"] > decay_period:
    #             decay_amount = 2 if not zone["is_major"] else 1  # Faster decay for minor zones
    #             zone["touches"] = max(1, zone["touches"] - decay_amount)

    #     # Filter zones by type and distance
    #     minor_zones = [z for z in self.zones if not z["is_major"] and abs(z["level"] - current_price) / current_price <= filter_percentage_minor / 100]
    #     major_zones = [z for z in self.zones if z["is_major"] and abs(z["level"] - current_price) / current_price <= filter_percentage_major / 100]
    #     all_zones = minor_zones + major_zones

    #     # Rank zones and apply minimum strength threshold
    #     zones_with_strength = self._rank_zones(all_zones, current_price)
    #     filtered_zones = [z for z in zones_with_strength if z["strength"] >= min_strength]
    #     return filtered_zones[:max_zones]

    # def _update_zones(self, price_window, peak_distance, current_step, is_major, prominence_factor=1.0):
    #     prominence = price_window.std() * prominence_factor if price_window.std() > 0 else 0.01
    #     peaks, _ = sp.find_peaks(price_window, distance=peak_distance, prominence=prominence)
    #     troughs, _ = sp.find_peaks(-price_window, distance=peak_distance, prominence=prominence)
    #     new_levels = [price_window.iloc[i] for i in list(peaks) + list(troughs)]
    #     threshold = price_window.iloc[-1] * 0.01  # 1% clustering

    #     for new_level in new_levels:
    #         close_zones = [z for z in self.zones if abs(z["level"] - new_level) <= threshold]
    #         if close_zones:
    #             closest = min(close_zones, key=lambda z: abs(z["level"] - new_level))
    #             closest["touches"] += 1
    #             closest["last_touched"] = current_step
    #             if is_major:
    #                 closest["is_major"] = True
    #         else:
    #             self.zones.append({"level": new_level, "touches": 1, "last_touched": current_step, "is_major": is_major})

    def _cluster_persistent_zones(self, cluster_threshold):
        if not self.zones:
            return
        levels = sorted(self.zones, key=lambda x: x["level"])
        clustered = []
        current_cluster = []
        for zone in levels:
            if not current_cluster or abs(current_cluster[-1]["level"] - zone["level"]) <= cluster_threshold:
                current_cluster.append(zone)
            else:
                avg_level = np.mean([z["level"] for z in current_cluster])
                total_touches = sum(z["touches"] for z in current_cluster)
                last_touched = max(z["last_touched"] for z in current_cluster)
                is_major = any(z["is_major"] for z in current_cluster)
                if total_touches >= 2:  # Require at least 2 touches to keep a clustered zone
                    clustered.append({"level": avg_level, "touches": total_touches, "last_touched": last_touched, "is_major": is_major})
                current_cluster = [zone]
        if current_cluster:
            avg_level = np.mean([z["level"] for z in current_cluster])
            total_touches = sum(z["touches"] for z in current_cluster)
            last_touched = max(z["last_touched"] for z in current_cluster)
            is_major = any(z["is_major"] for z in current_cluster)
            if total_touches >= 2:
                clustered.append({"level": avg_level, "touches": total_touches, "last_touched": last_touched, "is_major": is_major})
        self.zones = clustered

    def _rank_zones(self, zones, current_price, max_touches=10):
        max_touches_count = min(max([z["touches"] for z in zones], default=1), max_touches)
        zones_with_strength = []
        for zone in zones:
            touch_strength = zone["touches"] / max_touches_count
            proximity = 1 - min(abs(zone["level"] - current_price) / (current_price * 0.5), 1)
            strength = 0.7 * touch_strength + 0.3 * proximity
            zones_with_strength.append({"zone_level": zone["level"], "strength": min(strength, 1.0), "is_major": zone["is_major"]})
        return zones_with_strength

    # Keep calculate_peak_distance and calculate_drawdown unchanged

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
    

def normalize_zones(zone_list, current_price, max_zones=3, include_major_flag=False):
    """
    Normalize zone distances and strengths, sorted by proximity to current_price.

    Args:
        zone_list (list): List of zone dictionaries {"zone_level": float, "strength": float, "is_major": bool}.
        current_price (float): Current price to calculate distances from.
        max_zones (int): Maximum number of zones to return.
        include_major_flag (bool): If True, include 'is_major' in output for historical context.

    Returns:
        dict: Normalized distances and strengths for each zone level, ordered by proximity.
    """
    # Sort by absolute distance from current_price
    # For supports (below price), closest has smallest negative distance
    # For resistances (above price), closest has smallest positive distance
    zone_list.sort(key=lambda x: abs(x["zone_level"] - current_price))

    normalized = {}
    for j in range(max_zones):
        prefix = f"level_{j+1}"
        if j < len(zone_list) and current_price != 0:
            level = zone_list[j]["zone_level"]
            strength = zone_list[j]["strength"]  # Pre-normalized 0-1
            normalized[f"{prefix}_dist"] = ((level - current_price) / current_price) * 100
            normalized[f"{prefix}_strength"] = strength
            if include_major_flag:
                normalized[f"{prefix}_is_major"] = zone_list[j]["is_major"]
        else:
            normalized[f"{prefix}_dist"] = 0.0
            normalized[f"{prefix}_strength"] = 0.0
            if include_major_flag:
                normalized[f"{prefix}_is_major"] = False
    return normalized

    