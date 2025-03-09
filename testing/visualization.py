import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

class PricePlotter:
    def __init__(self, historical_data, interval):
        """Initialize the plotter with historical data and interval settings."""
        self.historical_data = historical_data  # Stores all price data
        self.interval = interval  # Timeframe interval
        self.new_data = []  # Stores newly added price points for coloring
        self.rsi_data = []  # Stores RSI values

    def add_price_point(self, new_price_data, action=None):
        """Add a new price point without updating the plot immediately."""
        self.historical_data.append(new_price_data)
        self.new_data.append((new_price_data, action))  # Store for later plotting

    def plot_static(self):
        """Generates a static price action plot with correctly colored points."""
        timestamps = [entry["unixTime"] for entry in self.historical_data]
        prices = [entry["value"] for entry in self.historical_data]
        times = [datetime.utcfromtimestamp(ts) for ts in timestamps]

        # Create the figure
        plt.figure(figsize=(12, 6))

        # Plot initial historical data in gray
        plt.plot(times, prices, marker='o', linestyle='-', color="gray", alpha=0.5, label="Historical Data")

        # Overlay new points in their respective colors
        for data, action in self.new_data:
            time = datetime.utcfromtimestamp(data["unixTime"])
            price = data["value"]

            # Set color based on action
            if action == "BOUGHT" or action == "ADDED":
                color = "green"
            elif action == "SOLD":
                color = "red"
            else:
                color = "blue"  # Default for newly added points

            plt.scatter(time, price, color=color, s=100)

        # Format the plot
        plt.xlabel("Time (UTC)")
        plt.ylabel("Price")
        plt.title(f"Price Action Over Time ({self.interval} Interval)")
        plt.xticks(rotation=45)
        plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M\n%d-%b"))
        plt.grid()
        plt.legend()
        plt.show()
