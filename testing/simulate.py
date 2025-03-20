from actions.tradingEngine import TradingEngine
from API.API_utils import fetch_complete_test_data
from analytics.time_utils import get_interval_in_minutes
from utils.os_utils import load_historical_data_from_file, save_historical_data_to_file, save_metrics_to_csv
from testing.plotter import PricePlotter
from testing.find_points import  PointFinder
import random

#global variables for data collection
ADRESSES_TO_FETCH = [ 
                    #   "CniPCE4b3s8gSUPhUiyMjXnytrEqUrMfSsnbBjLCpump",
                    #   "AQiE2ghyFbBsbsfHiTEbKWcCLTDgyGzceKEPWftZpump"
                      "FWAr6oWa6CHg6WUcXu8CqkmsdbhtEqL8t31QTonppump",
                    #   "FtUEW73K6vEYHfbkfpdBZfWpxgQar2HipGdbutEhpump",
                    #   "EF3Ln1DkUB5azvqcaCJgG3RR2qSUJEXxLo1q4ZHzpump",
                    #   "GYTd9XbZTfwicCV28LGkwiDF4DgpXTTAi2UeCajfpump",
                    #   "hV7MQkCpjvuTTnPJXPhPXzvmtMxk8A8ct1KPiRMpump",
                    #   "UL1jwqh3ARmdNTE5qUQyaXHDcrAZ988GZ6tp21Epump",
                    #   "5e41GfrQwTP74LgGt6WP9kw6xa1jQhAERCjnFKf74y52",
                    #   "FS4xcBxLJbrrdXE1R6zHvKw8no4zrQn2rRFuczvepump",
                    #   "9YnfbEaXPaPmoXnKZFmNH8hzcLyjbRf56MQP7oqGpump",
                    #   "2yFiCwdLiUfxq9PcNXQvu16QdgBFniCJP8P8gEXNpump",
                    #   "H4phNbsqjV5rqk8u6FUACTLB6rNZRTAPGnBb8KXJpump",
                    #   "9eXC6W3ZKnkNnCr9iENExRLJDYfPGLbc4m6qfJzJpump",
                    #   "2TUQ21D87yrbZM1F3RB93sbkiGXeTTfkb8wWqG2ipump",
                    #   "9pViBf84zD4ncn8Mj8rtdtojnRkxBpibPEjbaGW6pump",
                    ]                   

REFRESH_INTERVAL = "5m"
FETCHING_SPAN_IN_DAYS = 200 # set high to fetch all available data
OHLCV = False

#specify the path to save the data
RAW_DATA_PATH = "historical_data/"
TRAINING_DATA_PATH = "training_data_metrics/"

if __name__ == "__main__":
    token_list = ADRESSES_TO_FETCH

    for token in token_list:

        historical_data = None
        
        #fetching full historical data for each token
        print(f"Fetching data for token: {token}")
        try:
            historical_data = load_historical_data_from_file(filename=f"{RAW_DATA_PATH}historical_price_{token}_{REFRESH_INTERVAL}_{FETCHING_SPAN_IN_DAYS}_{OHLCV}.json")
        except Exception as e:
            print(f"No data found for token {token}. Fetching from API.")

        if not historical_data:
            historical_data = fetch_complete_test_data(token, REFRESH_INTERVAL, FETCHING_SPAN_IN_DAYS, ohlcv=OHLCV)

        if historical_data:
            save_historical_data_to_file(historical_data, filename=f"{RAW_DATA_PATH}historical_price_{token}_{REFRESH_INTERVAL}_{FETCHING_SPAN_IN_DAYS}_{OHLCV}.json")
            print(f"Data saved for token: {token}")
        else:
            print(f"No data to save for token: {token}. Check API response. ")
    
    print("Data fetching complete.")
    print("starting data collection for GYM data")

    #initialize data collector with simulated historical data for each token (historical + 1 live data point)
    #initialize starting metrics for the token
    starting_index = random.randint(10, 150)
    end_index = len(historical_data["data"]["items"]) - 200
    print(f"Starting index: {starting_index}")  

    # starting_index = 200
    
    tradingEngine = TradingEngine(REFRESH_INTERVAL, historical_data["data"]["items"][: starting_index])   

    # passing tradingEngine to the plotter to visualize the data
    plotter = PricePlotter(tradingEngine)

    #SIMULATION ENVIRONMENT: iterate through historical data in a loop, starting one interval after the starting index, mocking real-time data feed
    for i in range( starting_index, len(historical_data["data"]["items"])):
        tradingEngine.add_new_price_point(historical_data["data"]["items"][i]) # Simulate real-time data feed

        plotter.plot_live()


# print(f"analyzed {(len(tradingEngine.metric_collector.metrics)*get_interval_in_minutes(REFRESH_INTERVAL)) / 60} hours of data")
# print(f"equal to {(len(tradingEngine.metric_collector.metrics)*get_interval_in_minutes(REFRESH_INTERVAL)) / 60 / 24} days of data")
# # finding specific buy opportunities in the data
# pointFinder = PointFinder(tradingEngine.metric_collector.metrics)
# targets = pointFinder.find_significant_price_increases(price_increase=1.5)
# plotter.add_backtesting_points(targets , [])
# plotter.plot_static()

# print(pointFinder.get_indexed_metrics(targets, lower_bound=400))


        
# save_metrics_to_csv(token_metrics, filename=f"{TRAINING_DATA_PATH}token_metrics_{REFRESH_INTERVAL}.csv")



