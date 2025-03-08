class TestingPortfolio:
    def __init__(self, starting_balance=10000):
        """Initialize the portfolio with a starting balance and no assets."""
        self.balance = starting_balance  # Cash balance in USD
        self.holdings = {}  # Dictionary to store asset amounts {'TOKEN': amount}
        self.trade_history = []  # List to store buy/sell transactions

    def buy(self, token, price, amount):
        """
        Buy a certain amount of a token at a given price.

        :param token: The token symbol (e.g., "SOL")
        :param price: The price per token in USD
        :param amount: The amount of tokens to buy
        """
        cost = price * amount
        if cost > self.balance:
            print(f"❌ Not enough balance to buy {amount} {token} at ${price:.2f} each.")
            return False

        self.balance -= cost
        self.holdings[token] = self.holdings.get(token, 0) + amount
        self.trade_history.append({"action": "buy", "token": token, "price": price, "amount": amount})
        print(f"✅ Bought {amount:.4f} {token} at ${price:.2f}. New balance: ${self.balance:.2f}")
        return True

    def sell(self, token, price, amount):
        """
        Sell a certain amount of a token at a given price.

        :param token: The token symbol (e.g., "SOL")
        :param price: The price per token in USD
        :param amount: The amount of tokens to sell
        """
        if token not in self.holdings or self.holdings[token] < amount:
            print(f"❌ Not enough {token} to sell {amount}. Current holdings: {self.holdings.get(token, 0)}")
            return False

        revenue = price * amount
        self.balance += revenue
        self.holdings[token] -= amount
        if self.holdings[token] == 0:
            del self.holdings[token]  # Remove token if balance is zero
        self.trade_history.append({"action": "sell", "token": token, "price": price, "amount": amount})
        print(f"✅ Sold {amount:.4f} {token} at ${price:.2f}. New balance: ${self.balance:.2f}")
        return True

    def get_portfolio_value(self, current_prices):
        """
        Calculate the total portfolio value based on current prices.

        :param current_prices: Dictionary of token prices (e.g., {"SOL": 120.5})
        :return: Total portfolio value (cash + holdings value)
        """
        holdings_value = sum(self.holdings[token] * current_prices.get(token, 0) for token in self.holdings)
        return self.balance + holdings_value

    def portfolio_summary(self, current_prices=None):
        """Print a summary of the current portfolio."""
        print("\n📊 Portfolio Summary:")
        print(f"💰 Cash Balance: ${self.balance:.2f}")
        
        if self.holdings:
            print("\n📈 Holdings:")
            for token, amount in self.holdings.items():
                value = current_prices[token] * amount if current_prices else "N/A"
                print(f"  - {token}: {amount:.4f} (Value: ${value:.2f})")
        
        total_value = self.get_portfolio_value(current_prices) if current_prices else "N/A"
        print(f"\n💵 Total Portfolio Value: ${total_value}\n")
