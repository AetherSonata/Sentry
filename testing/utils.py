from API.dexScreenerAPI import get_historical_price
from analytics.price_analytics import calculate_rsi_for_intervals
from testing.visualization import plot_price_action
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.animation as animation
from datetime import datetime
import time


def get_historical_test_data(address, interval, span_in_days):
    periods = {
        "1m": 60 / 1 * 24,
        "5m": 60 / 5 * 24,
        "15m": 60 / 15 * 24,
        "30m": 60 / 30 * 24,
        "1H": 24,
        "4H": 4,
        "12H": 2,
        "1D": 1,
        "3D": 1/3,
        "1W": 1/7
    }
    
    # Calculate required number of data points
    num_points = int(periods[interval] * span_in_days)
    
    # Fetch historical data
    test_data = get_historical_price(address, interval, num_points)

    # print(f"{len(test_data['data']['items'])} data points fetched.")
    return test_data


def find_starting_point(historical_data, interval):
    """
    Determines the best possible starting point index for RSI calculation with at least 15 data points.
    Adjusts to the largest usable interval based on available data.

    :param historical_data: Dictionary containing price history.
    :param interval: The requested interval (e.g., "15m", "1H").
    :return: (starting_index, best_interval)
    """
    intervals = ["1m", "5m", "15m", "30m", "1H", "4H", "12H", "1D", "3D", "1W"]
    period_counts = {
        "1m": 1, "5m": 5, "15m": 15, "30m": 30, "1H": 60,
        "4H": 240, "12H": 720, "1D": 1440, "3D": 4320, "1W": 10080
    }
    
    data_points = historical_data["data"]["items"]
    total_points = len(data_points)
    
    # Find the largest interval that allows at least 15 data points
    available_intervals = [i for i in intervals if total_points >= 15 * (period_counts[i] // period_counts[interval])]
    
    if not available_intervals:
        raise ValueError("Not enough data points to calculate RSI with any reasonable interval.")
    
    best_interval = available_intervals[-1]  # Choose the largest usable interval
    step_size = period_counts[best_interval] // period_counts[interval]
    starting_index = min(15 * step_size, total_points - 1)


    return starting_index, best_interval



# Global storage for RSI data (will be updated in the loop)
rsi_data = []

def update_plot():
    ax.clear()

    # Extract available price action
    timestamps = [entry["unixTime"] for entry in historical_data["data"]["items"][:starting_index + len(rsi_data)]]
    prices = [entry["value"] for entry in historical_data["data"]["items"][:starting_index + len(rsi_data)]]
    
    # Convert timestamps to datetime
    times = [datetime.utcfromtimestamp(ts) for ts in timestamps]

    # Define colors
    before_color = "gray"
    starting_point_color = "purple"
    after_color = "blue"

    # Plot all points before the starting index in gray
    if starting_index > 0:
        ax.plot(times[:starting_index], prices[:starting_index], marker='o', linestyle='-', color=before_color, alpha=0.5)

    # Highlight the starting point in purple
    ax.scatter(times[starting_index], prices[starting_index], color=starting_point_color, s=100, label="Starting Point (RSI Start)")

    # Plot all points after the starting index in blue
    ax.plot(times[starting_index:starting_index + len(rsi_data)], 
            prices[starting_index:starting_index + len(rsi_data)], 
            marker='o', linestyle='-', color=after_color, label="Price Action (Post-Start)")

    # Display the most recent RSI values
    latest_rsi = rsi_data[-1] if rsi_data else {}
    rsi_text = "\n".join([f"RSI ({interval}): {rsi:.2f}" for interval, rsi in latest_rsi.items()])

    ax.set_title(f"Price Action Animation ({INTERVAL} Interval) | Step {len(rsi_data)}\n{rsi_text}")

    # Format the X-axis
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())  
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M\n%d-%b"))
    plt.xticks(rotation=45)

    # Set labels and legend
    ax.set_xlabel("Time (UTC)")
    ax.set_ylabel("Price")
    ax.legend()
    ax.grid()

    # Refresh the figure without blocking execution
    plt.pause(0.1)  # Pause for 0.1s to allow UI updates

    def animate(i):
        ax.clear()

        # Extract price action up to the current index
        timestamps = [entry["unixTime"] for entry in historical_data["data"]["items"][:starting_index + i]]
        prices = [entry["value"] for entry in historical_data["data"]["items"][:starting_index + i]]
        
        # Convert timestamps to datetime
        times = [datetime.utcfromtimestamp(ts) for ts in timestamps]

        # Define colors
        before_color = "gray"
        starting_point_color = "purple"
        after_color = "blue"

        # Plot before starting index
        if starting_index > 0:
            ax.plot(times[:starting_index], prices[:starting_index], marker='o', linestyle='-', color=before_color, alpha=0.5)

        # Mark the starting index
        ax.scatter(times[starting_index], prices[starting_index], color=starting_point_color, s=100, label="Starting Point (RSI Start)")

        # Plot data after starting index
        ax.plot(times[starting_index:starting_index + i], 
                prices[starting_index:starting_index + i], 
                marker='o', linestyle='-', color=after_color, label="Price Action (Post-Start)")

        # Display latest RSI values
        latest_rsi = rsi_data[-1] if rsi_data else {}
        rsi_text = "\n".join([f"RSI ({interval}): {rsi:.2f}" for interval, rsi in latest_rsi.items()])

        ax.set_title(f"Price Action Animation ({INTERVAL} Interval) | Step {i}\n{rsi_text}")

        # Format the X-axis
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())  
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M\n%d-%b"))
        plt.xticks(rotation=45)

        # Set labels and legend
        ax.set_xlabel("Time (UTC)")
        ax.set_ylabel("Price")
        ax.legend()
        ax.grid()


if __name__ == "__main__":
    TOKEN_ADDRESS = "H4phNbsqjV5rqk8u6FUACTLB6rNZRTAPGnBb8KXJpump"
    INTERVAL = "5m"
    SPAN_IN_DAYS = 2

    historical_data = get_historical_test_data(TOKEN_ADDRESS, INTERVAL, SPAN_IN_DAYS)

    print(f"{len(historical_data['data']['items'])} data points fetched.")
    if historical_data:
        starting_index, max_interval = find_starting_point(historical_data, INTERVAL)
        print(f"Starting point: {starting_index}, Max interval: {max_interval}")

        # rsi_values = calculate_rsi_for_intervals(historical_data, INTERVAL, max_interval, starting_index)
        # if rsi_values:
        #    # iterate through rsi_values and print the values for each interval
        #     for interval, rsi in rsi_values.items():
        #         print(f"RSI ({interval}): {rsi}")

            # Plot the price action

        fig, ax = plt.subplots(figsize=(12, 6))

        # plot_price_action(historical_data, INTERVAL, SPAN_IN_DAYS, starting_index, max_interval)
        

        #iterate through historical_data in a loop, starting from the starting_index
        for i in range(starting_index, len(historical_data["data"]["items"])):
            #calculate RSI values for each interval, setting the current_point to starting_index + i
            print(i)
            rsi_values = calculate_rsi_for_intervals(historical_data, INTERVAL, max_interval, starting_index + i)
            print(f"RSI values for index {i}: {rsi_values}")
            rsi_data.append(rsi_values)

            update_plot()

            time.sleep(0.5)



    else:
        print("Failed to fetch data.")
