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
        Find indices where price pumps to an ATH, retraces to ~61.8% (± tolerance), and recovers above ATH.

        Args:
            tolerance (float): Percentage tolerance around 61.8% (e.g., 0.05 for ±5%).

        Returns:
            list: List of lists, where each sublist contains indices of the retracement zone
                  (from ATH to just before recovery above ATH).
        """
        retracement_zones = []
        n = len(self.metrics)
        i = 0

        while i < n - 2:  # Need at least 3 points to check pump, retrace, recover
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

            # Look for retracement to ~61.8% level
            retrace_start = ath_idx
            retrace_end = None
            min_price = ath_price
            min_idx = ath_idx

            for k in range(ath_idx + 1, n):
                current_price = self.metrics[k]["price"]
                if current_price < min_price:
                    min_price = current_price
                    min_idx = k

                # Check if price enters the 61.8% retracement zone
                if lower_bound <= current_price <= upper_bound:
                    retrace_end = k
                    break
                # If price drops below start or rises above ATH, stop looking for retracement
                if current_price < start_price or current_price > ath_price:
                    break

            # If no retracement found within tolerance, move past the ATH
            if retrace_end is None:
                i = ath_idx + 1
                continue

            # Look for recovery above ATH
            recovery_idx = None
            for m in range(retrace_end + 1, n):
                if self.metrics[m]["price"] > ath_price:
                    recovery_idx = m
                    break
                # If price drops below start before recovering, invalid pattern
                if self.metrics[m]["price"] < start_price:
                    break

            # If recovery found, store the retracement zone indices
            if recovery_idx is not None:
                retracement_zone = list(range(ath_idx, recovery_idx))
                retracement_zones.append(retracement_zone)
                i = recovery_idx + 1  # Skip past the recovery point
            else:
                i = ath_idx + 1  # Move past the ATH if no recovery

        return retracement_zones