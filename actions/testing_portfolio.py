class TestingPortfolio:
    def __init__(self):
        # Initial holdings: Starting with 100 USDC balance
        self.holdings = {
            'USDC': 100  # Key for USDC holdings
        }  # Dictionary to store token holdings (token_symbol: amount)
        self.trade_history = []  # List to store buy/sell transactions

    def calculate_transaction_cost_percentage(self, price_per_token, amount):
        """
        Calculate the transaction cost based on the price and amount.
        Includes gas fees and DEX fees.

        :param price_per_token: The price of the token
        :param amount: The amount of the token to buy/sell
        :return: Transaction cost as a percentage of the total price
        """
        # Gas fee: A much lower value (e.g., 0.0005 SOL)
        gas_fee_percentage = 0.0005  # Solana gas fee, more realistic

        # DEX fee (lower than Ethereum, typically around 0.2%)
        dex_fee_percentage = 0.3 / 100  # 0.2% DEX fee

        total_cost = price_per_token * amount

        # Calculate total transaction cost as a sum of gas and DEX fees
        total_fee = (gas_fee_percentage + dex_fee_percentage) * total_cost
        return total_fee


    def buy(self, token, current_price, amount):
        """
        Buy a certain amount of a token using USDC.

        :param token: The token address or symbol (e.g., "So11111111111111111111111111111111111111112")
        :param amount: The amount of tokens to buy
        :param price_per_token: The price per token in USD
        """
        # Calculate the transaction cost (including gas and DEX fees)
        transaction_cost = self.calculate_transaction_cost_percentage(current_price, amount)
        total_cost = (current_price * amount) + transaction_cost

        # Check if we have enough USDC to perform the buy
        if self.holdings.get('USDC', 0) >= total_cost:
            # Deduct USDC from holdings
            self.holdings['USDC'] -= total_cost

            # Update holdings with purchased tokens
            if token in self.holdings:
                self.holdings[token] += amount
            else:
                self.holdings[token] = amount

            self.trade_history.append({"action": "buy", "token": token, "price": current_price, "amount": amount})
            print(f"✅ Purchased {amount} of {token} at ${current_price} each. Total cost: ${total_cost:.2f} (including fees)")
            return True
        else:
            print(f"❌ Not enough USDC to buy {amount} {token} at ${current_price} each. Total required: ${total_cost:.2f}")
            return False

    def sell(self, token, price_per_token, amount ):
        """
        Sell a certain amount of a token for USDC.

        :param token: The token address or symbol (e.g., "So11111111111111111111111111111111111111112")
        :param amount: The amount of tokens to sell
        :param price_per_token: The price per token in USD
        """
        # Calculate the transaction cost (including gas and DEX fees)
        transaction_cost = self.calculate_transaction_cost_percentage(price_per_token, amount)
        total_revenue = (price_per_token * amount) - transaction_cost

        # Check if enough tokens are available for selling
        if token in self.holdings and self.holdings[token] >= amount:
            self.holdings['USDC'] += total_revenue
            self.holdings[token] -= amount

            # Remove the token from holdings if the amount reaches zero
            if self.holdings[token] == 0:
                del self.holdings[token]

            self.trade_history.append({"action": "sell", "token": token, "price": price_per_token, "amount": amount})
            print(f"✅ Sold {amount} of {token} at ${price_per_token} each. Total revenue: ${total_revenue:.2f} (after fees)")
            return True
        else:
            print(f"❌ Not enough {token} to sell {amount}. Current holdings: {self.holdings.get(token, 0)}")
            return False

    def get_portfolio_value(self):
        """
        Return the total portfolio value in USD (cash balance + value of token holdings).

        :return: Total portfolio value in USD
        """
        holdings_value = sum(self.holdings[token] * self.fetch_current_prices().get(token, 0) for token in self.holdings if token != 'USDC')
        return self.holdings.get('USDC', 0) + holdings_value

    def portfolio_summary(self):
        """Print a summary of the current portfolio."""
        print("\n📊 Portfolio Summary:")
        print(f"💰 USDC Balance: ${self.holdings.get('USDC', 0):.2f}")
        if self.holdings:
            print("\n📈 Holdings:")
            for token, amount in self.holdings.items():
                if token != 'USDC':  # Skip displaying USDC as it's in the cash balance
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
            'USDC': 1,    # Example: USDC price = $1
        }
        return current_prices

    def get_holdings_by_address(self, token_address):
        """
        Returns the amount of a token in holdings.

        :param token_address: The token symbol (e.g., "So11111111111111111111111111111111111111112")
        :return: Amount of the token in the holdings
        """
        return self.holdings.get(token_address, 0)
