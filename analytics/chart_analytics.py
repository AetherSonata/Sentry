import numpy as np
import pandas as pd
from scipy import signal as sp


class ChartAnalyzer:
    def __init__(self, interval, price_data=[]):
        self.interval = interval  # e.g., '5m'
        self.price_data = price_data
        self.prices = [entry['value'] for entry in price_data]
        self.price_series = pd.Series(self.prices)
        self.last_update = -1
        self.zones = []  # Unified list of zones
        self.min_update_interval = 12  # 1hr
        self.max_update_interval = 144  # 12hr (adjusted for shitcoins)

    def append_price_data(self, price_data):
        """Append new price data and update price_series."""
        self.prices.append(price_data['value'])
        self.price_data.append(price_data)
        self.price_series = pd.Series(self.prices)

    def find_key_zones(self, current_step, max_zones=6, volatility_window=20, filter_percentage=50.0):
        """
        Identify key price zones (major and minor) dynamically based on price action.

        Args:
            current_step (int): Current simulation step.
            max_zones (int): Max number of zones to return (e.g., 3 major + 3 minor).
            volatility_window (int): Window to calculate volatility for dynamic parameters.
            filter_percentage (float): Max percentage distance from current price to include zones (e.g., 50.0 for ±50%).

        Returns:
            list: Sorted list of {"zone_level": float, "strength": float, "is_major": bool}.
        """
        available_candles = len(self.price_series)
        if available_candles < 12:  # Need at least 1hr of data
            return [{"zone_level": 0.0, "strength": 0.0, "is_major": False}] * max_zones

        # Dynamic update interval based on token age and volatility
        volatility = self.price_series[-volatility_window:].pct_change().std() * 100 if available_candles >= volatility_window else 1.0
        update_interval = min(self.max_update_interval, max(self.min_update_interval, int(volatility * 12)))  # Scale with volatility

        if (self.last_update == -1 or current_step - self.last_update >= update_interval):
            # Lookback: Use up to 2x max interval or all data
            lookback = min(available_candles, self.max_update_interval * 2)
            price_window = self.price_series[-lookback:]

            # Dynamic parameters based on volatility
            peak_distance = max(5, int(volatility * 5))  # Min 5 candles, scales with volatility
            cluster_threshold = max(0.01, volatility / 100)  # 1% min, scales with volatility

            # Calculate zones
            zones = self._calculate_zones(price_window, peak_distance=peak_distance)
            self.zones = self._cluster_and_rank_zones(zones, cluster_threshold=cluster_threshold, current_price=price_window.iloc[-1])
            self.last_update = current_step

        # Filter and sort zones relative to current price
        current_price = self.price_series.iloc[-1]
        filter_factor = filter_percentage / 100.0  # Convert percentage to decimal (e.g., 50.0 -> 0.5)
        relevant_zones = [z for z in self.zones if abs(z["zone_level"] - current_price) / current_price <= filter_factor]
        relevant_zones.sort(key=lambda x: x["zone_level"])

        # Select top major and minor zones
        major_zones = sorted([z for z in relevant_zones if z["is_major"]], key=lambda x: x["strength"], reverse=True)[:3]
        minor_zones = sorted([z for z in relevant_zones if not z["is_major"]], key=lambda x: x["strength"], reverse=True)[:3]
        final_zones = major_zones + minor_zones

        # Pad to max_zones if needed
        final_zones += [{"zone_level": 0.0, "strength": 0.0, "is_major": False}] * (max_zones - len(final_zones))
        return final_zones[:max_zones]

    def _calculate_zones(self, price_window, peak_distance):
        """Identify major and minor peaks/troughs."""
        # Major zones (strong peaks/troughs)
        major_distance = peak_distance * 3  # Wider spacing for major zones
        major_peaks, _ = sp.find_peaks(price_window, distance=major_distance, prominence=price_window.std() * 0.5)
        major_troughs, _ = sp.find_peaks(-price_window, distance=major_distance, prominence=price_window.std() * 0.5)
        
        # Minor zones (general peaks/troughs)
        minor_peaks, _ = sp.find_peaks(price_window, distance=peak_distance)
        minor_troughs, _ = sp.find_peaks(-price_window, distance=peak_distance)

        # Combine into zones with is_major flag
        zones = [
            {"level": price_window.iloc[p], "touches": 1, "is_major": True} for p in major_peaks
        ] + [
            {"level": price_window.iloc[t], "touches": 1, "is_major": True} for t in major_troughs
        ] + [
            {"level": price_window.iloc[p], "touches": 1, "is_major": False} for p in minor_peaks if p not in major_peaks
        ] + [
            {"level": price_window.iloc[t], "touches": 1, "is_major": False} for t in minor_troughs if t not in major_troughs
        ]

        return zones

    def _cluster_and_rank_zones(self, zones, cluster_threshold, current_price, min_touches=1, max_touches=10):
        """Cluster zones and assign strength based on touches and proximity."""
        if not zones:
            return []

        levels = sorted(zones, key=lambda x: x["level"])
        clustered = []
        current_cluster = []

        # Cluster based on relative threshold
        price_range = max(self.price_series) - min(self.price_series) if self.price_series.any() else 1
        threshold = cluster_threshold * price_range

        for zone in levels:
            if not current_cluster or abs(current_cluster[-1]["level"] - zone["level"]) <= threshold:
                current_cluster.append(zone)
            else:
                if len(current_cluster) >= min_touches:
                    avg_level = np.mean([z["level"] for z in current_cluster])
                    touches = sum(z["touches"] for z in current_cluster)
                    is_major = any(z["is_major"] for z in current_cluster)
                    clustered.append({"level": avg_level, "touches": touches, "is_major": is_major})
                current_cluster = [zone]

        if current_cluster and len(current_cluster) >= min_touches:
            avg_level = np.mean([z["level"] for z in current_cluster])
            touches = sum(z["touches"] for z in current_cluster)
            is_major = any(z["is_major"] for z in current_cluster)
            clustered.append({"level": avg_level, "touches": touches, "is_major": is_major})

        # Calculate strength: combine touches and proximity to current price
        max_touches_count = min(max([z["touches"] for z in clustered], default=1), max_touches)
        zones_with_strength = []
        for zone in clustered:
            touch_strength = zone["touches"] / max_touches_count
            proximity = 1 - min(abs(zone["level"] - current_price) / (current_price * 0.5), 1)  # 0-1, closer = stronger
            strength = 0.7 * touch_strength + 0.3 * proximity  # Weighted combination
            zones_with_strength.append({
                "zone_level": zone["level"],
                "strength": min(strength, 1.0),  # Cap at 1.0
                "is_major": zone["is_major"]
            })

        return zones_with_strength
        

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