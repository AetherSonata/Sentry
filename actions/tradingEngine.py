from analytics.price_analytics import calculate_rsi_for_intervals
from testing.utils import find_starting_point

SOL_MINT_ADDRESS = "So11111111111111111111111111111111111111112"

class TradingEngine:
    def __init__(self, historical_price_data, interval, portfolio):
        """Initialize the trading engine with historical price data and interval settings."""
        self.price_data = historical_price_data 
        self.interval = interval
        self.is_bought = False
        self.rsi_data = []
        self.portfolio = portfolio

    def check_for_trading_action(self, token_adress):
        #calculate max interval RSI for the latest price data
        notneeded, max_interval = find_starting_point(self.price_data, self.interval)
        #calculate RSI for the latest price data
        self.rsi_data.append(calculate_rsi_for_intervals(self.price_data, self.interval, max_interval))

        if self.is_bought:
            if self.check_if_sell_signal():
                
                if self.portfolio.sell(token_adress, self.calculate_sell_amount(token_adress), self.price_data[-1]["value"], ):
                    action = "SOLD"
                    self.is_bought = False
                else: 
                    action = "SELLING_ERROR"
            else:
                action = "HOLD"
        else:
            if self.check_if_buy_signal():
                
                if self.portfolio.buy(token_adress, self.calculate_buy_amount(), self.price_data[-1]["value"]):
                    action = "BOUGHT"
                    self.is_bought = True
                else:
                    action = "BUYING_ERROR"
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

    def calculate_buy_amount(self):
        available_balance = self.portfolio.holdings["USDC"]
        buy_percentage = 0.1  
        buy_amount = available_balance * buy_percentage

        return buy_amount if buy_amount > 0 else 0

    def calculate_sell_amount(self, token_adress):
        available_tokens = self.portfolio.holdings[token_adress]
        sell_percentage = 1
        sell_amount = available_tokens * sell_percentage
        
        return sell_amount if sell_amount > 0 else 0

    def calculate_stop_loss(self, current_price):
        pass