import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class ZoneParameters:
    """Parameters for a specific zone."""
    alpha: float = 0.05  # Rate of confidence adjustment
    threshold: float = 0.2  # Proximity threshold
    decay_rate: float = 0.02  # Decay rate when not near zones

class ZoneSettings:
    """Helper class to manage settings for each unique zone."""
    def __init__(self, default_alpha=0.05, default_threshold=0.2, default_decay_rate=0.02):
        self.default_params = ZoneParameters(
            alpha=default_alpha,
            threshold=default_threshold,
            decay_rate=default_decay_rate
        )
        self.zone_settings: Dict[str, ZoneParameters] = {}
        self.valid_zones = ["key_zone_1", "key_zone_2", "key_zone_3", "key_zone_4", "key_zone_5", "key_zone_6"]

    def set_parameters(self, zone_key: str, alpha: Optional[float] = None, threshold: Optional[float] = None, decay_rate: Optional[float] = None):
        """
        Set parameters for a specific zone.

        Args:
            zone_key (str): The zone identifier (e.g., 'key_zone_5').
            alpha (float, optional): Rate of confidence adjustment. Defaults to None (no change).
            threshold (float, optional): Proximity threshold. Defaults to None (no change).
            decay_rate (float, optional): Decay rate when not near zones. Defaults to None (no change).
        """
        if zone_key not in self.valid_zones:
            raise ValueError(f"Invalid zone key: {zone_key}. Must be one of {self.valid_zones}")
        
        # If no settings exist for this zone, initialize with defaults
        if zone_key not in self.zone_settings:
            self.zone_settings[zone_key] = ZoneParameters(
                alpha=self.default_params.alpha,
                threshold=self.default_params.threshold,
                decay_rate=self.default_params.decay_rate
            )
        
        # Update only the parameters provided
        if alpha is not None:
            self.zone_settings[zone_key].alpha = alpha
        if threshold is not None:
            self.zone_settings[zone_key].threshold = threshold
        if decay_rate is not None:
            self.zone_settings[zone_key].decay_rate = decay_rate

    def get_parameters(self, zone_key: str) -> ZoneParameters:
        return self.zone_settings.get(zone_key, self.default_params)

class ConfidenceCalculator:
    def __init__(self, metrics_collector, alpha=0.05, threshold=0.2, decay_rate=0.02, slope_window=10):
        """
        Initialize the ConfidenceCalculator with given parameters.

        Args:
            metrics_collector: Object with attributes key_zone_1 to key_zone_6 as single dicts and metrics list.
            alpha (float): Default rate of confidence adjustment (default: 0.05).
            threshold (float): Default proximity threshold (default: 0.2).
            decay_rate (float): Default decay rate (default: 0.02).
            slope_window (int): Number of past confidence values to store for slope (default: 10).
        """
        self.metrics_collector = metrics_collector
        self.zone_confidence = 0.0
        self.slope_window = slope_window
        self.confidence_history = []
        self.settings = ZoneSettings(
            default_alpha=alpha,
            default_threshold=threshold,
            default_decay_rate=decay_rate
        )

    def calculate_zone_confidence(self, current_price):
        """
        Calculate confidence based on price proximity to zones, preventing increase if zone level drops.

        Args:
            current_price (float): Current price to evaluate against zones.

        Returns:
            float: Updated zone confidence value between 0 and 1.
        """
        zones = []
        for key in ["key_zone_1", "key_zone_2", "key_zone_3", "key_zone_4", "key_zone_5", "key_zone_6"]:
            zone = getattr(self.metrics_collector, key, None)
            if zone and 'level' in zone:
                zone_copy = zone.copy()
                zone_copy['zone_key'] = key
                zones.append(zone_copy)

        if not zones:
            self.zone_confidence *= (1 - self.settings.default_params.decay_rate)
            self.confidence_history.append(self.zone_confidence)
            return self.zone_confidence

        previous_metrics = self.metrics_collector.metrics[-1] if self.metrics_collector.metrics else {}
        
        net_influence = 0.0
        max_decay_rate = 0.0
        for zone in zones:
            L = zone["level"]
            key = zone['zone_key']
            params = self.settings.get_parameters(key)
            alpha = params.alpha
            threshold = params.threshold
            decay_rate = params.decay_rate
            
            prev_zone = previous_metrics.get(key, {})
            prev_level = prev_zone.get('level') if prev_zone else None
            zone_dropped = prev_level is not None and L < prev_level
            
            lower_bound = L * (1 - threshold)
            upper_bound = L * (1 + threshold)
            if lower_bound <= current_price <= upper_bound:
                proximity = 1 - abs(current_price - L) / (threshold * L)
                if current_price > L and not zone_dropped:
                    net_influence += proximity * alpha
                elif current_price < L:
                    net_influence -= proximity * alpha
                max_decay_rate = max(max_decay_rate, decay_rate)

        if abs(net_influence) < 0.1:
            decay = max_decay_rate or self.settings.default_params.decay_rate
            self.zone_confidence *= (1 - decay)

        old_confidence = self.zone_confidence
        self.zone_confidence = max(min(self.zone_confidence + net_influence, 1.0), 0.0)

        self.confidence_history.append(self.zone_confidence)
        if len(self.confidence_history) > self.slope_window:
            self.confidence_history = self.confidence_history[-self.slope_window:]

        return self.zone_confidence

    def calculate_confidence_slope(self, lookback=3):
        """Calculate the slope of zone_confidence as a percentage change over the last lookback intervals."""
        lookback = min(lookback, len(self.confidence_history))
        if lookback < 2:
            return 0.0

        y = np.array(self.confidence_history[-lookback:])
        x = np.arange(lookback)
        initial_confidence = y[0]
        final_confidence = y[-1]
        
        if initial_confidence == 0:
            return 0.0 if final_confidence == 0 else (1.0 if final_confidence > 0 else -1.0)

        pct_change = (final_confidence - initial_confidence) / initial_confidence
        slope = pct_change / (lookback - 1)
        normalized_slope = max(min(slope, 1.0), -1.0)
        return normalized_slope