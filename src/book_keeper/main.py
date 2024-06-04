import pandas as pd


class BookKeeper:
    """
    This class stores all executed trades and provides analyses based on executed trades.
    """

    def __init__(self, initial_cash):
        self.initial_cash = initial_cash
        self.historical_data = pd.DataFrame(
            columns=[
                "Date",
                "RealizedProfit",
                "UnrealizedProfit",

            ]
        )
        self.historical_positions = pd.DataFrame(
            columns=[
                "Symbol",
                "Date",
                "AvgPrice",
                "PositionAmt",
            ]
        )
        self.market_prices = pd.DataFrame(columns=["Date", "Symbol", "Price"])

    @property
    def get_initial_cash(self):
        return self.initial_cash

    @property
    def get_unrealized_pnl(self):
        # TODO
        # Return last record in self.historical_position
        pass

    @property
    def get_realized_pnl(self):
        # TODO
        # Return last record in self.historical_position
        pass

    def update_bookkeeper(self, date, middle_price):
        # TODO
        # 1. Append date and middle_price to df market prices
        # 2. Make API call to get realised and unrealised price, and positions
        # 3. Update historical_data, historical_positions
        # 4. Trim data
        pass

    def calculate_max_drawdown(self):
        # TODO
        pass

    def calculate_sharpe_ratio(self, risk_free_rate=0):
        # TODO
        pass

    def calculate_vol(self):
        # TODO
        pass
