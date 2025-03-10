
from testing.utils import get_historical_test_data, find_starting_point, load_historical_price, save_historical_price
from testing.visualization import PricePlotter
from actions.tradingEngine import TradingEngine
from actions.testing_portfolio import TestingPortfolio as Portfolio

#global variables for testing
TOKEN_ADDRESS = "47NF9q76FaLAbZQmBaHeeUWYsEn4Rt4qjmh1oACipump"
INTERVAL = "5m"    # birdeye fetching max 1000 data points of historic data
SPAN_IN_DAYS = 3
TESTING_PORT_BALANCE = 100


if __name__ == "__main__":

    #if data cant be read from file, fetch it from API
    try:
        historical_data = load_historical_price()
    except Exception as e:
        print(f"Error loading data: {e}")
    
    if not historical_data: 
        historical_data = get_historical_test_data(TOKEN_ADDRESS, INTERVAL, SPAN_IN_DAYS)
        print("Data fetched from API.")
        try:
            save_historical_price(historical_data)
        except Exception as e:
            print(f"Error saving data: {e}")
    else:
        print("Data successfully loaded from file.")
    

    print(f"{len(historical_data['data']['items'])} data points fetched.")
    if historical_data:
        starting_index, max_interval = find_starting_point(historical_data["data"]["items"], INTERVAL)
        print(f"Starting index: {starting_index}, Max interval: {max_interval}")

        #initialize portfolio with starting balance
        portfolio = Portfolio()
        
        #initialize plotter with historical data up to the starting index
        plotter = PricePlotter(historical_data["data"]["items"][:starting_index ], INTERVAL)
                
        #initialize trading engine with historical data up to the starting index
        tradingEngine = TradingEngine(historical_data["data"]["items"][:starting_index ], INTERVAL, portfolio)

        
        #iterate through historical_data in a loop, starting one interval after the starting index, mocking real-time data feed
        for i in range(starting_index + 1, len(historical_data["data"]["items"])):
            tradingEngine.add_new_price_point(historical_data["data"]["items"][i])
            action = tradingEngine.check_for_trading_action(TOKEN_ADDRESS)

            # retrives latest added trends for live interval
            _, rsi_trends, ema_trends = tradingEngine.group_trends[-1]
            trends=[rsi_trends, ema_trends]
            short_term_trend = tradingEngine.determine_overall_trend()["group_trends"]["short_term"]
            mid_term_trend = tradingEngine.determine_overall_trend()["group_trends"]["mid_term"]
            
            #add the latest price point and metrics to the plotter
            plotter.add_price_point(historical_data["data"]["items"][i], action, short_term_trend,mid_term_trend)
            # plotter.plot_live()
            
        print(f"current balance: {portfolio.holdings['USDC']}")
        plotter.plot_static()
        
    else:
        print("Failed to fetch data.")