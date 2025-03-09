from analytics.price_analytics import calculate_rsi_for_intervals
from testing.utils import find_starting_point
from actions.testing_portfolio import Portfolio

class TradingEngine:
    def __init__(self, historical_price_data, interval):
        self.price_data = historical_price_data #initialize with historical price data
        self.interval = interval
        self.is_bought = False
        self.rsi_data = []

    def check_for_trading_action(self):
        #calculate max interval RSI for the latest price data
        starting_index, max_interval = find_starting_point(self.price_data, self.interval)
        #calculate RSI for the latest price data
        self.rsi_data.append(calculate_rsi_for_intervals(self.price_data, self.interval, max_interval))

        if self.is_bought:
            if self.check_if_sell_signal():
                self.is_bought = False
                action = "SOLD"
            else:
                action = "HOLD"
        else:
            if self.check_if_buy_signal():
                self.is_bought = True
                action = "BOUGHT"
            else:
                action = "NONE"

        return action

    def check_if_buy_signal(self):
        #check for RSI movements that indicate a buy signal
        
        return True

    def check_if_sell_signal(self):
        #check for RSI movements that indicate a sell signal

        return True

    def add_new_price_point(self, new_price_data):
        self.price_data.append(new_price_data)
        pass

    def calculate_buy_amount(self, current_price):
        pass

    def calculate_stop_loss(self, current_price):
        pass