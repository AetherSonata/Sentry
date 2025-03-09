class TestingPortfolio:
    def __init__(self):
        # Initial holdings: Starting with 100 USDC balance
        self.holdings = {
            'USDC': 100  # Key for USDC holdings
        }  # Dictionary to store token holdings (token_symbol: amount)
        self.trade_history = []  # List to store buy/sell transactions

    def calculate_transaction_fee(self, price_per_token, amount):
        """
        Calculate the transaction cost based on the price and amount.
        Includes gas fees and DEX fees.

        :param price_per_token: The price of the token
        :param amount: The amount of the token to buy/sell
        :return: Transaction cost as a percentage of the total price
        """
        # Gas fee: 
        gas_fee = 0.32 # Solana gas fee, more realistic

        # DEX fee (lower than Ethereum, typically around 0.2%)
        dex_fee_percentage = 0.3 / 100  # 0.2% DEX fee

        total_cost = price_per_token * amount

        # Calculate total transaction cost as a sum of gas and DEX fees
        total_fee = ( dex_fee_percentage) * total_cost + gas_fee
        return total_fee


    def buy(self, token, current_price, amount, slippage):
        """
        Buy a certain amount of a token using USDC.

        :param token: The token address or symbol (e.g., "So11111111111111111111111111111111111111112")
        :param amount: The amount of tokens to buy
        :param current_price: The price per token in USD before slippage
        :param slippage: The slippage tolerance (e.g., 0.02 for 2%)
        """

        # Apply slippage to execution price (increasing the price paid per token)
        slippage_adjusted_price = current_price * (1 + slippage)

        # Calculate the total cost before transaction fees
        total_cost_before_fees = slippage_adjusted_price * amount

        # Calculate transaction fees (gas + DEX fees)
        transaction_cost = self.calculate_transaction_fee(current_price, amount)

        # Final total cost including slippage and fees
        total_cost = total_cost_before_fees + transaction_cost

        # Print slippage cost
        slippage_cost = (slippage_adjusted_price - current_price) * amount
        print(f"📉 Slippage cost: ${slippage_cost:.2f}")

        # Check if we have enough USDC to perform the buy
        if self.holdings.get('USDC', 0) >= total_cost:
            # Deduct USDC from holdings
            self.holdings['USDC'] -= total_cost

            # Update holdings with purchased tokens
            if token in self.holdings:
                self.holdings[token] += amount
            else:
                self.holdings[token] = amount

            self.trade_history.append({
                "action": "buy", 
                "token": token, 
                "price": slippage_adjusted_price, 
                "amount": amount
            })

            # print(f"✅ Purchased {amount} of {token} at ${slippage_adjusted_price:.2f} each (after slippage).")
            # print(f"💵 Total cost: ${total_cost:.2f} (including fees).")
            return True
        else:
            print(f"❌ Not enough USDC to buy {amount} {token} at ${slippage_adjusted_price:.2f} each. Total required: ${total_cost:.2f}")
            return False


    def sell(self, token, price_per_token, amount, slippage):
        """
        Sell a certain amount of a token for USDC.

        :param token: The token address or symbol (e.g., "So11111111111111111111111111111111111111112")
        :param amount: The amount of tokens to sell
        :param price_per_token: The price per token in USD
        :param slippage: The slippage tolerance (e.g., 0.02 for 2%)
        """
        # Apply slippage to execution price
        slippage_adjusted_price = price_per_token * (1 - slippage)
        
        # Calculate revenue BEFORE transaction costs
        revenue_before_fees = slippage_adjusted_price * amount

        # Calculate transaction cost (gas + DEX fees)
        transaction_cost = self.calculate_transaction_fee(price_per_token, amount)

        # Final revenue after deducting transaction fees
        revenue_after_fees = revenue_before_fees - transaction_cost

        # Print slippage cost
        slippage_cost = (price_per_token * amount) - revenue_before_fees
        print(f"📉 Slippage cost: ${slippage_cost:.2f}")

        # Check if enough tokens are available for selling
        if token in self.holdings and self.holdings[token] >= amount:
            self.holdings['USDC'] += revenue_after_fees
            self.holdings[token] -= amount

            # Remove the token from holdings if the amount reaches zero
            if self.holdings[token] == 0:
                del self.holdings[token]

            self.trade_history.append({
                "action": "sell", 
                "token": token, 
                "price": slippage_adjusted_price, 
                "amount": amount
            })

            # print(f"✅ Sold {amount} of {token} at ${slippage_adjusted_price:.2f} each (after slippage).")
            # print(f"💵 Total revenue: ${revenue_after_fees:.2f} (after fees).")
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
