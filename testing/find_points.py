class PointFinder:
    def __init__(self, metrics):
        """
        Initializes the PriceIncreaseAnalyzer with a metrics list and calculates target indices.

        Args:
            metrics (list): List of metric dictionaries, each containing a 'price' key.
            price_increase (float): Minimum factor by which price must increase (e.g., 2.0 for 2x).
        """
        self.metrics = metrics
        self.targets = self.find_significant_price_increases(price_increase=1.5)

    def find_significant_price_increases(self, price_increase):
        """
        Analyzes self.metrics to find indices where price increases by at least 'price_increase' times
        without dropping below the initial price afterward. Returns the first index in any consecutive
        sequence of qualifying points.

        Args:
            price_increase (float): Minimum factor by which price must increase (e.g., 2.0 for 2x).

        Returns:
            list: List of indices in self.metrics where the condition is met.
        """
        result = []
        n = len(self.metrics)
        i = 0

        while i < n:
            initial_price = self.metrics[i]["price"]
            if initial_price <= 0:  # Skip invalid prices
                i += 1
                continue

            target_price = initial_price * price_increase
            qualifies = False
            max_price_seen = initial_price

            # Check all subsequent points from i
            for j in range(i + 1, n):
                current_price = self.metrics[j]["price"]
                max_price_seen = max(max_price_seen, current_price)

                # If price drops below initial, this point doesn’t qualify
                if current_price < initial_price:
                    break

                # If price reaches or exceeds target without dropping below initial
                if max_price_seen >= target_price:
                    qualifies = True
                    break

            if qualifies:
                result.append(i)
                # Skip ahead to the next point after the increase to avoid overlapping sequences
                next_i = i + 1
                while next_i < n:
                    next_price = self.metrics[next_i]["price"]
                    if next_price < initial_price or next_price >= target_price:
                        break
                    next_i += 1
                i = next_i
            else:
                i += 1

        return result