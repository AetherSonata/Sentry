class TestingPortfolio:
    def __init__(self):
        self.holdings = {
            "So11111111111111111111111111111111111111112": 10,  # Example SOL balance
            "USDC111111111111111111111111111111111111111": 10   # Example USDC balance
        }
        self.trade_history = []  # List to store buy/sell transactions

    def buy(self, token, current_price, amount):
        """
        Buy a certain amount of a token at a given price.

        :param token: The token address (e.g., "So11111111111111111111111111111111111111112")
        :param amount: The amount of tokens to buy
        :param price_per_token: The price per token in USD
        """
        # Check if we have enough SOL to deploy for the purchase
        sol_balance = self.holdings.get("So11111111111111111111111111111111111111112", 0)
        total_cost = 

        if sol_balance >= total_cost:
            # Proceed with purchase: Deduct SOL and add token to holdings
            self.holdings["So11111111111111111111111111111111111111112"] -= total_cost
            self.holdings[token] = self.holdings.get(token, 0) + amount  # Add the purchased token

            self.trade_history.append({"action": "buy", "token": token, "price": price_per_token, "amount": amount})
            return True
        else:
            print(f"❌ Not enough SOL to buy {amount} {token} at ${price_per_token} each. Total required: ${total_cost:.2f}")
            return False

    def sell(self, token, amount, price_per_token):
        """
        Sell a certain amount of a token at a given price.

        :param token: The token address (e.g., "So11111111111111111111111111111111111111112")
        :param amount: The amount of tokens to sell
        :param price_per_token: The price per token in USD
        """
        # Check if we have enough tokens to sell
        token_balance = self.holdings.get(token, 0)

        if token_balance >= amount:
            # Proceed with sale: Add SOL to balance and remove token from holdings
            total_revenue = price_per_token * amount
            self.holdings["So11111111111111111111111111111111111111112"] += total_revenue
            self.holdings[token] -= amount

            if self.holdings[token] == 0:
                del self.holdings[token]  # Remove token if balance is zero

            self.trade_history.append({"action": "sell", "token": token, "price": price_per_token, "amount": amount})
            return True
        else:
            print(f"❌ Not enough {token} to sell {amount}. Current holdings: {token_balance}")
            return False

    def get_portfolio_value(self, current_prices):
        """
        Calculate the total portfolio value based on current prices.

        :param current_prices: Dictionary of token prices (e.g., {"SOL": 120.5})
        :return: Total portfolio value (cash + holdings value)
        """
        holdings_value = sum(self.holdings[token] * current_prices.get(token, 0) for token in self.holdings)
        return holdings_value

    def portfolio_summary(self, current_prices=None):
        """Print a summary of the current portfolio."""
        print("\n📊 Portfolio Summary:")
        print(f"💰 Cash Balance: ${self.holdings.get('So11111111111111111111111111111111111111112', 0):.2f}")
        
        if self.holdings:
            print("\n📈 Holdings:")
            for token, amount in self.holdings.items():
                value = current_prices[token] * amount if current_prices else "N/A"
                print(f"  - {token}: {amount:.4f} (Value: ${value:.2f})")
        
        total_value = self.get_portfolio_value(current_prices) if current_prices else "N/A"
        print(f"\n💵 Total Portfolio Value: ${total_value}\n")

    def fetch_current_prices(self):
        """
        Fetches the current prices for all tokens in the holdings dictionary.
        
        :param get_current_price: A function that takes a token address and returns the current price.
        :return: Dictionary of token prices.
        """
        current_prices = {}
        
        for token_address in self.holdings.keys():
            current_prices[token_address] = mock_get_current_price(token_address)
        
        return current_prices

    def get_holdings_by_adress(self, token_adress):
        return self.holdings.get(token_adress, 0)
    
    
@staticmethod
def mock_get_current_price(token_address):
    mock_prices = {
        'So11111111111111111111111111111111111111112': 150,  # Example: SOL price = $150
        'USDC111111111111111111111111111111111111111': 1,    # Example: USDC price = $1
    }
    return mock_prices.get(token_address, 0)  # Default to 0 if token not found
