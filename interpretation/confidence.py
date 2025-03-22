import numpy as np

class ConfidenceCalculator:
    def __init__(self, metrics_collector, alpha=0.05, threshold=0.1, decay_rate=0.02, slope_window=10):
        """
        Initialize the ConfidenceCalculator with given parameters.

        Args:
            metrics_collector: Object with attributes key_zone_1 to key_zone_6 as single dicts.
            alpha (float): Rate of confidence adjustment based on zone influence (default: 0.05).
            threshold (float): Proximity threshold for zone influence (default: 0.1).
            decay_rate (float): Rate of confidence decay over time (default: 0.02).
            slope_window (int): Number of past confidence values to store for slope (default: 10).
        """
        self.metrics_collector = metrics_collector
        self.zone_confidence = 0.0  # Start at 0
        self.alpha = alpha
        self.threshold = threshold
        self.decay_rate = decay_rate
        self.slope_window = slope_window
        self.confidence_history = []

    def calculate_zone_confidence(self, current_price):
        """
        Calculate confidence based on price proximity to all zones, treating them uniformly.

        Args:
            current_price (float): Current price to evaluate against zones.

        Returns:
            float: Updated zone confidence value between 0 and 1.
        """
        # Define weightings for different zone types
        weightings = {
            'short_term': 1,
            'mid_term': 2,
            'long_term': 3
        }

        # Map zone attributes to their types
        zone_types = {
            "key_zone_1": "short_term",
            "key_zone_2": "short_term",
            "key_zone_3": "mid_term",
            "key_zone_4": "mid_term",
            "key_zone_5": "long_term",
            "key_zone_6": "long_term"
        }

        # Aggregate all zones from metrics_collector attributes
        zones = []
        for key in ["key_zone_1", "key_zone_2", "key_zone_3", "key_zone_4", "key_zone_5", "key_zone_6"]:
            zone = getattr(self.metrics_collector, key, None)
            if zone and 'level' in zone:  # Check if zone exists and is valid
                zone_copy = zone.copy()
                zone_copy['zone_type'] = zone_types[key]
                zones.append(zone_copy)

        if not zones:
            self.confidence_history.append(self.zone_confidence)
            return self.zone_confidence

        # Calculate net influence from all zones
        net_influence = 0.0
        for zone in zones:
            L = zone["level"]
            weight = weightings[zone['zone_type']]
            lower_bound = L * (1 - self.threshold)
            upper_bound = L * (1 + self.threshold)
            if lower_bound <= current_price <= upper_bound:
                proximity = 1 - abs(current_price - L) / (self.threshold * L)
                # Increase confidence if above, decrease if below
                if current_price > L:
                    net_influence += proximity * weight  # Above: increases confidence
                elif current_price < L:  # Use elif to avoid double-counting exact matches
                    net_influence -= proximity * weight  # Below: decreases confidence

        # Apply decay if price is not near significant zones
        if abs(net_influence) < 0.1:
            self.zone_confidence *= (1 - self.decay_rate)

        # Update confidence, bounded between 0 and 1
        self.zone_confidence = max(min(self.zone_confidence + self.alpha * net_influence, 1.0), 0.0)

        # Update confidence history
        self.confidence_history.append(self.zone_confidence)
        if len(self.confidence_history) > self.slope_window:
            self.confidence_history = self.confidence_history[-self.slope_window:]

        # print(f"Zone confidence: {self.zone_confidence}")
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