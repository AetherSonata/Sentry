from analytics.price_analytics import  MetricAnalyzer
from testing.utils import find_starting_point
from collections import Counter

# Global Configuration
SLIPPAGE_PERCENTAGE = 0.02  # 2% slippage
BUY_PERCENTAGE = 0.1        # 10% of available balance for buying
SELL_PERCENTAGE = 1         # 100% of holding when selling
STOP_LOSS_PERCENTAGE_LOW = 0.95  # 5% below current price
STOP_LOSS_PERCENTAGE_HIGH = 0.98 # 3% below current price
TAKE_PROFIT_PERCENTAGE = 1.07    # 10% above current price
TREND_LOOKBACK = 5
SOL_MINT_ADDRESS = "So11111111111111111111111111111111111111112"

class TradingEngine:
    def __init__(self, historical_price_data, interval, portfolio):
        """Initialize the trading engine with historical price data, interval settings, and a portfolio."""
        self.price_data = historical_price_data
        self.interval = interval
        self.active_position = None  # This will hold our current (averaged) position
        self.metrics = []
        self.group_trends = []
        self.portfolio = portfolio
        self.metric_analyzer = MetricAnalyzer(self.interval)

        print(len(self.price_data))
        self.initialize_prior_metrics()
    
    def initialize_prior_metrics(self):
        # Initialize the metric analyzer with historical price data  
        lookback = TREND_LOOKBACK
        for i in range(lookback):
            lookback -= 1
            self.metric_analyzer.update_price_data(self.price_data[:(len(self.price_data) - lookback )])  
            self.metrics.append(self.metric_analyzer.calculate_metrics_for_intervals())
            

    def check_for_trading_action(self, token_address):
        # Calculate max interval RSI for the latest price data
        _, max_interval = find_starting_point(self.price_data, self.interval)
        # Append the latest RSI calculation
        self.metric_analyzer.update_price_data(self.price_data)
        self.metrics.append(self.metric_analyzer.calculate_metrics_for_intervals())
        self.group_trends.append(self.determine_overall_trend()) 
        
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
        # print(action)
        return action

    def check_if_buy_signal(self, current_price):
        # get latest metrics
        current_metrics = self.metrics[-1]
        # Check if RSI is below 30 (oversold)
        if current_metrics.get(f"RSI_15m", 0) < 30 and current_metrics.get(f"RSI_1H", 0) < 30:
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
        # print(f"💰 Spending ${buy_total_in_usd:.2f} at adjusted price ${adjusted_price:.2f} per token; tokens received: {buy_amount:.6f}")
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
    


    def determine_overall_trend(self):
        """Determine overall trend by incorporating both RSI, smaller EMAs, and the 200-EMA confirmation (Golden Cross/Death Cross). """
        
        if not self.metrics:
            return {"group_trends": {}, "overall_trend": "no data", "votes": {}}

        metrics = self.metrics[-1]  # Latest metrics

        # Define groups of intervals
        groups = {
            "short_term": ["1m", "5m", "15m"],
            "mid_term": ["30m", "1h", "4h"],
            "long_term": ["12h", "1d", "3d", "1w"]
        }

        group_trends = {}
        for group_name, intervals in groups.items():
            rsi_list = []
            ema_signal_list = []
            golden_cross = 0  # 1 for bullish, -1 for bearish

            for interval in intervals:
                rsi_key = f"RSI_{interval}"
                ema15_key = f"15-Point-EMA_{interval}"
                ema50_key = f"50-Point-EMA_{interval}"
                ema200_key = f"200-Point-EMA_{interval}"

                # Time-based trend determination
                rsi_trend = self.determine_trend_over_time(rsi_key) if rsi_key in metrics else None
                ema_trend = self.determine_trend_over_time(ema15_key, ema50_key) if ema15_key in metrics and ema50_key in metrics else None

                # Store trend signals
                if rsi_trend:
                    rsi_list.append(rsi_trend)
                if ema_trend:
                    ema_signal_list.append(ema_trend)

                # Check for Golden Cross / Death Cross
                if ema200_key in metrics and ema15_key in metrics:
                    ema200 = metrics[ema200_key]
                    if metrics[ema15_key] > ema200:
                        golden_cross = 1  # Bullish
                    elif metrics[ema15_key] < ema200:
                        golden_cross = -1  # Bearish

            # Determine dominant trend in the group
            if rsi_list or ema_signal_list:
                avg_rsi_trend = Counter(rsi_list).most_common(1)[0][0] if rsi_list else None
                avg_ema_trend = Counter(ema_signal_list).most_common(1)[0][0] if ema_signal_list else None

                # Final group trend determination
                if avg_rsi_trend == "bullish" and avg_ema_trend == "bullish" : #TODO implement golden cross +1/-1 logic ( maybe better for takeprofit and size setting)
                    group_trends[group_name] = "bullish"
                elif avg_rsi_trend == "bearish" and avg_ema_trend == "bearish" :
                    group_trends[group_name] = "bearish"
                else:
                    group_trends[group_name] = "neutral"
            else:
                group_trends[group_name] = "no data"

        # Determine overall trend by majority vote
        votes = Counter(group_trends.values())
        overall_trend = max(votes, key=votes.get) if votes else "neutral"

        return {
            "group_trends": group_trends,
            "overall_trend": overall_trend,
            "votes": votes
        } 

    def determine_trend_over_time(self, metric_key, compare_key=None, lookback=TREND_LOOKBACK):
        """Analyze RSI or EMA over the last `lookback` data points to determine trend direction over time."""
        
        if len(self.metrics) < lookback:
            return "insufficient data"

        # Extract metric values over `lookback` period
        values = [entry.get(metric_key) for entry in self.metrics[-lookback:] if entry.get(metric_key) is not None]

        # Ensure there are enough valid values
        if len(values) < 2:
            return "neutral"

        if compare_key:
            compare_values = [entry.get(compare_key) for entry in self.metrics[-lookback:] if entry.get(compare_key) is not None]

            if len(compare_values) < 2:
                return "neutral"

            return "bullish" if values[-1] > compare_values[-1] else "bearish" if values[-1] < compare_values[-1] else "neutral"

        return "bullish" if values[-1] > values[0] else "bearish" if values[-1] < values[0] else "neutral"



    def confirm_short_mid_ema_change(self, trend_confirmation_lookback=5, trend_confirmation_threshold=1):
        """
        Checks the past `trend_confirmation_lookback` number of group EMA/RSI trends.
        If both short-term and mid-term trends are 'neutral' in at least `trend_confirmation_threshold` intervals, returns True.
        
        :param trend_confirmation_lookback: Number of past+current group trends to check.
        :param trend_confirmation_threshold: Minimum number of 'neutral' trends required.
        :return: True if condition is met, otherwise False.
        """
        if len(self.group_trends) < trend_confirmation_lookback:
            return False  # Not enough data to confirm a trend change

        neutral_count = 0

        for trend in self.group_trends[-trend_confirmation_lookback:]:  # Look back at the required number of intervals
            short_term = trend["group_trends"]["short_term"]
            mid_term = trend["group_trends"]["mid_term"]

            if short_term == "neutral" and mid_term == "neutral":
                neutral_count += 1

            if neutral_count >= trend_confirmation_threshold:
                return True  # Condition met

        return False  # Not enough neutral trends
    
    def confirm_group_rsi_threshold(self, group_intervals, trend_confirmation_lookback=5, 
                                    rsi_threshold=30, direction="below", trend_confirmation_threshold=None):
        """
        Analyzes the last `trend_confirmation_lookback` snapshots in self.metrics for RSI values 
        from the specified group intervals.
        
        For each snapshot, it computes the average RSI across available intervals in the group.
        It then counts how many snapshots have an average RSI that meets the condition:
        - If direction == "below", snapshot counts if average RSI < rsi_threshold.
        - If direction == "above", snapshot counts if average RSI > rsi_threshold.
        
        If no snapshots contain any RSI data for the group, it prints a warning.
        
        :param group_intervals: List of intervals for the group (e.g. ["1m", "5m", "15m"]).
        :param trend_confirmation_lookback: Number of recent metric snapshots to examine.
        :param rsi_threshold: RSI threshold value.
        :param direction: "below" or "above" to check whether the average RSI is below or above the threshold.
        :param trend_confirmation_threshold: (Optional) Minimum number of snapshots required to meet the condition.
        :return: Dictionary with keys 'count' and 'total' representing the number of snapshots meeting the condition and the total snapshots evaluated.
        """
        # Ensure there are enough snapshots
        if len(self.metrics) < trend_confirmation_lookback:
            print("Not enough snapshots for calculation of group")
            return {"count": 0, "total": 0}
        
        count = 0
        total = 0
        # Iterate over the last trend_confirmation_lookback snapshots in self.metrics
        for snapshot in self.metrics[-trend_confirmation_lookback:]:
            # Extract RSI values for the intervals in the group (if available)
            rsi_values = [snapshot.get(f"RSI_{interval}") for interval in group_intervals 
                        if snapshot.get(f"RSI_{interval}") is not None]
            if not rsi_values:
                continue  # Skip this snapshot if no RSI data is available for the group
            avg_rsi = sum(rsi_values) / len(rsi_values)
            total += 1
            
            if direction == "below" and avg_rsi < rsi_threshold:
                count += 1
            elif direction == "above" and avg_rsi > rsi_threshold:
                count += 1

        if total == 0:
            print("Not enough data points for calculation of group")
        
        # Optionally, enforce a minimum threshold count if provided
        if trend_confirmation_threshold is not None and count < trend_confirmation_threshold:
            # Return the counts so you know it didn't meet the threshold
            return {"count": count, "total": total}
        
        return {"count": count, "total": total}


    def count_rsi_passing_threshold_for_groups(self, short_term=True, mid_term=True, long_term=True, direction="below"):
        """
        Uses the generic confirm_group_rsi_threshold method for different RSI analysis groups.

        Groups:
        - Short-term RSI (1m, 5m, 15m) checks if the average RSI is below 30.
        - Mid-term RSI (30m, 1h, 4h) checks if the average RSI is below 50.
        - Long-term RSI (12h, 1d, 3d, 1w) checks if the average RSI is below 70.

        The function allows enabling/disabling each group using the parameters.

        :param short_term: Whether to calculate short-term RSI.
        :param mid_term: Whether to calculate mid-term RSI.
        :param long_term: Whether to calculate long-term RSI.
        :return: Dictionary with results for all groups (disabled ones return None).
        """
        results = {
            "short_term": None,
            "mid_term": None,
            "long_term": None
        }

        if short_term:
            results["short_term"] = self.confirm_group_rsi_threshold(
                group_intervals=["1m", "5m", "15m"],
                trend_confirmation_lookback=5,
                rsi_threshold=30,
                direction=direction
            )
            print("Short-term RSI result:", results["short_term"])

        if mid_term:
            results["mid_term"] = self.confirm_group_rsi_threshold(
                group_intervals=["30m", "1h", "4h"],
                trend_confirmation_lookback=5,
                rsi_threshold=50,
                direction=direction
            )
            print("Mid-term RSI result:", results["mid_term"])

        if long_term:
            results["long_term"] = self.confirm_group_rsi_threshold(
                group_intervals=["12h", "1d", "3d", "1w"],
                trend_confirmation_lookback=5,
                rsi_threshold=70,
                direction=direction
            )
            print("Long-term RSI result:", results["long_term"])

        return results


    def confirm_rsi_oversold():
        pass

        
