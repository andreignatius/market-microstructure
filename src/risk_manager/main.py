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

    def check_balance(self,trade):
        current_balance = self.book_keeper.get_balance()
        initial_balance = self.book_keeper.get_initial_balance()
        reserve_ratio = 0.10
        balance_limit = reserve_ratio * initial_balance

        post_trade_balance = current_balance - trade # assuming buy order
        # if post_trade_balance > balance_limit, continue trade, otherwise don't trade
        if post_trade_balance > balance_limit:
            print('Proceed with trade')
            return True
        else: return False # Don't trade

    def check_PnL(self):
        portfolio_value = self.book_keeper.get_WalletBalance() # in the historical_data dataframe, ['WalletBalance'] dataframe

    def check_position(self,sellrequest):
        current_trade_balance = self.book_keeper.get_positionamount() # trade balance is amnt of BTC in $
        if sellrequest < current_trade_balance: # assuming sellrequest is in $ amount
            return True # allow sell
        else: return False # don't allow short position
        
    # Other pre-trade controls
    def check_order_size(tradesize):
        order_size_control = 0.02 # insert amount of BTC here
        if tradesize == order_size_control:
            return True 
        else: 
            print('Check order size')
            return False
    
    def check_order_value(self,trade):
        market_price_df = self.book_keeper.return_historical_market_prices()
        latest_market_price = market_price_df['Price'].iloc[-1]
        upper_bound_price_ratio = 1.2 # Can adjust the tolerance, upper bound assuming buy order
        if trade <= latest_market_price * upper_bound_price_ratio:
            return True
        else:
            print('Check order value')
            return False
        

    def check_symbol(tradesymbol):
        ticker_control = 'BTCUSDT' # Set what ticker we want to trade to prevent ordering the wrong asset
        if tradesymbol == ticker_control:
            return True
        else:
            print('Check trade symbol')
            return False












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
