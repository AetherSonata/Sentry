
from analytics.price_analytics import calculate_rsi_for_intervals
from testing.utils import get_historical_test_data, find_starting_point
from testing.visualization import PricePlotter


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

        plotter = PricePlotter(historical_data, INTERVAL, starting_index)
        

        #iterate through historical_data in a loop, starting from the starting_index
        for i in range(starting_index, len(historical_data["data"]["items"])):
            #calculate RSI values for each interval, setting the current_point to starting_index + i
            print(i)
            rsi_values = calculate_rsi_for_intervals(historical_data, INTERVAL, max_interval, starting_index + i)
            print(f"RSI values for index {i}: {rsi_values}")

            plotter.add_rsi_data(rsi_values)

            # time.sleep(0.5)

        

    else:
        print("Failed to fetch data.")