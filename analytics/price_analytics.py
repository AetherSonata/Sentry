import numpy as np

# Convert interval strings to minutes
interval_map = {
    "1m": 1, "5m": 5, "15m": 15, "30m": 30, "1H": 60,
    "4H": 240, "12H": 720, "1D": 1440, "3D": 4320, "1W": 10080
}

def calculate_rsi(prices, period=14):
    """
    Calculates the Relative Strength Index (RSI) using a method similar to TradingView's RSI.
    
    :param prices: List or NumPy array of closing prices
    :param period: RSI calculation period (default: 14)
    :return: RSI value as a float
    """
    if len(prices) < period + 1:
        raise ValueError(f"Not enough data points to calculate RSI. Required: {period+1}, Given: {len(prices)}")

    changes = np.diff(prices)
    gains = np.where(changes >= 0, changes, 0)
    losses = np.where(changes < 0, -changes, 0)

    def rma(values, length):
        rma_values = np.zeros_like(values)
        rma_values[0] = np.mean(values[:length])
        for i in range(1, len(values)):
            rma_values[i] = (rma_values[i - 1] * (length - 1) + values[i]) / length
        return rma_values

    avg_gain = rma(gains, period)[-1]
    avg_loss = rma(losses, period)[-1]

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 2)

def calculate_rsi_for_intervals(historical_data, min_interval, max_interval, current_point):
    """
    Calculates RSI for different intervals using the 60 points before current_point as the last point.
    
    :param historical_data: Dataset of historical price data (15-minute granularity).
    :param min_interval: Smallest interval (e.g., "15m").
    :param max_interval: Largest interval (e.g., "1H").
    :param current_point: Index of the last data point for RSI calculation.
    """
    DATA_RESOLUTION_MINUTES = 15  # Data is in 15-minute intervals
    min_interval_minutes = interval_map[min_interval]
    max_interval_minutes = interval_map[max_interval]
    data_points = historical_data["data"]["items"]
    rsi_results = {}

    if current_point < 60:
        raise ValueError(f"current_point {current_point} must have at least 60 prior points, but dataset starts at 0")

    for interval in interval_map:
        interval_minutes = interval_map[interval]
        
        if interval_minutes < min_interval_minutes or interval_minutes > max_interval_minutes:
            continue

        # Calculate step size based on data resolution (15 minutes)
        step_size = max(1, interval_minutes // DATA_RESOLUTION_MINUTES)  # e.g., 15/15=1, 30/15=2, 60/15=4
        required_points = 14 + 1  # Need 15 points for RSI with period=14

        # Calculate how many points we need before current_point
        total_points_needed = required_points * step_size  # e.g., 15*1=15, 15*2=30, 15*4=60

        if current_point - total_points_needed + 1 < 0:
            print(f"⚠️ Not enough prior data for {interval} RSI (required {total_points_needed} points before index {current_point})")
            continue

        # Get the price data, working backwards from current_point
        price_data = []
        for i in range(current_point - (required_points - 1) * step_size, current_point + 1, step_size):
            price_data.append(data_points[i]["value"])

        if len(price_data) != required_points:
            print(f"⚠️ Unexpected data length for {interval} RSI (expected {required_points}, got {len(price_data)})")
            continue

        rsi = calculate_rsi(price_data)
        rsi_results[interval] = rsi
        print(f"✅ RSI ({interval}): {rsi}")

    return rsi_results