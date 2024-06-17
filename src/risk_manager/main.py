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

    def check_available_balance(self, trade):
        # trade is total dollar buy amount
        print(f"buy trade check amt{trade}")
        historical_data_df = self.book_keeper.return_historical_data()

        current_available_balance = float(
            historical_data_df["AvailableBalance"].iloc[-1]
        )
        print(f"[risk mgr] AvailableBalance :{current_available_balance}")

        current_portfolio_balance = float(historical_data_df["WalletBalance"].iloc[-1])
        print(f"[risk mgr] WalletBalance :{current_available_balance}")

        minimum_cash_ratio = 0.25  # Set our desired minimum cash ratio
        post_trade_cash_ratio = (
            current_available_balance - trade
        ) / current_portfolio_balance  # assuming buy order
        post_trade_cash_ratio = round(post_trade_cash_ratio, 2)
        print(f"post trade ratio {post_trade_cash_ratio}")
        # if post_trade_cash_ratio >= minimum cash ratio, continue trade, otherwise don't trade
        if post_trade_cash_ratio >= minimum_cash_ratio:
            return True  # Allow buy order
        else:
            return False

    def get_available_tradable_balance(self):
        # current_available_balance = self.book_keeper.get_wallet_balance()
        historical_data_df = self.book_keeper.return_historical_data()
        current_available_balance = float(
            historical_data_df["AvailableBalance"].iloc[-1]
        )
        print(f"[risk mgr] AvailableBalance :{current_available_balance}")
        minimum_cash_ratio = 0.25  # Set our desired minimum cash ratio
        available_trade_balance = (1 - minimum_cash_ratio) * current_available_balance
        return available_trade_balance

    def get_last_buy_price(self):
        last_buy_price = None
        historical_positions_df = self.book_keeper.return_historical_positions()
        for i in range(1, len(historical_positions_df)):
            # Check if the 'PositionAmt' has increased compared to the previous row
            if (
                historical_positions_df["PositionAmt"].iloc[i]
                > historical_positions_df["PositionAmt"].iloc[i - 1]
            ):
                last_buy_price = historical_positions_df["entryPrice"].iloc[i]
        # To handle NA or 0 values
        if last_buy_price is None or last_buy_price <= 0:
            print("Invalid last buy price")
            return None

        return last_buy_price

    def get_current_btc_inventory(self):
        historical_positions_df = self.book_keeper.return_historical_positions()
        current_btc_inventory = historical_positions_df["PositionAmt"].iloc[-1]
        return current_btc_inventory

    def check_buy_position(self):
        current_btc_inventory = float(self.get_current_btc_inventory())
        if current_btc_inventory == 0:
            return True  # Can buy if no current positions (prev was sell order)
        else:
            return False

    def check_sell_position(self):
        current_btc_inventory = float(self.get_current_btc_inventory())
        if current_btc_inventory > 0:
            return (
                True  # Can sell if there is current long position (prev was buy order)
            )
        else:
            return False

    def trigger_stop_loss(self):
        last_buy_price = self.get_last_buy_price()
        if last_buy_price is None or last_buy_price <= 0:
            print("Cannot trigger stop loss due to invalid last buy price")
            return False  # Do not trigger stop loss if last_buy_price is invalid

        market_price_df = self.book_keeper.return_historical_market_prices()
        latest_market_price = market_price_df["Price"].iloc[-1]
        current_btc_inventory = self.get_current_btc_inventory()

        stoploss_threshold = 0.02  # Set stoploss threshold here
        stoploss_limit_value = (1 - stoploss_threshold) * last_buy_price
        print(
            f"STOPLOSS CHECK: stoploss_limit_value{stoploss_limit_value}, latest_market_price{latest_market_price},  last_buy_price{last_buy_price}"
        )
        stoploss_limit_value = float(stoploss_limit_value)
        latest_market_price = float(latest_market_price)
        last_buy_price = float(last_buy_price)

        if current_btc_inventory > 0:
            if latest_market_price <= stoploss_limit_value:
                return True  # Liquidate positions now
            else:
                return False  # do nothing
        else:
            return False  # No inventory to liquidate

    def trigger_trading_halt(self):
        daily_maxdrawdown = self.book_keeper.calculate_max_drawdown()
        daily_mdd_threshold = -0.05  # Set daily maxdrawdown threshold here
        current_btc_inventory = self.get_current_btc_inventory()
        if current_btc_inventory > 0:
            if daily_maxdrawdown <= daily_mdd_threshold:
                return True  # Liquidate positions now
            else:
                return False  # do nothing
        else:
            return False  # No inventory to liquidate

    def check_short_position(self, ordersize):
        # ordersize is limit sell order in BTC
        current_btc_inventory = self.get_current_btc_inventory()
        print(f"current_btc_inventory {current_btc_inventory} vs ordersize {ordersize}")
        if current_btc_inventory == 0 and ordersize == 0:
            print("All is Zero, nothing to do")
        elif ordersize <= current_btc_inventory:
            return True  # Allow sell
        else:
            print("No short position allowed")
            return False  # don't allow short position

    def check_buy_order_value(self, buyprice):
        # buyprice is limit price for buy order
        market_price_df = self.book_keeper.return_historical_market_prices()
        latest_market_price = float(market_price_df["Price"].iloc[-1])
        upper_buy_price_ratio = 1.1  # Set upper buy ratio here (don't buy too high)
        lower_buy_price_ratio = (
            0.6  # Set lower buy ratio here (avoid very low buy prices due to error)
        )
        if (
            lower_buy_price_ratio * latest_market_price <= buyprice
            and buyprice <= latest_market_price * upper_buy_price_ratio
        ):
            return True  # Allow buy order if buyprice between lower and upper bounds
        else:
            print("Check buy order value")
            return False

    def check_sell_order_value(self, sellprice):
        # last buy
        last_buy_price = self.get_last_buy_price()
        if last_buy_price == None:
            last_buy_price = 0
        # sellprice is limit price for sell order
        market_price_df = self.book_keeper.return_historical_market_prices()
        latest_market_price = float(market_price_df["Price"].iloc[-1])
        lower_sell_price_ratio = 0.9  # Set lower sell ratio here (don't sell too low)
        upper_sell_price_ratio = (
            1.4  # Set upper sell ratio here (avoid very high sell prices due to error)
        )
        if (
            latest_market_price * lower_sell_price_ratio <= sellprice
            and sellprice <= latest_market_price * upper_sell_price_ratio
            and sellprice >= last_buy_price
        ):
            return True  # Allow sell order if sellprice between lower and upper bounds
        else:
            print("Check sell order value")
            return False

    def check_symbol(tradesymbol):
        ticker_control = "BTCUSDT"  # Set what ticker we want to trade to prevent ordering the wrong asset
        if tradesymbol == ticker_control:
            return True  # Allow buy/sell order
        else:
            print("Check trade symbol")
            return False
