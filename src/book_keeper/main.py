import pandas as pd


class BookKeeper:
    """
    This class stores all executed trades and provides analyses based on executed trades.
    """

    def __init__(self, initial_cash):
        self.initial_cash = initial_cash
        self.trades = pd.DataFrame(
            columns=[
                "TradeID",
                "Date",
                "Symbol",
                "Quantity",
                "Price",
                "Type",
                "TransactionCost",
            ]
        )
        self.market_prices = pd.DataFrame(columns=["Date", "Symbol", "Price"])
        self.realized_pnl = 0
        self.unrealized_pnl = 0
        self.positions = {}

    @property
    def get_initial_cash(self):
        return self.initial_cash

    @property
    def get_unrealized_pnl(self):
        return self.unrealized_pnl

    @property
    def get_realized_pnl(self):
        return self.realized_pnl

    @property
    def get_trades(self):
        return self.trades

    @property
    def get_trade_by_id(self, trade_id):
        return self.trades[self.trades["TradeID"] == trade_id]

    def add_trade(
        self, trade_id, date, symbol, quantity, price, trade_type, transaction_cost
    ):
        self.trades = self.trades.append(
            {
                "TradeID": trade_id,
                "Date": date,
                "Symbol": symbol,
                "Quantity": quantity,
                "Price": price,
                "Type": trade_type,
                "TransactionCost": transaction_cost,
            },
            ignore_index=True,
        )
        self._update_realized_pnl(symbol, quantity, price, trade_type, transaction_cost)
        self._update_unrealized_pnl()

    def update_market_price(self, date, symbol, price):
        self.market_prices = self.market_prices.append(
            {"Date": date, "Symbol": symbol, "Price": price}, ignore_index=True
        )
        self._update_unrealized_pnl()

    def export_data(self):
        """
        Export the trades in CSV format.
        """
        self.trades.to_csv("outputs/trades.csv")

    def calculate_max_drawdown(self):
        pnl_series = self._calculate_pnl_series()
        roll_max = pnl_series.cummax()
        drawdown = (pnl_series - roll_max) / roll_max
        return drawdown.min()

    def calculate_sharpe_ratio(self, risk_free_rate=0):
        pnl_series = self._calculate_pnl_series()
        returns = pnl_series.pct_change().dropna()
        excess_returns = returns - risk_free_rate
        return excess_returns.mean() / excess_returns.std()

    def _calculate_pnl_series(self):
        portfolio_value = self.trades.apply(
            lambda row: (row["Price"] * row["Quantity"] - row["TransactionCost"])
            if row["Type"] == "buy"
            else (-row["Price"] * row["Quantity"] + row["TransactionCost"]),
            axis=1,
        )
        pnl_series = portfolio_value.cumsum() - portfolio_value[0]
        return pnl_series
    
    def _update_realized_pnl(
        self, symbol, quantity, price, trade_type, transaction_cost
    ):
        if price == 0 or quantity == 0:
            return

        if symbol not in self.positions:
            self.positions[symbol] = {"cost": 0, "quantity": 0}

        curr_cost, curr_quantity = (
            self.positions[symbol]["cost"],
            self.positions[symbol]["quantity"],
        )

        if trade_type == "buy":
            if curr_quantity < 0:
                quantity_to_close = min(quantity, abs(curr_quantity))
                quantity_to_long = max(quantity + curr_quantity, 0)
                if quantity_to_close < abs(curr_quantity):
                    # Close partial short positions
                    new_cost = curr_cost
                    new_quantity = curr_quantity + quantity_to_close
                elif quantity_to_close == abs(curr_quantity):
                    # Close all short positions
                    new_cost = 0
                    new_quantity = 0
                    if quantity_to_long > 0:
                        # Add long position after closing existing short position
                        new_cost += price
                        new_quantity += quantity_to_long
            else:
                quantity_to_close = 0
                quantity_to_long = quantity

                # Add long position to existing long position
                new_cost += (curr_cost * curr_quantity + price * quantity_to_long) / (
                    curr_quantity + quantity_to_long
                )
                new_quantity = curr_quantity + quantity_to_long

            pnl = quantity_to_close * (curr_cost - price) - transaction_cost
            self.realized_pnl += pnl

            self.positions[symbol] = {"cost": new_cost, "quantity": new_quantity}
        elif trade_type == "sell":
            if curr_quantity > 0:
                quantity_to_close = min(quantity, curr_quantity)
                quantity_to_short = min(curr_quantity - quantity, 0)
                if quantity_to_close < curr_quantity:
                    # Close partial long positions
                    new_cost = curr_cost
                    new_quantity = curr_quantity - quantity_to_close
                elif quantity_to_close == curr_quantity:
                    # Close all long positions
                    new_cost = 0
                    new_quantity = 0
                    if quantity_to_short < 0:
                        # Add short position after closing existing long position
                        new_cost += price
                        new_quantity += quantity_to_short
            else:
                quantity_to_close = 0
                quantity_to_short = -quantity

                # Add short position to existing short position
                new_cost = (
                    curr_cost * abs(curr_quantity) + price * abs(quantity_to_short)
                ) / (abs(curr_quantity) + abs(quantity_to_short))
                new_quantity = curr_quantity + quantity_to_short

            pnl = quantity_to_close * (curr_cost - price) - transaction_cost
            self.realized_pnl += pnl

            self.positions[symbol] = {"cost": new_cost, "quantity": new_quantity}

    def _update_unrealized_pnl(self):
        pass
