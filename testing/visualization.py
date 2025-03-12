import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# Offset for trend points below the price
SHORT_TERM_TREND_OFFSET = 0.2 
MID_TERM_TREND_OFFSET = 0.45

# Vertical line properties for bought and sold
BOUGHT_LINE_WIDTH = 2
SOLD_LINE_WIDTH = 2
BOUGHT_COLOR = "green"
SOLD_COLOR = "red"

SHORT_TERM_ALPHA = 0.5
MID_TERM_ALPHA = 0.5

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

    def add_price_point(self, new_price_data, action=None, short_term_trends=None, mid_term_trends=None, supportzones=None, resistancezones=None):
        """Add a new price point without updating the plot immediately."""
        self.historical_data.append(new_price_data)
        self.new_data.append((new_price_data, action, short_term_trends, mid_term_trends, supportzones, resistancezones))  # Store for later plotting

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
        for data, action, short_term_trends, mid_term_trends, supportzones, resistancezones in self.new_data:
            time = datetime.utcfromtimestamp(data["unixTime"])
            price = data["value"]

            # Draw vertical lines for 'BOUGHT' and 'SOLD' actions without labels
            if action == "BOUGHT" or action == "ADDED":
                self.ax.axvline(x=time, color=BOUGHT_COLOR, linewidth=BOUGHT_LINE_WIDTH)
            elif action == "SOLD":
                self.ax.axvline(x=time, color=SOLD_COLOR, linewidth=SOLD_LINE_WIDTH)

            # Draw trend indicators if needed
            if short_term_trends == "bullish":
                self.ax.scatter(time, price - SHORT_TERM_TREND_OFFSET * price, color="green", s=50, alpha=SHORT_TERM_ALPHA)
            elif short_term_trends == "bearish":
                self.ax.scatter(time, price - SHORT_TERM_TREND_OFFSET * price, color="red", s=50, alpha=SHORT_TERM_ALPHA) 

            if mid_term_trends == "bullish":
                self.ax.scatter(time, price - MID_TERM_TREND_OFFSET * price, color="green", s=50, alpha=MID_TERM_ALPHA)
            elif mid_term_trends == "bearish":
                self.ax.scatter(time, price - MID_TERM_TREND_OFFSET * price, color="red", s=50, alpha=MID_TERM_ALPHA)

            # Plot support and resistance zones if they exist
            if supportzones:
                for label, support_price in supportzones:
                    self.ax.axhline(y=support_price, color='purple', linestyle='--', alpha=0.7, label=f"{label} Support")
                    self.ax.text(times[-1], support_price, f" {label}", color='purple', fontsize=10, verticalalignment='center')

            if resistancezones:
                for label, resistance_price in resistancezones:
                    self.ax.axhline(y=resistance_price, color='purple', linestyle='--', alpha=0.7, label=f"{label} Resistance")
                    self.ax.text(times[-1], resistance_price, f" {label}", color='purple', fontsize=10, verticalalignment='center')

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
        for data, action, short_term_trends, mid_term_trends, supportzones, resistancezones in self.new_data:
            time = datetime.utcfromtimestamp(data["unixTime"])
            price = data["value"]

            # Draw vertical lines for 'BOUGHT' and 'SOLD' actions without labels
            if action == "BOUGHT" or action == "ADDED":
                self.ax.axvline(x=time, color=BOUGHT_COLOR, linewidth=BOUGHT_LINE_WIDTH)
            elif action == "SOLD":
                self.ax.axvline(x=time, color=SOLD_COLOR, linewidth=SOLD_LINE_WIDTH)

            # Draw trend indicators if needed
            if short_term_trends == "bullish":
                self.ax.scatter(time, price - SHORT_TERM_TREND_OFFSET * price, color="green", s=50, alpha=SHORT_TERM_ALPHA)
            elif short_term_trends == "bearish":
                self.ax.scatter(time, price - SHORT_TERM_TREND_OFFSET * price, color="red", s=50, alpha=SHORT_TERM_ALPHA) 

            if mid_term_trends == "bullish":
                self.ax.scatter(time, price - MID_TERM_TREND_OFFSET * price, color="green", s=50, alpha=MID_TERM_ALPHA)
            elif mid_term_trends == "bearish":
                self.ax.scatter(time, price - MID_TERM_TREND_OFFSET * price, color="red", s=50, alpha=MID_TERM_ALPHA)

        
        # Plot support zones if they exist
        if supportzones['strong']:
            self.ax.axhline(y=supportzones['strong'], color='green', linestyle='-', alpha=0.7)
            self.ax.text(times[-1], supportzones['strong'], " Strong", color='green', fontsize=10, verticalalignment='center')

        if supportzones['weak']:
            self.ax.axhline(y=supportzones['weak'], color='orange', linestyle='--', alpha=0.7)
            self.ax.text(times[-1], supportzones['weak'], " Weak", color='orange', fontsize=10, verticalalignment='center')

        if supportzones['neutral']:
            self.ax.axhline(y=supportzones['neutral'], color='purple', linestyle=':', alpha=0.7)
            self.ax.text(times[-1], supportzones['neutral'], " Neutral", color='purple', fontsize=10, verticalalignment='center')

        # Plot resistance zones if they exist
        if resistancezones['strong']:
            self.ax.axhline(y=resistancezones['strong'], color='red', linestyle='-', alpha=0.7)
            self.ax.text(times[-1], resistancezones['strong'], " Strong", color='red', fontsize=10, verticalalignment='center')

        if resistancezones['weak']:
            self.ax.axhline(y=resistancezones['weak'], color='orange', linestyle='--', alpha=0.7)
            self.ax.text(times[-1], resistancezones['weak'], " Weak", color='orange', fontsize=10, verticalalignment='center')

        if resistancezones['neutral']:
            self.ax.axhline(y=resistancezones['neutral'], color='purple', linestyle=':', alpha=0.7)
            self.ax.text(times[-1], resistancezones['neutral'], " Neutral", color='purple', fontsize=10, verticalalignment='center')


        # Format the plot
        self.ax.set_xlabel("Time (UTC)")
        self.ax.set_ylabel("Price")
        self.ax.set_title(f"Price Action Over Time ({self.interval} Interval)")
        self.ax.tick_params(axis='x', rotation=45)
        self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M\n%d-%b"))
        self.ax.grid()
        self.ax.legend()

        # Show the static plot
        plt.show()
