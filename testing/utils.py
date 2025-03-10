from API.BirdEyeAPI import get_historical_price
from testing.visualization import PricePlotter
from datetime import datetime
import time
import json
import os


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
    
    best_interval = available_intervals[-2]  # Choose the largest usable interval
    step_size = period_counts[best_interval] // period_counts[interval]
    starting_index = min(15 * step_size, total_points - 1) + 50


    return starting_index, best_interval




def save_historical_price(data, filename="historical_price.json"):
    """
    Saves historical price data to a JSON file.
    
    :param data: The historical price data (dictionary) to save.
    :param filename: The name of the file to store data.
    """
    if data is None:
        print("No data to save.")
        return
    
    try:
        with open(filename, "w") as file:
            json.dump(data, file, indent=4)
        print(f"Data successfully saved to {filename}")
    except Exception as e:
        print(f"Error saving data: {e}")

def load_historical_price(filename="historical_price.json"):
    """
    Loads historical price data from a JSON file.

    :param filename: The name of the file to read data from.
    :return: The historical price data in the same format as returned by `get_historical_price`.
    """
    if not os.path.exists(filename):
        print("No stored data found.")
        return None

    try:
        with open(filename, "r") as file:
            data = json.load(file)
        return data
    except Exception as e:
        print(f"Error loading data: {e}")
        return None


