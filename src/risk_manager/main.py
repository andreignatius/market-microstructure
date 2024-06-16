class RiskManager:
    """
    - monitors PnL / MTM and the greeks and updates VaR / ES values
    - interacts w Strategy engine to trigger stop losses where applicable
    """

    def __init__(self, book_keeper):
        """
        This is risk manager, we will measure risk with the following tools
        1. Check balance (including cash)
        2. Portfolio value
        3. Positions (to check for short)
        """
        self.book_keeper = book_keeper
        self.risk_metrics = {}
        self.greeks = {}  # Options trading might require tracking of Greeks

    def check_available_balance(self,trade):
        current_available_balance = self.book_keeper.get_wallet_balance()
        historical_data_df = self.book_keeper.return_historical_data()
        current_portfolio_balance = historical_data_df['WalletBalance'].iloc[-1]
        minimum_cash_ratio = 0.25 # Set our desired minimum cash ratio
        post_trade_cash_ratio = (current_available_balance - trade) / current_portfolio_balance # assuming buy order
        # if post_trade_cash_ratio >= minimum cash ratio, continue trade, otherwise don't trade
        if post_trade_cash_ratio >= minimum_cash_ratio:
            return True # Allow buy order
        else: 
            return False 
        
    def get_available_tradable_balance(self):
        current_available_balance = self.book_keeper.get_wallet_balance()
        minimum_cash_ratio = 0.25 # Set our desired minimum cash ratio
        available_trade_balance = (1-minimum_cash_ratio) * current_available_balance
        return available_trade_balance
    
    def get_last_buy_price(self):
        last_buy_price = None
        historical_positions_df = self.book_keeper.return_historical_positions()
        for i in range(1, len(historical_positions_df)):
            # Check if the 'PositionAmt' has increased compared to the previous row
            if historical_positions_df['PositionAmt'].iloc[i] > historical_positions_df['PositionAmt'].iloc[i - 1]:
                last_buy_price = historical_positions_df['entryPrice'].iloc[i]
        # To handle NA or 0 values
        if last_buy_price is None or last_buy_price <= 0:
            print('Invalid last buy price')
            return None
        
        return last_buy_price

    def trigger_stop_loss(self):
        last_buy_price = self.get_last_buy_price()
        if last_buy_price is None or last_buy_price <= 0:
            print("Cannot trigger stop loss due to invalid last buy price")
            return False  # Do not trigger stop loss if last_buy_price is invalid

        market_price_df = self.book_keeper.return_historical_market_prices()
        latest_market_price = market_price_df['Price'].iloc[-1]
        historical_positions_df = self.book_keeper.return_historical_positions()
        current_btc_inventory = historical_positions_df['PositionAmt'].iloc[-1]

        stoploss_threshold = 0.02
        stoploss_limit_value = (1-stoploss_threshold) * last_buy_price

        if current_btc_inventory > 0:
            if latest_market_price <= stoploss_limit_value:
                return True # Liquidate positions now
            else:
                return False # do nothing
        else:
            return False # No inventory to liquidate
            

    def check_position(self,sellrequest):
        #sellrequest is limit sell order (in usdt)
        trade_balance_df = self.book_keeper.return_historical_positions()
        current_trade_balance = trade_balance_df['PositionAmt'].iloc[-1] * # trade balance is fraction of BTC
        if sellrequest < current_trade_balance: # assuming sellrequest is in $ amount
            return True # Allow sell
        else: 
            print('No short position allowed')
            return False # don't allow short position

    
    def check_buy_order_value(self,trade):
        market_price_df = self.book_keeper.return_historical_market_prices()
        latest_market_price = market_price_df['Price'].iloc[-1]
        upper_bound_price_ratio = 1.2 # Can adjust the tolerance, upper bound assuming buy order
        if trade <= latest_market_price * upper_bound_price_ratio:
            return True # Allow buy order
        else:
            print('Check buy order value')
            return False

    def check_sell_order_value(self,sellrequest):
        market_price_df = self.book_keeper.return_historical_market_prices()
        latest_market_price = market_price_df['Price'].iloc[-1]
        lower_bound_price_ratio = 0.9 # Can adjust the tolerance, lower bound for sell order
        if sellrequest <= latest_market_price * lower_bound_price_ratio:
            return True # Allow sell order
        else:
            print('Check sell order value')
            return False        

    def check_symbol(tradesymbol):
        ticker_control = 'BTCUSDT' # Set what ticker we want to trade to prevent ordering the wrong asset
        if tradesymbol == ticker_control:
            return True # Allow buy/sell order
        else:
            print('Check trade symbol')
            return False


## Unused functions

    def update_risk_metrics(self):
        """
        Update and calculate risk metrics based on current market data and portfolio positions.
        """
        # TODO: Implement the calculations for updating risk metrics like VaR, CVaR, etc.
        pass

    def evaluate_trade_risk(self, trade):
        """
        Evaluate the risk of a proposed trade to ensure it does not exceed predefined limits.
        """
        # TODO: Implement logic to evaluate trade risk based on current risk metrics
        return True

    def perform_stress_test(self):
        """
        Conduct stress tests and scenario analyses to assess potential impact of extreme market events.
        """
        # TODO: Implement stress testing logic
        pass

    def monitor_positions(self):
        """
        Continuously monitor open positions to ensure they remain within risk limits.
        """
        # TODO: Implement position monitoring logic
        pass

    def handle_breach(self, breach_details):
        """
        Handle breaches of risk limits, including logging the breach and taking corrective actions.
        """
        # TODO: Implement breach handling procedures
        pass

    def generate_risk_reports(self):
        """
        Generate detailed risk reports for internal review or regulatory compliance.
        """
        # TODO: Implement risk reporting logic
        pass

    def adjust_risk_limits(self):
        """
        Dynamically adjust risk limits based on latest market conditions and portfolio performance.
        """
        # TODO: Implement dynamic risk limit adjustments
        pass

    def monitor_pnl(self):
        """
        Continuously monitor profit and loss of the trading portfolio to identify trends and outliers.
        """
        # TODO: Implement the logic to calculate and monitor P&L
        pass

    def update_greeks(self):
        """
        Update the Greeks for options trading, crucial for managing derivatives positions.
        """
        # TODO: Implement logic to calculate and update Greeks like Delta, Gamma, Theta, Vega, Rho
        pass

    def update_var_es(self):
        """
        Update the Value at Risk (VaR) and Expected Shortfall (ES) calculations periodically.
        """
        # TODO: Implement the updates for VaR and ES based on latest data and statistical methods
        pass

    def trigger_stop_loss(self):
        """
        Automatically trigger stop losses for positions that exceed predefined loss thresholds.
        """
        # TODO: Implement the logic to execute stop-loss orders based on risk parameters
        pass

