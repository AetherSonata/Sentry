import numpy as np
from collections import Counter

class ChartAnalyzer:
    def __init__(self, price_data, interval):
        self.price_data = price_data
        self.interval = interval
        self.prices = [entry['value'] for entry in price_data]
        
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
    

    def _get_dynamic_window_size(self):
        """Determine window size dynamically based on the number of price points."""
        length = len(self.prices)
        if length < 50:
            return 5
        elif length < 200:
            return 10
        elif length < 500:
            return 20
        else:
            return 30  # Larger dataset -> bigger window

    def _find_frequent_levels(self, prices):
        """Find the most common price levels in the list."""
        if not prices:
            return None
        counter = Counter(prices)
        most_common = counter.most_common(5)  # Get top 5 most frequent prices
        return np.mean([price for price, _ in most_common])  # Average them

    def find_support_zones(self):
        """Identify support zones and return a single averaged value for each category."""
        window_size = self._get_dynamic_window_size()
        support_zones = {'strong': [], 'weak': [], 'neutral': []}
        temp_strong, temp_weak, temp_neutral = [], [], []
        
        # Identify local min/max
        for i in range(len(self.prices) - window_size):
            window = self.prices[i:i + window_size]
            min_price = min(window)
            max_price = max(window)
            
            temp_strong.append(min_price)
            temp_weak.append(max_price)
        
        # Compute final values
        support_zones['strong'] = self._find_frequent_levels(temp_strong)
        support_zones['weak'] = self._find_frequent_levels(temp_weak)
        support_zones['neutral'] = np.mean([support_zones['strong'], support_zones['weak']]) if support_zones['strong'] and support_zones['weak'] else None

        return support_zones

    def find_resistance_zones(self):
        """Identify resistance zones and return a single averaged value for each category."""
        window_size = self._get_dynamic_window_size()
        resistance_zones = {'strong': [], 'weak': [], 'neutral': []}
        temp_strong, temp_weak, temp_neutral = [], [], []
        
        # Identify local min/max
        for i in range(len(self.prices) - window_size):
            window = self.prices[i:i + window_size]
            min_price = min(window)
            max_price = max(window)
            
            temp_strong.append(max_price)
            temp_weak.append(min_price)
        
        # Compute final values
        resistance_zones['strong'] = self._find_frequent_levels(temp_strong)
        resistance_zones['weak'] = self._find_frequent_levels(temp_weak)
        resistance_zones['neutral'] = np.mean([resistance_zones['strong'], resistance_zones['weak']]) if resistance_zones['strong'] and resistance_zones['weak'] else None

        return resistance_zones
    
    def calculate_volatility(self):
        """
        Calculate the volatility score based on the standard deviation of price returns.
        """
        returns = [(self.prices[i] - self.prices[i-1]) / self.prices[i-1] for i in range(1, len(self.prices))]
        volatility = np.std(returns)
        normalized_volatility = volatility * 100
        return normalized_volatility
    
    def analyze(self):
        """
        Analyze price data and return the average price, support zones, resistance zones, and volatility score.
        """
        avg_price = self.calculate_average_price()
        
        support_zones = self.find_support_zones()
        resistance_zones = self.find_resistance_zones()
        
        volatility_score = self.calculate_volatility()
        
        return {
            "average_price": avg_price,
            "support_zones": support_zones,
            "resistance_zones": resistance_zones,
            "volatility_score": volatility_score
        }

