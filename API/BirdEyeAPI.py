import requests

import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()
BIRDEYE_API_URL = "https://public-api.birdeye.so/defi/history_price"
API_KEY = os.getenv("BIRDEYE_API_KEY")  # Replace with your Birdeye API key

def get_historical_price(token_address, interval, periods, chain="solana"):
    """
    Fetches historical price data for a given token from Birdeye API.

    :param token_address: The mint address of the token.
    :param interval: Time interval (15m, 30m, 1h, 4h, 12h, 1d, 1week).
    :param api_key: Your Birdeye API key.
    :param chain: Blockchain network (default: "solana").
    :return: JSON response containing historical price data.
    """
    # Convert interval string to equivalent seconds
    interval_seconds = {
        "1m": 60,
        "5m": 5 * 60,
        "15m": 15 * 60,
        "30m": 30 * 60,
        "1H": 60 * 60,
        "4H": 4 * 60 * 60,
        "12H": 12 * 60 * 60,
        "1D": 24 * 60 * 60,
        "3D": 3 * 24 * 60 * 60,
        "1W": 7 * 24 * 60 * 60
    }

    if interval not in interval_seconds:
        raise ValueError("Invalid interval! Use one of: '15m', '30m', '1H', '4H', '12H', '1d', '1week'")

    # Calculate time range
    current_time = int(time.time())  # Current UNIX timestamp
    time_from = current_time - (interval_seconds[interval] * periods)  # 15 periods back for RSI calculation

    # Construct API request
    params = {
        "address": token_address,
        "address_type": "token",
        "type": interval,
        "time_from": time_from,
        "time_to": current_time
    }

    headers = {
        "accept": "application/json",
        "x-chain": chain,
        "x-api-key": API_KEY
    }

    try:
        response = requests.get(BIRDEYE_API_URL, headers=headers, params=params)
        
        if response.status_code == 200:
            return response.json()  # Returns historical price data
        else:
            print(f"Error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
    
