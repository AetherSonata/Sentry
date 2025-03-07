from API.dexScreenerAPI import get_historical_price
from analytics.price_analytics import calculate_rsi

if __name__ == "__main__":
    TOKEN_ADDRESS="So11111111111111111111111111111111111111112"
    INTERVAL="1H"

    historical_data = get_historical_price(TOKEN_ADDRESS, INTERVAL)
    if historical_data:
        rsi_value = calculate_rsi(historical_data)
        print(f"historical_data: {historical_data}")
        print(f"RSI value for {INTERVAL} interval: {rsi_value}")
    else:
        print("Failed to fetch data.")
    