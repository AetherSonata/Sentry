import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

def plot_price_action(historical_data, interval, span_in_days, starting_index, max_interval):
    """
    Plots price action over a given span with adapted time intervals.
    
    - All points before `starting_index` are greyed out.
    - The `starting_index` point is marked in purple.
    - All points after `starting_index` are in blue.
    - X-axis labels are distributed evenly with a maximum of 10 labels.
    
    :param historical_data: Historical data dictionary with timestamps and prices.
    :param interval: The queried interval (e.g., "15m", "1H", "4H").
    :param span_in_days: Total duration of data in days.
    :param starting_index: The index marking the RSI calculation start.
    """
    if "data" not in historical_data or "items" not in historical_data["data"]:
        raise ValueError("Invalid data format: Missing 'items' key.")

    # Extract time and price
    timestamps = [entry["unixTime"] for entry in historical_data["data"]["items"]]
    prices = [entry["value"] for entry in historical_data["data"]["items"]]

    # Convert UNIX timestamps to datetime
    times = [datetime.utcfromtimestamp(ts) for ts in timestamps]

    # Define colors
    before_color = "gray"
    starting_point_color = "purple"
    after_color = "blue"

    # Plot the price action
    plt.figure(figsize=(12, 6))

    # Grey out all points before the starting index
    if starting_index > 0:
        plt.plot(times[:starting_index + 1], prices[:starting_index + 1], marker='o', linestyle='-', color=before_color, alpha=0.5)

    # Highlight the starting point in purple
    plt.scatter(times[starting_index], prices[starting_index], color=starting_point_color, s=100, label="Starting Point (RSI Start)")

    # Plot all points after the starting index in blue
    plt.plot(times[starting_index:], prices[starting_index:], marker='o', linestyle='-', color=after_color, label="Price Action (Post-Start)")

    # Determine major time step for x-axis labels
    interval_map = {
        "1m": 1, "5m": 5, "15m": 15, "30m": 30, "1H": 60,
        "4H": 240, "12H": 720, "1D": 1440, "3D": 4320, "1W": 10080
    }
    interval_minutes = interval_map.get(interval, 15)  # Default to 15m if unknown
    total_time_minutes = (times[-1] - times[0]).total_seconds() / 60  # Total time span in minutes

    # Define number of labels (max 10 labels on x-axis)
    max_labels = 10
    labels_interval = max(1, int(len(times) / max_labels))  # How many points between each label
    
    # Calculate time step for x-axis label distribution (evenly spaced labels)
    label_times = [times[i * labels_interval] for i in range(max_labels)]
    
    # Format the X-axis
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())  # Automatically space major ticks
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M\n%d-%b"))

    # Set the x-ticks to the evenly distributed labels
    plt.xticks(label_times)

    # Labels and title
    plt.xlabel("Time (UTC)")
    plt.ylabel("Price")
    plt.title(f"Price Action Over {span_in_days} Days ({interval} Interval)")
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid()

    # Show the plot
    plt.show()


