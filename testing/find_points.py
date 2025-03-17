class PointFinder:
    def __init__(self, metrics):
        self.metrics = metrics

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
        targets = []
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
                targets.append(i)
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

        return targets
    
    def get_indexed_metrics(self, indexes, lower_bound=0):
        # Filter indexes to include only those > lower_bound and within self.metrics bounds
        valid_indexes = [idx for idx in indexes if idx > lower_bound and idx < len(self.metrics)]
        
        # Return corresponding metrics
        return [self.metrics[idx] for idx in valid_indexes]
    
    
    def find_fib_618_retracement_recovery(self, tolerance=0.05):
        """
        Find the first index after a pump's ATH where price hits ~61.8% (± tolerance),
        then only increases until exceeding the ATH.

        Args:
            tolerance (float): Percentage tolerance around 61.8% (e.g., 0.05 for ±5%).

        Returns:
            list: List of indices, each the first retracement point before a monotonic rise past ATH.
        """
        retracement_indices = []
        n = len(self.metrics)
        i = 0

        while i < n - 2:  # Need at least 3 points for pump, retrace, recover
            start_price = self.metrics[i]["price"]
            if start_price <= 0:  # Skip invalid prices
                i += 1
                continue

            # Find the pump peak (ATH) after the start
            ath_price = start_price
            ath_idx = i
            for j in range(i + 1, n):
                current_price = self.metrics[j]["price"]
                if current_price > ath_price:
                    ath_price = current_price
                    ath_idx = j
                elif current_price < start_price:  # Drop below start ends the pump
                    break
                if j == n - 1:  # Reached end without breaking
                    break

            # If no higher peak found, move to next point
            if ath_idx == i:
                i += 1
                continue

            # Calculate 61.8% retracement level with tolerance
            price_range = ath_price - start_price
            fib_618_level = ath_price - (price_range * 0.618)
            lower_bound = fib_618_level * (1 - tolerance)
            upper_bound = fib_618_level * (1 + tolerance)

            # Look for the first retracement point hitting ~61.8%
            retrace_idx = None
            for k in range(ath_idx + 1, n):
                current_price = self.metrics[k]["price"]
                if lower_bound <= current_price <= upper_bound:
                    retrace_idx = k
                    break
                # If price drops below start or rises above ATH before retracing, skip
                if current_price < start_price or current_price > ath_price:
                    break

            if retrace_idx is None:
                i = ath_idx + 1
                continue

            # Check if price only increases from retrace_idx and hits ATH
            valid_recovery = True
            last_price = self.metrics[retrace_idx]["price"]
            reached_ath = False

            for m in range(retrace_idx + 1, n):
                current_price = self.metrics[m]["price"]
                if current_price < last_price:  # Price dipped, invalid
                    valid_recovery = False
                    break
                if current_price >= ath_price:  # Reached or exceeded ATH
                    reached_ath = True
                    break
                last_price = current_price

            if valid_recovery and reached_ath:
                retracement_indices.append(retrace_idx)
                i = m + 1  # Skip past the recovery point
            else:
                i = ath_idx + 1  # Move past the ATH if no valid recovery

        return retracement_indices