from API.BirdEyeAPI import get_historical_price
from testing.visualization import PricePlotter
from datetime import datetime
import time
import json
import os


def fetch_data_by_date(address, interval, start_timestamp, end_timestamp, chunk_size=10000, chain="solana"):
    """
    Fetches historical price data between a given start and end timestamp in chunks, working backwards.

    :param address: Token address.
    :param interval: Interval string (e.g., "15m", "1H", etc.).
    :param start_timestamp: The earliest UNIX timestamp to fetch.
    :param end_timestamp: The latest UNIX timestamp to fetch.
    :param chunk_size: Maximum number of data points to fetch per API call.
    :param chain: Blockchain network (default: "solana").
    :return: Dictionary with {"data": {"items": all_data}} in chronological order.
    """
    interval_seconds = {
        "1m": 60, "5m": 5 * 60, "15m": 15 * 60, "30m": 30 * 60,
        "1H": 60 * 60, "4H": 4 * 60 * 60, "12H": 12 * 60 * 60,
        "1D": 24 * 60 * 60, "3D": 3 * 24 * 60 * 60, "1W": 7 * 24 * 60 * 60
    }
    
    if interval not in interval_seconds:
        raise ValueError("Invalid interval! Use one of: '1m', '5m', '15m', '30m', '1H', '4H', '12H', '1D', '3D', '1W'")
    
    all_data = []
    time_to = end_timestamp  # Start from the newest data
    delta = chunk_size * interval_seconds[interval]  # Time range for each chunk

    iterations = 0
    while time_to > start_timestamp:
        iterations += 1
        time_from = max(start_timestamp, time_to - delta)  # Ensure we don’t go before start_timestamp
        
        print(f"Fetching from {time_from} to {time_to}...")
        time.sleep(5)
        
        data_chunk = get_historical_price(address, interval, time_from, time_to, chain=chain)
        
        if isinstance(data_chunk, dict) and "success" in data_chunk and not data_chunk["success"]:
            if "Too many requests" in data_chunk.get("message", ""):
                print("Rate limit hit! Returning fetched data so far.")
                break
        
        if data_chunk and "data" in data_chunk and "items" in data_chunk["data"]:
            items = data_chunk["data"]["items"]
            
            if not items:
                print("No more data returned. Stopping fetch.")
                break
            
            all_data = items + all_data  # Prepend to maintain chronological order
            
            if len(items) < chunk_size:
                print(f"Received only {len(items)} items, stopping fetch.")
                break
        else:
            print("Unexpected API response format. Stopping fetch.")
            break
        
        try:
            oldest_timestamp = min(int(item["unixTime"]) for item in items)
        except Exception as e:
            print(f"Error retrieving timestamp: {e}")
            break
        
        if oldest_timestamp >= time_to:
            print("Timestamps did not decrease, stopping to prevent infinite loop.")
            break
        
        time_to = oldest_timestamp  # Move backwards
    
    print(f"Loop executed {iterations} times.")
    return {"data": {"items": all_data}}

def fetch_complete_test_data(address, interval, span_in_days, chunk_size=1000, chain="solana"):
    """
    Fetches historical price data in chunks until the span (in days) is covered.
    
    Fetches the newest data first and works backwards in chunks.
    
    :param address: Token address.
    :param interval: Interval string (e.g., "15m", "1H", etc.).
    :param span_in_days: Number of days of historical data desired.
    :param chunk_size: Maximum number of data points to fetch per API call.
    :param chain: Blockchain network (default: "solana").
    :return: Dictionary with {"data": {"items": all_data}} where all_data is in chronological order.
    """
    
    interval_seconds = {
        "1m": 60, "5m": 5 * 60, "15m": 15 * 60, "30m": 30 * 60,
        "1H": 60 * 60, "4H": 4 * 60 * 60, "12H": 12 * 60 * 60,
        "1D": 24 * 60 * 60, "3D": 3 * 24 * 60 * 60, "1W": 7 * 24 * 60 * 60
    }
    
    if interval not in interval_seconds:
        raise ValueError("Invalid interval! Use one of: '1m', '5m', '15m', '30m', '1H', '4H', '12H', '1D', '3D', '1W'")
    
    span_seconds = span_in_days * 24 * 60 * 60  # Total time span in seconds
    current_time = int(time.time())  # Current UNIX timestamp
    desired_start = current_time - span_seconds  # Target start timestamp
    
    all_data = []  # Store results
    time_to = current_time  # Start from now and move backwards
    delta = chunk_size * interval_seconds[interval]  # Time step per chunk

    iterations = 0  # API call counter
    
    while time_to > desired_start:
        iterations += 1
        time_from = max(desired_start, time_to - delta)  # Ensure we do not go past the earliest point

        print(f"Fetching from {time_from} to {time_to}...")  # Debugging log

        time.sleep(5)  # Prevent rate limiting
        
        data_chunk = get_historical_price(address, interval, time_from, time_to, chain=chain)

        if isinstance(data_chunk, dict) and "success" in data_chunk and not data_chunk["success"]:
            if "Too many requests" in data_chunk.get("message", ""):
                print("Rate limit hit! Returning fetched data so far.")
                break  # Stop and return what we have

        if data_chunk and "data" in data_chunk and "items" in data_chunk["data"]:
            items = data_chunk["data"]["items"]
            
            if not items:
                print("No more data returned. Stopping fetch.")
                break  # Stop if API returns empty data
            
            # Prepend data instead of appending (to keep chronological order)
            all_data = items + all_data
            
            # Stop if we receive fewer items than expected
            if len(items) < chunk_size:
                print(f"Received only {len(items)} items (less than chunk_size), stopping fetch.")
                break

        else:
            print("Unexpected API response format. Stopping fetch.")
            break
        
        try:
            oldest_timestamp = min(int(item["unixTime"]) for item in items)  # Find the oldest timestamp in chunk
        except Exception as e:
            print(f"Error retrieving timestamp: {e}")
            break
        
        if oldest_timestamp >= time_to:  # Ensure we are moving backwards
            print("Timestamps did not decrease, stopping to prevent infinite loop.")
            break
        
        time_to = oldest_timestamp  # Move backwards
    
    print(f"Loop executed {iterations} times.")
    return {"data": {"items": all_data}}  # Now already in chronological order



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


