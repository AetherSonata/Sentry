from analytics.price_analytics import calculate_rsi_for_intervals
from testing.utils import find_starting_point

# Global Configuration
SLIPPAGE_PERCENTAGE = 0.02  # 2% slippage
BUY_PERCENTAGE = 0.1        # 10% of available balance for buying
SELL_PERCENTAGE = 1         # 100% of holding when selling
STOP_LOSS_PERCENTAGE_LOW = 0.95  # 5% below current price
STOP_LOSS_PERCENTAGE_HIGH = 0.97 # 3% below current price
TAKE_PROFIT_PERCENTAGE = 1.10    # 10% above current price

SOL_MINT_ADDRESS = "So11111111111111111111111111111111111111112"

class TradingEngine:
    def __init__(self, historical_price_data, interval, portfolio):
        """Initialize the trading engine with historical price data, interval settings, and a portfolio."""
        self.price_data = historical_price_data
        self.interval = interval
        self.active_position = None  # This will hold our current (averaged) position
        self.rsi_data = []
        self.portfolio = portfolio

    def check_for_trading_action(self, token_address):
        # Calculate max interval RSI for the latest price data
        _, max_interval = find_starting_point(self.price_data, self.interval)
        # Append the latest RSI calculation
        self.rsi_data.append(calculate_rsi_for_intervals(self.price_data, self.interval, max_interval))
        current_price = self.price_data[-1]["value"]

        action = "NONE"

        if self.active_position:
            # If we have an active position, check for exit or to add to the position
            if self.check_if_sell_signal(self.active_position, current_price):
                # Sell the entire position
                if self.portfolio.sell(token_address, self.active_position["amount"], current_price, slippage=SLIPPAGE_PERCENTAGE):
                    action = "SOLD"
                    self.active_position = None
                else:
                    action = "SELLING_ERROR"
            elif self.check_if_add_to_position(self.active_position, current_price):
                # Buy additional tokens (averaging down) while keeping the initial stop loss range
                additional_amount = self.calculate_buy_amount(current_price)
                if additional_amount > 0 and self.portfolio.buy(token_address, current_price, additional_amount, slippage=SLIPPAGE_PERCENTAGE):
                    # Calculate the new weighted average entry price
                    old_amount = self.active_position["amount"]
                    old_avg = self.active_position["avg_entry"]
                    # For buy orders, slippage increases the effective price paid:
                    adjusted_price = current_price * (1 + SLIPPAGE_PERCENTAGE)
                    new_total_amount = old_amount + additional_amount
                    new_avg = ((old_avg * old_amount) + (adjusted_price * additional_amount)) / new_total_amount
                    self.active_position["avg_entry"] = new_avg
                    self.active_position["amount"] = new_total_amount
                    # Keep the original stop loss range unchanged
                    action = "ADDED"
                else:
                    action = "ADDING_ERROR"
            else:
                action = "HOLD"
        else:
            # No active position: check for a buy signal
            if self.check_if_buy_signal(current_price):
                buy_amount = self.calculate_buy_amount(current_price)
                if buy_amount > 0 and self.portfolio.buy(token_address, current_price, buy_amount, slippage=SLIPPAGE_PERCENTAGE):
                    # Open a new active position using the slippage-adjusted entry price
                    adjusted_price = current_price * (1 + SLIPPAGE_PERCENTAGE)
                    self.active_position = {
                        "avg_entry": adjusted_price,
                        "amount": buy_amount,
                        "stop_loss_range": self.calculate_stop_loss_range(current_price),
                        "take_profit": self.calculate_take_profit(current_price)
                    }
                    action = "BOUGHT"
                else:
                    action = "BUYING_ERROR"
            else:
                action = "NONE"

        return action

    def check_if_buy_signal(self, current_price):
        # Placeholder logic for a buy signal (e.g., based on RSI)
        return True

    def check_if_sell_signal(self, position, current_price):
        # Sell if the price is above take profit or below the lower bound of the stop loss range
        stop_loss_lower, _ = position["stop_loss_range"]
        if current_price >= position["take_profit"] or current_price <= stop_loss_lower:
            return True
        return False

    def check_if_add_to_position(self, position, current_price):
        # Example: add to position if current price is near the lower bound of the stop loss zone (e.g., within 1% above it)
        stop_loss_lower, _ = position["stop_loss_range"]
        if current_price <= stop_loss_lower * 1.01:
            return True
        return False

    def add_new_price_point(self, new_price_data):
        self.price_data.append(new_price_data)

    def calculate_buy_amount(self, current_price):
        available_balance = self.portfolio.holdings["USDC"]
        buy_total_in_usd = available_balance * BUY_PERCENTAGE  # Use global constant for buying percentage
        # Adjust the effective price per token for slippage (you pay more per token)
        adjusted_price = current_price * (1 + SLIPPAGE_PERCENTAGE)
        buy_amount = buy_total_in_usd / adjusted_price
        print(f"💰 Spending ${buy_total_in_usd:.2f} at adjusted price ${adjusted_price:.2f} per token; tokens received: {buy_amount:.6f}")
        return buy_amount if buy_amount > 0 else 0

    def calculate_sell_amount(self, token_address):
        available_tokens = self.portfolio.holdings.get(token_address, 0)
        sell_amount = available_tokens * SELL_PERCENTAGE  # Use global constant for sell percentage
        return sell_amount if sell_amount > 0 else 0

    def calculate_stop_loss_range(self, current_price):
        # Use global constants for stop loss zone range
        lower_bound = current_price * STOP_LOSS_PERCENTAGE_LOW
        upper_bound = current_price * STOP_LOSS_PERCENTAGE_HIGH
        return (lower_bound, upper_bound)

    def calculate_take_profit(self, current_price):
        # Use global constant for take profit percentage
        return current_price * TAKE_PROFIT_PERCENTAGE
