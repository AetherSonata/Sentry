import numpy as np
from scipy.cluster.hierarchy import linkage, fcluster

class SupportResistanceDetector:
    def __init__(self, price_data, interval):
        # Extract values from the price data, we only care about the 'value' field for prices.
        self.prices = np.array([entry['value'] for entry in price_data])  # Store price data
        self.support_zones = []
        self.resistance_zones = []
        self.price_data = price_data
        self.interval = interval

    def calculate_average_price(self):
        """
        Calculate the average price depending on the chart interval and data age.
        """
        start_time = self.price_data[0]['unixTime']
        end_time = self.price_data[-1]['unixTime']
        duration_seconds = end_time - start_time
        
        interval_mapping = {
            '1m': 1, '5m': 5, '15m': 15, '30m': 30, '1h': 60, '4h': 240, '12h': 720, '1d': 1440, '1w': 10080
        }
        
        interval_minutes = interval_mapping.get(self.interval, 60)
        
        # Adjust number of data points based on duration
        if duration_seconds <= 3600:
            num_points = min(10, len(self.prices))
        elif duration_seconds <= 86400:
            num_points = min(20, len(self.prices))
        elif duration_seconds <= 604800:
            num_points = min(50, len(self.prices))
        else:
            num_points = min(100, len(self.prices))
        
        avg_price = np.mean(self.prices[-num_points:])
        return avg_price

    def calculate_volatility(self):
        """Calculate normalized volatility based on the standard deviation of price returns."""
        if len(self.prices) < 2:
            return 0

        # Compute percentage returns
        returns = [(self.prices[i] - self.prices[i-1]) / self.prices[i-1] for i in range(1, len(self.prices))]

        volatility = np.std(returns)  # Standard deviation of returns
        return volatility * 100  # Normalize to percentage

    def _adaptive_cluster_threshold(self):
        """Dynamically adjust the clustering threshold based on data density and volatility."""
        volatility = self.calculate_volatility()
        
        # Get price spread
        price_range = np.ptp(self.prices)  # Peak-to-peak price range
        
        # Adjust base threshold using volatility and price range, making it more dynamic
        base_threshold = 0.005 * price_range
        adaptive_threshold = base_threshold * (1 + volatility / 50)  # Modulate by volatility

        return adaptive_threshold

    def _cluster_price_points(self):
        """Cluster price points using hierarchical clustering based on proximity, adjusted for dynamic threshold."""
        if len(self.prices) < 2:
            return []

        # Calculate the adaptive threshold for clustering
        adaptive_threshold = self._adaptive_cluster_threshold()

        # Perform hierarchical clustering with dynamic threshold
        linked = linkage(self.prices.reshape(-1, 1), method='ward')
        
        # Assign cluster labels based on adaptive price distance threshold
        clusters = fcluster(linked, t=adaptive_threshold, criterion='distance')

        # Group price points by cluster
        cluster_dict = {}
        for price, cluster_id in zip(self.prices, clusters):
            cluster_dict.setdefault(cluster_id, []).append(price)

        return list(cluster_dict.values())

    def _calculate_zones(self, clusters):
        """Calculate support/resistance zones with better-defined logic."""
        zones = []
        for cluster in clusters:
            cluster = np.array(cluster)
            avg_price = np.mean(cluster)
            min_price = np.min(cluster)
            max_price = np.max(cluster)
            density = len(cluster)  # Density is based on the number of price points in the cluster

            # Use density to categorize strength
            strength = "weak"
            if density > 15:
                strength = "strong"
            elif density > 7:
                strength = "medium"

            zones.append({
                "average": avg_price,
                "range": (min_price, max_price),
                "strength": strength,
                "density": density
            })

        # Sort by average price (ascending order)
        return sorted(zones, key=lambda x: x["average"])

    def find_support_resistance_zones(self):
        """Detect both support and resistance zones with improved logic."""
        clusters = self._cluster_price_points()

        # Separate into support and resistance based on price action
        mid_price = np.median(self.prices)
        
        supports = [c for c in clusters if np.mean(c) < mid_price]
        resistances = [c for c in clusters if np.mean(c) > mid_price]

        # Refine the zones to ensure resistance is above the current price
        self.support_zones = self._calculate_zones(supports)
        self.resistance_zones = self._calculate_zones([c for c in resistances if np.mean(c) > max(self.prices)])

        return {
            "support_zones": self.support_zones,
            "resistance_zones": self.resistance_zones
        }
