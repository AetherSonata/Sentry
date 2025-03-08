import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

class PricePlotter:
    def __init__(self, historical_data, interval, starting_index):
        """Initialize the plotter with historical data and interval settings."""
        self.historical_data = historical_data
        self.interval = interval
        self.starting_index = starting_index
        self.rsi_data = []

        # Create figure and axis
        self.fig, self.ax = plt.subplots(figsize=(12, 6))

    def update_plot(self):
        """Update the price action plot with the latest RSI data."""
        self.ax.clear()

        # Extract available price action
        timestamps = [entry["unixTime"] for entry in self.historical_data["data"]["items"][:self.starting_index + len(self.rsi_data)]]
        prices = [entry["value"] for entry in self.historical_data["data"]["items"][:self.starting_index + len(self.rsi_data)]]

        # Convert timestamps to datetime
        times = [datetime.utcfromtimestamp(ts) for ts in timestamps]

        # Define colors
        before_color = "gray"
        starting_point_color = "purple"
        after_color = "blue"

        # Plot all points before the starting index in gray
        if self.starting_index > 0:
            self.ax.plot(times[:self.starting_index], prices[:self.starting_index], marker='o', linestyle='-', color=before_color, alpha=0.5)

        # Highlight the starting point in purple
        self.ax.scatter(times[self.starting_index], prices[self.starting_index], color=starting_point_color, s=100, label="Starting Point (RSI Start)")

        # Plot all points after the starting index in blue
        self.ax.plot(times[self.starting_index:self.starting_index + len(self.rsi_data)], 
                     prices[self.starting_index:self.starting_index + len(self.rsi_data)], 
                     marker='o', linestyle='-', color=after_color, label="Price Action (Post-Start)")

        # Display the most recent RSI values
        latest_rsi = self.rsi_data[-1] if self.rsi_data else {}
        rsi_text = "\n".join([f"RSI ({interval}): {rsi:.2f}" for interval, rsi in latest_rsi.items()])

        self.ax.set_title(f"Price Action Animation ({self.interval} Interval) | Step {len(self.rsi_data)}\n{rsi_text}")

        # Format the X-axis
        self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())  
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M\n%d-%b"))
        plt.xticks(rotation=45)

        # Set labels and legend
        self.ax.set_xlabel("Time (UTC)")
        self.ax.set_ylabel("Price")
        self.ax.legend()
        self.ax.grid()

        # Refresh the figure without blocking execution
        plt.pause(0.1)

    def add_rsi_data(self, rsi_values):
        """Append new RSI values and update the plot."""
        self.rsi_data.append(rsi_values)
        self.update_plot()

    def plot_static(self):
        """Generates a static price action plot."""
        timestamps = [entry["unixTime"] for entry in self.historical_data["data"]["items"]]
        prices = [entry["value"] for entry in self.historical_data["data"]["items"]]
        times = [datetime.utcfromtimestamp(ts) for ts in timestamps]

        before_color = "gray"
        starting_point_color = "purple"
        after_color = "blue"

        plt.figure(figsize=(12, 6))

        if self.starting_index > 0:
            plt.plot(times[:self.starting_index + 1], prices[:self.starting_index + 1], marker='o', linestyle='-', color=before_color, alpha=0.5)

        plt.scatter(times[self.starting_index], prices[self.starting_index], color=starting_point_color, s=100, label="Starting Point (RSI Start)")
        plt.plot(times[self.starting_index:], prices[self.starting_index:], marker='o', linestyle='-', color=after_color, label="Price Action (Post-Start)")

        plt.xlabel("Time (UTC)")
        plt.ylabel("Price")
        plt.title(f"Price Action Over Time ({self.interval} Interval)")
        plt.xticks(rotation=45)
        plt.legend()
        plt.grid()
        plt.show()
