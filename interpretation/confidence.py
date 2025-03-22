import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class ZoneParameters:
    """Parameters for a specific zone."""
    alpha: float = 0.05  # Rate of confidence adjustment
    threshold: float = 0.2  # Proximity threshold
    decay_rate: float = 0.02  # Decay rate when not near zones


# USAGE INFO::

# # Access the settings helper
# settings = confidence_calculator.settings

# # Customize parameters for specific zones
# settings.set_zone_alpha("key_zone_1", 0.1)        # Faster adjustment for short-term support
# settings.set_zone_threshold("key_zone_2", 0.3)    # Wider range for short-term resistance
# settings.set_zone_decay_rate("key_zone_5", 0.01)  # Slower decay for long-term support

class ZoneSettings:
    """Helper class to manage settings for each unique zone."""
    def __init__(self, default_alpha=0.05, default_threshold=0.2, default_decay_rate=0.02):
        # Default global parameters
        self.default_params = ZoneParameters(
            alpha=default_alpha,
            threshold=default_threshold,
            decay_rate=default_decay_rate
        )
        # Zone-specific settings (overrides defaults if set)
        self.zone_settings: Dict[str, ZoneParameters] = {}
        # Valid zone keys
        self.valid_zones = ["key_zone_1", "key_zone_2", "key_zone_3", "key_zone_4", "key_zone_5", "key_zone_6"]

    def set_zone_alpha(self, zone_key: str, alpha: float):
        """Set alpha for a specific zone."""
        if zone_key not in self.valid_zones:
            raise ValueError(f"Invalid zone key: {zone_key}. Must be one of {self.valid_zones}")
        if zone_key not in self.zone_settings:
            self.zone_settings[zone_key] = ZoneParameters()
        self.zone_settings[zone_key].alpha = alpha

    def set_zone_threshold(self, zone_key: str, threshold: float):
        """Set threshold for a specific zone."""
        if zone_key not in self.valid_zones:
            raise ValueError(f"Invalid zone key: {zone_key}. Must be one of {self.valid_zones}")
        if zone_key not in self.zone_settings:
            self.zone_settings[zone_key] = ZoneParameters()
        self.zone_settings[zone_key].threshold = threshold

    def set_zone_decay_rate(self, zone_key: str, decay_rate: float):
        """Set decay rate for a specific zone."""
        if zone_key not in self.valid_zones:
            raise ValueError(f"Invalid zone key: {zone_key}. Must be one of {self.valid_zones}")
        if zone_key not in self.zone_settings:
            self.zone_settings[zone_key] = ZoneParameters()
        self.zone_settings[zone_key].decay_rate = decay_rate

    def get_parameters(self, zone_key: str) -> ZoneParameters:
        """Get parameters for a zone key, falling back to defaults."""
        return self.zone_settings.get(zone_key, self.default_params)

class ConfidenceCalculator:
    def __init__(self, metrics_collector, alpha=0.05, threshold=0.2, decay_rate=0.02, slope_window=10):
        """
        Initialize the ConfidenceCalculator with given parameters.

        Args:
            metrics_collector: Object with attributes key_zone_1 to key_zone_6 as single dicts.
            alpha (float): Default rate of confidence adjustment (default: 0.05).
            threshold (float): Default proximity threshold (default: 0.2).
            decay_rate (float): Default decay rate (default: 0.02).
            slope_window (int): Number of past confidence values to store for slope (default: 10).
        """
        self.metrics_collector = metrics_collector
        self.zone_confidence = 0.0
        self.slope_window = slope_window
        self.confidence_history = []
        # Initialize settings with global defaults
        self.settings = ZoneSettings(
            default_alpha=alpha,
            default_threshold=threshold,
            default_decay_rate=decay_rate
        )

    def calculate_zone_confidence(self, current_price):
        """
        Calculate confidence based on price proximity to all zones, with per-zone settings.

        Args:
            current_price (float): Current price to evaluate against zones.

        Returns:
            float: Updated zone confidence value between 0 and 1.
        """
        # Aggregate all zones from metrics_collector attributes
        zones = []
        for key in ["key_zone_1", "key_zone_2", "key_zone_3", "key_zone_4", "key_zone_5", "key_zone_6"]:
            zone = getattr(self.metrics_collector, key, None)
            if zone and 'level' in zone:
                zone_copy = zone.copy()
                zone_copy['zone_key'] = key
                zones.append(zone_copy)

        if not zones:
            # Use the default decay rate if no zones are present
            self.zone_confidence *= (1 - self.settings.default_params.decay_rate)
            self.confidence_history.append(self.zone_confidence)
            return self.zone_confidence

        # Calculate net influence from all zones
        net_influence = 0.0
        max_decay_rate = 0.0  # Track the highest decay rate among influencing zones
        for zone in zones:
            L = zone["level"]
            params = self.settings.get_parameters(zone['zone_key'])
            alpha = params.alpha
            threshold = params.threshold
            decay_rate = params.decay_rate
            lower_bound = L * (1 - threshold)
            upper_bound = L * (1 + threshold)
            if lower_bound <= current_price <= upper_bound:
                proximity = 1 - abs(current_price - L) / (threshold * L)
                if current_price > L:
                    net_influence += proximity  # Base influence
                elif current_price < L:
                    net_influence -= proximity
                max_decay_rate = max(max_decay_rate, decay_rate)  # Update max decay rate

        # Apply decay if price is not near significant zones
        if abs(net_influence) < 0.1:
            # Use the highest decay rate among zones that influenced the calculation
            self.zone_confidence *= (1 - (max_decay_rate or self.settings.default_params.decay_rate))

        # Update confidence with per-zone alpha applied to the net influence
        self.zone_confidence = max(min(self.zone_confidence + self.settings.default_params.alpha * net_influence, 1.0), 0.0)
        for zone in zones:
            params = self.settings.get_parameters(zone['zone_key'])
            alpha = params.alpha
            threshold = params.threshold
            L = zone["level"]
            lower_bound = L * (1 - threshold)
            upper_bound = L * (1 + threshold)
            if lower_bound <= current_price <= upper_bound:
                proximity = 1 - abs(current_price - L) / (threshold * L)
                if current_price > L:
                    self.zone_confidence += alpha * proximity
                elif current_price < L:
                    self.zone_confidence -= alpha * proximity
            self.zone_confidence = max(min(self.zone_confidence, 1.0), 0.0)

        # Update confidence history
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