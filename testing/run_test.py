
from testing.utils import get_historical_test_data, find_starting_point
from testing.visualization import PricePlotter
from actions.tradingEngine import TradingEngine
from actions.testing_portfolio import TestingPortfolio as Portfolio

#global variables for testing
TOKEN_ADDRESS = "47NF9q76FaLAbZQmBaHeeUWYsEn4Rt4qjmh1oACipump"
INTERVAL = "5m"    # birdeye fetching max 1000 data points of historic data
SPAN_IN_DAYS = 3
TESTING_PORT_BALANCE = 100


if __name__ == "__main__":


    historical_data = get_historical_test_data(TOKEN_ADDRESS, INTERVAL, SPAN_IN_DAYS)

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
            _, rsi_trends, ema_trends = tradingEngine.determine_overall_trend()
            trends=[rsi_trends, ema_trends]
            short_term_trend = tradingEngine.determine_overall_trend()["group_trends"]["short_term"]
            mid_term_trend = tradingEngine.determine_overall_trend()["group_trends"]["mid_term"]
            
            # print(trends)
            plotter.add_price_point(historical_data["data"]["items"][i], action, short_term_trend,mid_term_trend)

            
            # print(f"current metrics: {tradingEngine.metrics[-1]}")
            # plotter.plot_live()
            
        print(f"current balance: {portfolio.holdings['USDC']}")
        plotter.plot_static()
        
        
        
    else:
        print("Failed to fetch data.")