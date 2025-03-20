import numpy as np

class ConfidenceCalculator:
    def __init__(self, metrics_collector, chart_analyzer, alpha=0.05, threshold=0.1, decay_rate=0.02, slope_window=10):
        self.metrics_collector = metrics_collector
        self.chart_analyzer = chart_analyzer
        self.zone_confidence = 0.5
        self.alpha = alpha
        self.threshold = threshold
        self.decay_rate = decay_rate
        self.slope_window = slope_window  # Maximum history to store for slope calculation
        self.confidence_history = []  # Store history of zone_confidence values

    def calculate_strength(self, zone, current_price, max_touches=10):
        """Calculate a zone's strength based on touches and proximity (same as ChartAnalyzer._rank_zones)."""
        touch_strength = zone["touches"] / max_touches
        proximity = 1 - min(abs(zone["level"] - current_price) / (current_price * 0.5), 1)
        return 0.7 * touch_strength + 0.3 * proximity

    def score_zone(self, zone, current_price, strength):
        """Score a zone based on its strength and proximity."""
        distance_pct = abs(zone["level"] - current_price) / current_price
        return strength / (1 + distance_pct)

    def calculate_zone_confidence(self, current_price):
        # Access all zones from ChartAnalyzer
        zones = self.chart_analyzer.zones

        # Handle case where zones are empty
        if not zones:
            self.confidence_history.append(self.zone_confidence)
            return self.zone_confidence

        # Split zones into support and resistance
        support_zones = [z for z in zones if z["level"] < current_price]
        resistance_zones = [z for z in zones if z["level"] > current_price]

        # Calculate influence from support zones (increases confidence)
        support_influence = 0.0
        for zone in support_zones:
            L = zone["level"]
            S = self.calculate_strength(zone, current_price)
            lower_bound = L * (1 - self.threshold)
            upper_bound = L * (1 + self.threshold)
            if lower_bound <= current_price <= upper_bound:
                proximity = 1 - abs(current_price - L) / (self.threshold * L)
                scored_strength = self.score_zone(zone, current_price, S)
                support_influence += scored_strength * proximity
            # Boost influence if price is just above a major support
            if zone["is_major"] and current_price > L and current_price <= L * 1.05:
                proximity = 1 - (current_price - L) / (0.05 * L)
                support_influence += scored_strength * proximity * 1.5

        # Calculate influence from resistance zones (decreases confidence)
        resistance_influence = 0.0
        for zone in resistance_zones:
            L = zone["level"]
            S = self.calculate_strength(zone, current_price)
            lower_bound = L * (1 - self.threshold)
            upper_bound = L * (1 + self.threshold)
            if lower_bound <= current_price <= upper_bound:
                proximity = 1 - abs(current_price - L) / (self.threshold * L)
                scored_strength = self.score_zone(zone, current_price, S)
                resistance_influence += scored_strength * proximity
            # Stronger penalty if price is just below a major resistance
            if zone["is_major"] and current_price < L and current_price >= L * 0.95:
                proximity = 1 - (L - current_price) / (0.05 * L)
                resistance_influence += scored_strength * proximity * 1.5

        # Net influence: support increases confidence, resistance decreases it
        net_influence = support_influence - resistance_influence

        # Decay confidence if price is not near any significant zone
        if abs(net_influence) < 0.1:
            self.zone_confidence *= (1 - self.decay_rate)

        # Update confidence
        self.zone_confidence = max(min(self.zone_confidence + self.alpha * net_influence, 1.0), 0.0)

        # Store the new confidence value in history
        self.confidence_history.append(self.zone_confidence)
        # Keep only the last slope_window values
        if len(self.confidence_history) > self.slope_window:
            self.confidence_history = self.confidence_history[-self.slope_window:]

        return self.zone_confidence

    def calculate_confidence_slope(self, lookback=5):
        """Calculate the slope of zone_confidence over the last lookback intervals.

        Args:
            lookback (int, optional): Number of past intervals to consider for the slope.
                                      If None, uses self.slope_window.

        Returns:
            float: Slope of zone_confidence over the specified lookback period.
        """
        if lookback is None:
            lookback = self.slope_window

        # Ensure lookback is not larger than the history
        lookback = min(lookback, len(self.confidence_history))

        if lookback < 2:  # Need at least 2 points to calculate a slope
            return 0.0

        # Use the last lookback points
        y = np.array(self.confidence_history[-lookback:])  # Confidence values
        x = np.arange(lookback)  # Time indices (0, 1, 2, ..., lookback-1)

        # Fit a linear polynomial (degree 1) and get the slope
        slope, _ = np.polyfit(x, y, 1)
        return slope