import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# Offset for trend points below the price
SHORT_TERM_TREND_OFFSET = 0.2 
MID_TERM_TREND_OFFSET = 0.45

BOUGHT_OFFSET = 1.25
SOLD_OFFSET = 1.25



class PricePlotter:
    def __init__(self, historical_data, interval):
        """Initialize the plotter with historical data and interval settings."""
        self.historical_data = historical_data  # Stores all price data
        self.interval = interval  # Timeframe interval
        self.new_data = []  # Stores newly added price points for coloring
        self.rsi_data = []  # Stores RSI values

        # Initialize the plot
        self.fig, self.ax = plt.subplots(figsize=(12, 6))

        # Store trend text for later updating
        self.trend_text = None

    def add_price_point(self, new_price_data, action=None, short_term_trends=None, mid_term_trends=None):
        """Add a new price point without updating the plot immediately."""
        self.historical_data.append(new_price_data)
        self.new_data.append((new_price_data, action, short_term_trends, mid_term_trends))  # Store for later plotting

    def plot_live(self):
        """Generates a live price action plot with updated points."""
        timestamps = [entry["unixTime"] for entry in self.historical_data]
        prices = [entry["value"] for entry in self.historical_data]
        times = [datetime.utcfromtimestamp(ts) for ts in timestamps]

        # Clear previous plot
        self.ax.clear()

        # Plot initial historical data in blue
        self.ax.plot(times, prices, marker='o', linestyle='-', color="blue", alpha=0.5, label="Historical Data")

        # Overlay new points in their respective colors
        for data, action, short_term_trends, mid_term_trends in self.new_data:
            time = datetime.utcfromtimestamp(data["unixTime"])
            price = data["value"]

            # Set color based on action
            if action == "BOUGHT" or action == "ADDED":
                color = "green"
                s = 150
                alpha = 1
                price = price * BOUGHT_OFFSET
            elif action == "SOLD":
                color = "red"
                s = 150
                alpha = 1
                price = price * SOLD_OFFSET
            else:
                color = "gray"  # Default for newly added points with no action
                s = 50
                alpha = 0.5

            # Add scatter point for new data
            self.ax.scatter(time, price, color=color, s=s, alpha=alpha)

            if short_term_trends == "bullish":
                # Green point below the price
                self.ax.scatter(time, price - SHORT_TERM_TREND_OFFSET, color="green", s=50, alpha=0.7)
            elif short_term_trends == "bearish":
                # Red point below the price
                self.ax.scatter(time, price - SHORT_TERM_TREND_OFFSET, color="red", s=50, alpha=0.7) 

            # Draw an additional point based on the trend
            if mid_term_trends == "bullish":
                # Green point below the price
                self.ax.scatter(time, price - MID_TERM_TREND_OFFSET, color="green", s=50, alpha=0.7)
            elif mid_term_trends == "bearish":
                # Red point below the price
                self.ax.scatter(time, price - MID_TERM_TREND_OFFSET, color="red", s=50, alpha=0.7)

           

        # Update the trend text in the upper-right corner
        if trends:
            if self.trend_text:
                self.trend_text.set_text(f"Trend: {trends}")
            else:
                # Initialize trend text if it doesn't exist
                self.trend_text = self.ax.text(0.95, 0.95, f"Trend: {trends}",
                                                transform=self.ax.transAxes, fontsize=12, color="black", ha="right", va="top")

        # Format the plot
        self.ax.set_xlabel("Time (UTC)")
        self.ax.set_ylabel("Price")
        self.ax.set_title(f"Price Action Over Time ({self.interval} Interval)")
        self.ax.tick_params(axis='x', rotation=45)
        self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M\n%d-%b"))
        self.ax.grid()
        self.ax.legend()

        # Pause to update the plot live
        plt.pause(0.1)

    def plot_static(self):
        """Generates a static price action plot with correctly colored points."""
        # Clear the previous axes and figure
        self.fig, self.ax = plt.subplots(figsize=(12, 6))

        # Extract the historical price data
        timestamps = [entry["unixTime"] for entry in self.historical_data]
        prices = [entry["value"] for entry in self.historical_data]
        times = [datetime.utcfromtimestamp(ts) for ts in timestamps]

        # Plot initial historical data in blue
        self.ax.plot(times, prices, marker='o', linestyle='-', color="blue", alpha=0.5, label="Historical Data")

        # Overlay new points in their respective colors
        for data, action, short_term_trends, mid_term_trends in self.new_data:
            time = datetime.utcfromtimestamp(data["unixTime"])
            price = data["value"]

            # Set color based on action
            if action == "BOUGHT" or action == "ADDED":
                color = "green"
                s = 150
                alpha = 1
                price = price * BOUGHT_OFFSET
            elif action == "SOLD":
                color = "red"
                s = 150
                alpha = 1
                price = price * SOLD_OFFSET
            else:
                color = "gray"  # Default for newly added points with no action
                s = 50
                alpha = 0.5

            # Add scatter point for new data
            self.ax.scatter(time, price, color=color, s=s, alpha=alpha)

            if short_term_trends == "bullish":
                # Green point below the price
                self.ax.scatter(time, price - SHORT_TERM_TREND_OFFSET * price, color="green", s=50, alpha=0.7)
            elif short_term_trends == "bearish":
                # Red point below the price
                self.ax.scatter(time, price - SHORT_TERM_TREND_OFFSET * price, color="red", s=50, alpha=0.7) 

            # Draw an additional point based on the trend
            if mid_term_trends == "bullish":
                # Green point below the price
                self.ax.scatter(time, price - MID_TERM_TREND_OFFSET * price, color="green", s=50, alpha=0.7)
            elif mid_term_trends == "bearish":
                # Red point below the price
                self.ax.scatter(time, price - MID_TERM_TREND_OFFSET * price, color="red", s=50, alpha=0.7)

        # Format the plot
        self.ax.set_xlabel("Time (UTC)")
        self.ax.set_ylabel("Price")
        self.ax.set_title(f" ({self.interval} Interval)")
        self.ax.tick_params(axis='x', rotation=45)
        self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M\n%d-%b"))
        self.ax.grid()
        self.ax.legend()

        # Show the static plot
        plt.show()
