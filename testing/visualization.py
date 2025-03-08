import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

def plot_price_action(historical_data, interval, span_in_days):
    """
    Plots price action over a given span with adapted time intervals.

    :param historical_data: Historical data dictionary with timestamps and prices.
    :param interval: The queried interval (e.g., "15m", "1H", "4H").
    :param span_in_days: Total duration of data in days.
    """
    if "data" not in historical_data or "items" not in historical_data["data"]:
        raise ValueError("Invalid data format: Missing 'items' key.")

    # Extract time and price
    timestamps = [entry["unixTime"] for entry in historical_data["data"]["items"]]
    prices = [entry["value"] for entry in historical_data["data"]["items"]]

    # Convert UNIX timestamps to datetime
    times = [datetime.utcfromtimestamp(ts) for ts in timestamps]

    # Determine major time step for x-axis labels
    interval_map = {
        "1m": 1, "5m": 5, "15m": 15, "30m": 30, "1H": 60,
        "4H": 240, "12H": 720, "1D": 1440, "3D": 4320, "1W": 10080
    }
    
    interval_minutes = interval_map.get(interval, 15)  # Default to 15m if unknown
    hours_per_tick = max(1, interval_minutes // 60)  # At least 1 hour per tick
    major_ticks = mdates.HourLocator(interval=hours_per_tick)  # Mark hours dynamically

    # Plot the price action
    plt.figure(figsize=(12, 6))
    plt.plot(times, prices, marker='o', linestyle='-', label="Price Action")

    # Format the X-axis
    plt.gca().xaxis.set_major_locator(major_ticks)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M\n%d-%b"))

    # Labels and title
    plt.xlabel("Time (UTC)")
    plt.ylabel("Price")
    plt.title(f"Price Action Over {span_in_days} Days ({interval} Interval)")
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid()

    # Show the plot
    plt.show()
