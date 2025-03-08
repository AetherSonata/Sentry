
class trading_logic:
    def __init__(self, price_data, interval):
        self.price_data = price_data
        self.interval = interval
        pass

    def check_if_buy_signal(self, rsi_data):
        pass

    def check_if_sell_signal(self, rsi_data):
        pass 

    def add_new_price_point(self, new_price_data):
        self.price_data.append(new_price_data)
        pass