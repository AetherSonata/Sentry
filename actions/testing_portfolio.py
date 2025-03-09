class TestingPortfolio:
    def __init__(self):
        # Initial holdings: Starting with 10 USD balance
        self.usd_balance = 10  # USD balance in portfolio
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
            # Proceed with purchase: Deduct USD and simulate acquiring tokens
            self.usd_balance -= total_cost
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
        # Here, we simulate selling by adding USD to the balance
        total_revenue = price_per_token * amount
        self.usd_balance += total_revenue
        self.trade_history.append({"action": "sell", "token": token, "price": price_per_token, "amount": amount})
        print(f"✅ Sold {amount} of {token} at ${price_per_token} each. Total revenue: ${total_revenue:.2f}")
        return True

    def get_portfolio_value(self):
        """
        Return the total portfolio value in USD (only cash balance for now).

        :return: Total portfolio value in USD
        """
        return self.usd_balance

    def portfolio_summary(self):
        """Print a summary of the current portfolio."""
        print("\n📊 Portfolio Summary:")
        print(f"💰 Cash Balance: ${self.usd_balance:.2f}")
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
        # For now, we don't track tokens, but this can be implemented later
        return 0
