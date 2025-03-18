class ConfidenceCalculator:
    def __init__(self, metrics_collector, alpha=0.01, threshold=0.1):
        self.metrics_collector = metrics_collector
        self.zone_confidence = 0.0
        self.alpha = alpha
        self.threshold = threshold

    def calculate_zone_confidence(self, current_price):
        zones = self.metrics_collector.zones
        # print(f"Zones in calculate_zone_confidence: {zones}")
        
        # Handle invalid zones format
        if not zones or not all(isinstance(z, dict) and "zone_level" in z for z in zones):
            print("Warning: Zones are empty or not in dict format, using current confidence")
            return self.zone_confidence

        zones_below = [z for z in zones if z["zone_level"] < current_price]
        zones_above = [z for z in zones if z["zone_level"] > current_price]

        zone_below = max(zones_below, key=lambda z: z["zone_level"]) if zones_below else None
        zone_above = min(zones_above, key=lambda z: z["zone_level"]) if zones_above else None

        influence = 0.0

        if zone_below:
            L_below = zone_below["zone_level"]
            S_below = zone_below.get("strength", 1.0 if zone_below["is_major"] else 0.5)
            lower_bound = L_below * (1 - self.threshold)
            upper_bound = L_below * (1 + self.threshold)
            if lower_bound <= current_price <= upper_bound:
                proximity = 1 - abs(current_price - L_below) / (self.threshold * L_below)
                influence += S_below * proximity

        if zone_above:
            L_above = zone_above["zone_level"]
            S_above = zone_above.get("strength", 1.0 if zone_above["is_major"] else 0.5)
            lower_bound = L_above * (1 - self.threshold)
            upper_bound = L_above * (1 + self.threshold)
            if lower_bound <= current_price <= upper_bound:
                proximity = 1 - abs(current_price - L_above) / (self.threshold * L_above)
                influence -= S_above * proximity

        if influence != 0.0:
            self.zone_confidence = max(min(self.zone_confidence + self.alpha * influence, 1.0), -1.0)
            print(f"Zone confidence updated: {self.zone_confidence}")
        return self.zone_confidence