class TestingPortfolio:
    def __init__(self):
        # Initial holdings: Starting with 10 USD balance
        self.usd_balance = 10  # USD balance in portfolio
        self.holdings = {}  # Dictionary to store token holdings (token_address: amount)
        self.trade_history = []  # List to store buy/sell transactions

    def buy(self, token, current_price, amount):
        """
        Buy a certain amount of a token using USD.

        :param token: The token address (e.g., "So11111111111111111111111111111111111111112")
        :param amount: The amount of tokens to buy
        :param price_per_token: The price per token in USD
        """
        total_cost = current_price * amount

        if self.usd_balance >= total_cost:
            # Proceed with purchase: Deduct USD and add the token to holdings
            self.usd_balance -= total_cost

            # Update holdings with purchased tokens
            if token in self.holdings:
                self.holdings[token] += amount
            else:
                self.holdings[token] = amount

            self.trade_history.append({"action": "buy", "token": token, "price": current_price, "amount": amount})
            print(f"✅ Purchased {amount} of {token} at ${current_price} each. Total cost: ${total_cost:.2f}")
            return True
        else:
            print(f"❌ Not enough USD to buy {amount} {token} at ${current_price} each. Total required: ${total_cost:.2f}")
            return False

    def sell(self, token, amount, price_per_token):
        """
        Sell a certain amount of a token for USD.

        :param token: The token address (e.g., "So11111111111111111111111111111111111111112")
        :param amount: The amount of tokens to sell
        :param price_per_token: The price per token in USD
        """
        # Check if enough tokens are available for selling
        if token in self.holdings and self.holdings[token] >= amount:
            total_revenue = price_per_token * amount
            self.usd_balance += total_revenue
            self.holdings[token] -= amount

            # Remove the token from holdings if the amount reaches zero
            if self.holdings[token] == 0:
                del self.holdings[token]

            self.trade_history.append({"action": "sell", "token": token, "price": price_per_token, "amount": amount})
            print(f"✅ Sold {amount} of {token} at ${price_per_token} each. Total revenue: ${total_revenue:.2f}")
            return True
        else:
            print(f"❌ Not enough {token} to sell {amount}. Current holdings: {self.holdings.get(token, 0)}")
            return False

    def get_portfolio_value(self):
        """
        Return the total portfolio value in USD (cash balance + value of token holdings).

        :return: Total portfolio value in USD
        """
        holdings_value = sum(self.holdings[token] * self.fetch_current_prices().get(token, 0) for token in self.holdings)
        return self.usd_balance + holdings_value

    def portfolio_summary(self):
        """Print a summary of the current portfolio."""
        print("\n📊 Portfolio Summary:")
        print(f"💰 Cash Balance: ${self.usd_balance:.2f}")
        if self.holdings:
            print("\n📈 Holdings:")
            for token, amount in self.holdings.items():
                current_price = self.fetch_current_prices().get(token, 0)
                value = amount * current_price if current_price else "N/A"
                print(f"  - {token}: {amount:.4f} (Value: ${value:.2f})")
        total_value = self.get_portfolio_value()
        print(f"\n💵 Total Portfolio Value: ${total_value:.2f}\n")

    def fetch_current_prices(self):
        """
        Fetches the current prices for all tokens (for simulation purposes).
        
        :return: Dictionary of token prices.
        """
        current_prices = {
            'So11111111111111111111111111111111111111112': 150,  # Example: SOL price = $150
            'USDC111111111111111111111111111111111111111': 1,    # Example: USDC price = $1
        }
        return current_prices

    def get_holdings_by_address(self, token_address):
        """
        Returns the amount of a token in holdings.

        :param token_address: The token address (e.g., "So11111111111111111111111111111111111111112")
        :return: Amount of the token in the holdings
        """
        return self.holdings.get(token_address, 0)
