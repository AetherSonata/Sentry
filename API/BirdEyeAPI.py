import requests

import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()
BIRDEYE_API_URL = "https://public-api.birdeye.so/defi/history_price"
BIRDEYE_API_URL_OHLCV = "https://public-api.birdeye.so/defi/ohlcv"
API_KEY = os.getenv("BIRDEYE_API_KEY")  # Replace with your Birdeye API key

def get_historical_price(token_address, interval, time_from, time_to, chain="solana"):
    """
    Fetches historical price data for a given token from Birdeye API.
    """
    params = {
        "address": token_address,
        "address_type": "token",
        "type": interval,
        "time_from": time_from,
        "time_to": time_to
    }
    headers = {
        "accept": "application/json",
        "x-chain": chain,
        "x-api-key": API_KEY
    }
    try:
        response = requests.get(BIRDEYE_API_URL, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    

def get_historical_ohlcv_price_data(token_address, interval, time_from, time_to, chain="solana"):
    """
    Fetches historical OHLCV data for a given token from Birdeye API.
    """
    params = {
        "address": token_address,
        "type": interval,  # Interval should match Birdeye's format (e.g., "15m", "1h")
        "time_from": time_from,
        "time_to": time_to
    }
    headers = {
        "accept": "application/json",
        "x-chain": chain,
        "X-API-KEY": API_KEY
    }
    
    try:
        response = requests.get(BIRDEYE_API_URL_OHLCV, headers=headers, params=params)
        response.raise_for_status()  # Raise an error for HTTP codes 4xx/5xx
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API request error: {e}")
        return None