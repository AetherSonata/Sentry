from analytics.time_utils import get_interval_in_minutes
from collections import defaultdict
from typing import Dict, List
from datetime import datetime
import pandas as pd

class IntervalDataAggregator:
    def __init__(self, metrics_collector):
        """
        Initialize aggregator for multi-time-frame OHLCV data.

        Args:
            metrics_collector: Instance of MetricCollector, providing base interval and other attributes.
        """
        self.metrics_collector = metrics_collector
        self.base_interval = metrics_collector.interval
        self.base_interval_in_minutes = get_interval_in_minutes(self.base_interval)
        if self.base_interval_in_minutes is None:
            raise ValueError(f"Invalid base interval: {self.base_interval}")

        # Interval-based OHLCV data
        self.interval_price_data = defaultdict(list)  # {interval_minutes: [{'timestamp', 'open', 'high', 'low', 'close', 'volume'}, ...]}
        self.partial_candles = defaultdict(list)  # {interval_minutes: [price_points for current candle]}
        self.target_intervals = None  # Set in initialize_intervals

    def initialize_intervals(self, target_intervals: List[int] = None) -> None:
        """
        Initialize base interval and target intervals for OHLCV data aggregation.

        Args:
            target_intervals: List of target interval minutes (e.g., [60, 240] for 1h, 4h).
                              Defaults to [60, 240].
        """
        self.target_intervals = target_intervals if target_intervals is not None else [60, 240]
        # Initialize base interval
        if self.base_interval_in_minutes not in self.interval_price_data:
            self.interval_price_data[self.base_interval_in_minutes] = []
        # Initialize target intervals
        for interval_minutes in self.target_intervals:
            if interval_minutes not in self.interval_price_data:
                self.interval_price_data[interval_minutes] = []

    def update_interval_data(self, price_point: Dict, ohlcv: bool = False) -> Dict[int, List[Dict]]:
        """
        Update interval-based OHLCV data with a new price point.

        Args:
            price_point: Dict with 'value' and 'unixTime' (or OHLCV if ohlcv=True).
            ohlcv: If True, treat as OHLCV.

        Returns:
            Dict: {interval_minutes: [new_candles]} for completed candles.
        """
        # Initialize intervals if not already done
        if self.target_intervals is None:
            self.initialize_intervals()

        # Normalize price point to OHLCV format
        timestamp = datetime.fromtimestamp(price_point['unixTime'])
        if ohlcv:
            candle = {
                'timestamp': timestamp,
                'open': price_point['open'],
                'high': price_point['high'],
                'low': price_point['low'],
                'close': price_point['close'],
                'volume': price_point.get('volume', 0)
            }
        else:
            candle = {
                'timestamp': timestamp,
                'open': price_point['value'],
                'high': price_point['value'],
                'low': price_point['value'],
                'close': price_point['value'],
                'volume': price_point.get('volume', 0)
            }

        # Add to base interval (e.g., 5m)
        self.interval_price_data[self.base_interval_in_minutes].append(candle)

        # Update larger intervals
        new_candles = {}
        for interval_minutes in self.target_intervals:
            # Add to partial candle
            self.partial_candles[interval_minutes].append(candle)

            # Determine if the candle is complete based on timestamp
            if self.partial_candles[interval_minutes]:
                latest_ts = self.partial_candles[interval_minutes][-1]['timestamp']
                # Calculate the start of the current interval
                interval_start = latest_ts - pd.Timedelta(minutes=latest_ts.minute % interval_minutes,
                                                        seconds=latest_ts.second,
                                                        microseconds=latest_ts.microsecond)
                # Check if the next price point would fall into a new interval
                next_ts = latest_ts + pd.Timedelta(minutes=self.base_interval_in_minutes)
                next_interval_start = next_ts - pd.Timedelta(minutes=next_ts.minute % interval_minutes,
                                                           seconds=next_ts.second,
                                                           microseconds=next_ts.microsecond)
                if interval_start != next_interval_start:
                    # Complete the candle
                    df = pd.DataFrame(self.partial_candles[interval_minutes])
                    new_candle = {
                        'timestamp': interval_start + pd.Timedelta(minutes=interval_minutes),  # End of interval
                        'open': df['open'].iloc[0],
                        'high': df['high'].max(),
                        'low': df['low'].min(),
                        'close': df['close'].iloc[-1],
                        'volume': df['volume'].sum()
                    }
                    self.interval_price_data[interval_minutes].append(new_candle)
                    new_candles[interval_minutes] = [new_candle]
                    self.partial_candles[interval_minutes] = []  # Reset partial candle

        return new_candles

    def get_interval_data(self, interval_minutes: int, window: int = None) -> List[Dict]:
        """
        Retrieve OHLCV data for a specific interval.

        Args:
            interval_minutes: Target interval in minutes (e.g., 60 for 1h).
            window: Number of candles to return (optional).

        Returns:
            List of dicts with OHLCV data.
        """
        data = self.interval_price_data.get(interval_minutes, [])
        if window:
            return data[-window:]
        return data

    def determine_largest_interval(self) -> int:
        """
        Suggest the largest relevant interval based on token age.

        Returns:
            int: Largest interval in minutes (e.g., 1440 for 1D).
        """
        if not self.interval_price_data[self.base_interval_in_minutes]:
            return self.base_interval_in_minutes
        age_minutes = (self.interval_price_data[self.base_interval_in_minutes][-1]['timestamp'] -
                       self.interval_price_data[self.base_interval_in_minutes][0]['timestamp']).total_seconds() / 60
        available_intervals = sorted(self.target_intervals + [self.base_interval_in_minutes, 1440, 10080, 43200])
        for interval in reversed(available_intervals):
            if age_minutes >= 2 * interval:  # At least 2 candles
                return interval
        return self.base_interval_in_minutes