import numpy as np



def calculate_rsi(historical_data, period=14):
    """
    Calculates the Relative Strength Index (RSI) using the method similar to TradingView's rsi() function.

    :param historical_data: Dictionary containing price history in the format {'data': {'items': [{'unixTime': ..., 'value': ...}]}}
    :param period: RSI calculation period (default: 14)
    :return: RSI value as a float
    """
    if "data" not in historical_data or "items" not in historical_data["data"]:
        raise ValueError("Invalid data format: Missing 'items' key.")

    prices = np.array([entry["value"] for entry in historical_data["data"]["items"]])

    if len(prices) < period + 1:
        raise ValueError("Not enough data points to calculate RSI.")

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

    # Calculate Relative Strength (RS)
    rs = avg_gain / avg_loss

    # Calculate RSI
    rsi = 100 - (100 / (1 + rs))

    return round(rsi, 2)  # Round to 2 decimal places


