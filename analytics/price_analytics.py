import numpy as np

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


def calculate_rsi_for_intervals(historical_data, period_counts):
    """
    Calculates and prints RSI for different intervals at the starting position.
    
    :param historical_data: Full dataset of historical price data.
    :param starting_data: Subset of historical data used for RSI calculations.
    :param period_counts: Dictionary mapping intervals to minutes.
    """
    intervals = ["15m", "30m", "1H", "4H"]
    
    # Extract price data for each interval
    for interval in intervals:
        period = 14  # Standard RSI calculation period

        # Find how many data points we need
        required_points = period + 1  # 15 points (RSI needs 14 previous changes)
        step_size = period_counts[interval] // period_counts["15m"]  # Convert to 15m steps

        # Extract price data
        price_data = [entry["value"] for entry in historical_data["data"]["items"][-(required_points * step_size) :: step_size]]

        if len(price_data) < required_points:
            print(f"⚠️ Not enough data for {interval} RSI (required {required_points}, found {len(price_data)})")
            continue

        # Calculate RSI
        rsi = calculate_rsi(price_data, period)
        print(f"✅ RSI ({interval}): {rsi}")


