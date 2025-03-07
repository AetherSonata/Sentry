from API.dexScreenerAPI import get_historical_price
from analytics.price_analytics import calculate_rsi_for_intervals
from testing.visualization import PricePlotter
from datetime import datetime
import time


def get_historical_test_data(address, interval, span_in_days):
    periods = {
        "1m": 60 / 1 * 24,
        "5m": 60 / 5 * 24,
        "15m": 60 / 15 * 24,
        "30m": 60 / 30 * 24,
        "1H": 24,
        "4H": 4,
        "12H": 2,
        "1D": 1,
        "3D": 1/3,
        "1W": 1/7
    }
    
    # Calculate required number of data points
    num_points = int(periods[interval] * span_in_days)
    
    # Fetch historical data
    test_data = get_historical_price(address, interval, num_points)

    # print(f"{len(test_data['data']['items'])} data points fetched.")
    return test_data


def find_starting_point(historical_data, interval):
    """
    Determines the best possible starting point index for RSI calculation with at least 15 data points.
    Adjusts to the largest usable interval based on available data.

    :param historical_data: Dictionary containing price history.
    :param interval: The requested interval (e.g., "15m", "1H").
    :return: (starting_index, best_interval)
    """
    intervals = ["1m", "5m", "15m", "30m", "1H", "4H", "12H", "1D", "3D", "1W"]
    period_counts = { 
        "1m": 1, "5m": 5, "15m": 15, "30m": 30, "1H": 60,
        "4H": 240, "12H": 720, "1D": 1440, "3D": 4320, "1W": 10080
    }
    
    total_points = len(historical_data)
    
    # Find the largest interval that allows at least 15 data points
    available_intervals = [i for i in intervals if total_points >= 15 * (period_counts[i] // period_counts[interval])]
    
    if not available_intervals:
        raise ValueError("Not enough data points to calculate RSI with any reasonable interval.")
    
    best_interval = available_intervals[-1]  # Choose the largest usable interval
    step_size = period_counts[best_interval] // period_counts[interval]
    starting_index = min(15 * step_size, total_points - 1)


    return starting_index, best_interval




