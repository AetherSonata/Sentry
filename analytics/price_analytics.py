import numpy as np

# RSI Calculation
def calculate_rsi(prices, period=14):
    """
    Calculates the Relative Strength Index (RSI) using a method similar to TradingView's RSI.

    :param prices: List or NumPy array of closing prices
    :param period: RSI calculation period (default: 14)
    :return: RSI value as a float
    """
    if len(prices) < period + 1:
        raise ValueError(f"Not enough data points to calculate RSI. Required: {period+1}, Given: {len(prices)}")

    # Calculate price changes
    changes = np.diff(prices)

    # Separate gains and losses
    gains = np.where(changes >= 0, changes, 0)
    losses = np.where(changes < 0, -changes, 0)

    # Compute the smoothed moving averages of gains and losses using Wilder's smoothing (RMA)
    def rma(values, length):
        rma_values = np.zeros_like(values)
        rma_values[0] = np.mean(values[:length])  # Initial value is the SMA of the first 'length' values
        for i in range(1, len(values)):
            rma_values[i] = (rma_values[i - 1] * (length - 1) + values[i]) / length
        return rma_values

    avg_gain = rma(gains, period)[-1]
    avg_loss = rma(losses, period)[-1]

    # Avoid division by zero
    if avg_loss == 0:
        return 100  # RSI is 100 if there are no losses

    # Calculate Relative Strength (RS) and RSI
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return round(rsi, 2)  # Round to 2 decimal places


def calculate_rsi_for_intervals(historical_data, min_interval, max_interval, starting_index):
    """
    Calculates and prints RSI for different intervals from starting point.

    :param historical_data: Full dataset of historical price data.
    :param min_interval: The smallest interval to calculate RSI for.
    :param max_interval: The largest interval to calculate RSI for.
    :param starting_index: Index from where to start the RSI calculation.
    :return: A dictionary containing RSI values for each interval.
    """
    intervals = ["1m", "5m", "15m", "30m", "1H", "4H", "12H", "1D", "3D", "1W"]
    period_counts = {
        "1m": 1, "5m": 5, "15m": 15, "30m": 30, "1H": 60,
        "4H": 240, "12H": 720, "1D": 1440, "3D": 4320, "1W": 10080
    }

    # Initialize dictionary to store RSI values
    rsi_values = {}

    # Extract price data from the starting index onward
    data_points = historical_data["data"]["items"]
    for interval in intervals:
        if interval < min_interval or interval > max_interval:
            continue  # Only calculate RSI for intervals in the given range

        step_size = period_counts[interval] // period_counts["15m"]  # Convert steps to 15m intervals
        required_points = 14 + 1  # We need 15 points to calculate RSI

        # Extract price data based on the interval's step size
        price_data = [entry["value"] for entry in data_points[starting_index::step_size]]

        if len(price_data) < required_points:
            print(f"⚠️ Not enough data for {interval} RSI (required {required_points}, found {len(price_data)})")
            continue

        # Calculate RSI for the current interval
        rsi = calculate_rsi(price_data, period=14)
        rsi_values[interval] = rsi

        # Print the RSI for the interval
        print(f"✅ RSI ({interval}): {rsi}")

    return rsi_values
