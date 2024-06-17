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
        # trade is total dollar buy amount
        current_available_balance = self.book_keeper.get_wallet_balance()
        historical_data_df = self.book_keeper.return_historical_data()
        current_portfolio_balance = historical_data_df['WalletBalance'].iloc[-1]
        minimum_cash_ratio = 0.25 # Set our desired minimum cash ratio
        post_trade_cash_ratio = (current_available_balance - trade) / current_portfolio_balance # assuming buy order
        # if post_trade_cash_ratio >= minimum cash ratio, continue trade, otherwise don't trade
        if round(post_trade_cash_ratio, 2) >= minimum_cash_ratio:
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

    def get_current_btc_inventory(self):
        historical_positions_df = self.book_keeper.return_historical_positions()
        current_btc_inventory = historical_positions_df['PositionAmt'].iloc[-1]
        return current_btc_inventory
    
    def check_buy_position(self):
        current_btc_inventory = self.get_current_btc_inventory()
        if current_btc_inventory == 0:
            return True # Can buy if no current positions (prev was sell order)
        else:
            return False 
        
    def check_sell_position(self):
        current_btc_inventory = self.get_current_btc_inventory()
        if current_btc_inventory > 0:
            return True # Can sell if there is current long position (prev was buy order)
        else:
            return False

    def trigger_stop_loss(self):
        last_buy_price = self.get_last_buy_price()
        if last_buy_price is None or last_buy_price <= 0:
            print("Cannot trigger stop loss due to invalid last buy price")
            return False  # Do not trigger stop loss if last_buy_price is invalid

        market_price_df = self.book_keeper.return_historical_market_prices()
        latest_market_price = market_price_df['Price'].iloc[-1]
        current_btc_inventory = self.get_current_btc_inventory()

        stoploss_threshold = 0.02 # Set stoploss threshold here
        stoploss_limit_value = (1-stoploss_threshold) * last_buy_price

        if current_btc_inventory > 0:
            if latest_market_price <= stoploss_limit_value:
                return True # Liquidate positions now
            else:
                return False # do nothing
        else:
            return False # No inventory to liquidate
    
    def trigger_trading_halt(self):
        daily_maxdrawdown = self.book_keeper.calculate_max_drawdown()
        daily_mdd_threshold = -0.05 # Set daily maxdrawdown threshold here
        current_btc_inventory = self.get_current_btc_inventory
        if current_btc_inventory > 0:
            if daily_maxdrawdown <= daily_mdd_threshold:
                return True # Liquidate positions now
            else:
                return False # do nothing
        else:
            return False # No inventory to liquidate

    def check_short_position(self,ordersize):
        # ordersize is limit sell order in BTC
        current_btc_inventory = self.get_current_btc_inventory()
        if ordersize == current_btc_inventory: 
            return True # Allow sell
        else: 
            print('Check sell order size')
            return False 
    
    def check_buy_order_value(self, buyprice):
        # buyprice is limit price for buy order
        market_price_df = self.book_keeper.return_historical_market_prices()
        latest_market_price = market_price_df['Price'].iloc[-1]
        upper_buy_price_ratio = 1.1 # Set upper buy ratio here (don't buy too high)
        lower_buy_price_ratio = 0.6 # Set lower buy ratio here (avoid very low buy prices due to error)
        if lower_buy_price_ratio * latest_market_price <= buyprice <= latest_market_price * upper_buy_price_ratio:
            return True # Allow buy order if buyprice between lower and upper bounds
        else:
            print('Check buy order value')
            return False

    def check_sell_order_value(self,sellprice):
        # sellprice is limit price for sell order
        market_price_df = self.book_keeper.return_historical_market_prices()
        latest_market_price = market_price_df['Price'].iloc[-1]
        lower_sell_price_ratio = 0.9 # Set lower sell ratio here (don't sell too low)
        upper_sell_price_ratio = 1.4 # Set upper sell ratio here (avoid very high sell prices due to error)
        if latest_market_price * lower_sell_price_ratio <= sellprice <= latest_market_price * upper_sell_price_ratio:
            return True # Allow sell order if sellprice between lower and upper bounds
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

    # def update_risk_metrics(self):
    #     """
    #     Update and calculate risk metrics based on current market data and portfolio positions.
    #     """
    #     # TODO: Implement the calculations for updating risk metrics like VaR, CVaR, etc.
    #     pass

    # def evaluate_trade_risk(self, trade):
    #     """
    #     Evaluate the risk of a proposed trade to ensure it does not exceed predefined limits.
    #     """
    #     # TODO: Implement logic to evaluate trade risk based on current risk metrics
    #     return True

    # def perform_stress_test(self):
    #     """
    #     Conduct stress tests and scenario analyses to assess potential impact of extreme market events.
    #     """
    #     # TODO: Implement stress testing logic
    #     pass

    # def monitor_positions(self):
    #     """
    #     Continuously monitor open positions to ensure they remain within risk limits.
    #     """
    #     # TODO: Implement position monitoring logic
    #     pass

    # def handle_breach(self, breach_details):
    #     """
    #     Handle breaches of risk limits, including logging the breach and taking corrective actions.
    #     """
    #     # TODO: Implement breach handling procedures
    #     pass

    # def generate_risk_reports(self):
    #     """
    #     Generate detailed risk reports for internal review or regulatory compliance.
    #     """
    #     # TODO: Implement risk reporting logic
    #     pass

    # def adjust_risk_limits(self):
    #     """
    #     Dynamically adjust risk limits based on latest market conditions and portfolio performance.
    #     """
    #     # TODO: Implement dynamic risk limit adjustments
    #     pass

    # def monitor_pnl(self):
    #     """
    #     Continuously monitor profit and loss of the trading portfolio to identify trends and outliers.
    #     """
    #     # TODO: Implement the logic to calculate and monitor P&L
    #     pass

    # def update_greeks(self):
    #     """
    #     Update the Greeks for options trading, crucial for managing derivatives positions.
    #     """
    #     # TODO: Implement logic to calculate and update Greeks like Delta, Gamma, Theta, Vega, Rho
    #     pass

    # def update_var_es(self):
    #     """
    #     Update the Value at Risk (VaR) and Expected Shortfall (ES) calculations periodically.
    #     """
    #     # TODO: Implement the updates for VaR and ES based on latest data and statistical methods
    #     pass


