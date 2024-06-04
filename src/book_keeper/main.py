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
            lambda row: (row["Price"] * row["Quantity"])
            if row["Type"] == "buy"
            else (-row["Price"] * row["Quantity"]),
            axis=1,
        )
        pnl_series = portfolio_value.cumsum()
        return pnl_series

    def _update_realized_pnl(
        self, symbol, quantity, price, trade_type, transaction_cost
    ):
        if symbol not in self.positions:
            self.positions[symbol] = {"cost": 0, "quantity": 0}

        curr_cost, curr_quantity = (
            self.positions[symbol]["cost"],
            self.positions[symbol]["quantity"],
        )

        if trade_type == "buy":
            if curr_quantity < 0:
                # Selling short positions
                quantity_to_close = min(abs(curr_quantity), quantity)
                trade_pnl = quantity_to_close * (curr_cost - price)
                self.realized_pnl += trade_pnl

            # Adding to long position
            new_quantity = curr_quantity + quantity
            new_cost = (curr_quantity * curr_cost + quantity * price) / new_quantity
            self.positions[symbol] = {"quantity": new_quantity, "cost": new_cost}
        # elif trade_type == "sell":
        #     if curr_quantity > 0:
        #         # Selling long positions
        #         quantity_to_close = min((curr_quantity), quantity)
        #         trade_pnl = quantity_to_close * (price - curr_price)
        #         self.realized_pnl += trade_pnl
        #         self.positions[symbol] -= quantity_to_close

        #     # Adding to short position
        #     self.positions[symbol] -= quantity

        #     if positions[asset]["quantity"] > 0:
        #         # Closing long positions
        #         quantity_to_close = min(positions[asset]["quantity"], quantity)
        #         realized_pnl += quantity_to_close * (price - positions[asset]["price"])
        #         positions[asset]["quantity"] -= quantity_to_close

        #     # Adding to short position
        #     new_quantity = positions[asset]["quantity"] - quantity
        #     new_price = (
        #         (
        #             abs(positions[asset]["quantity"]) * positions[asset]["price"]
        #             + quantity * price
        #         )
        #         / abs(new_quantity)
        #         if new_quantity != 0
        #         else 0
        #     )
        #     positions[asset] = {"quantity": new_quantity, "price": new_price}

    def _update_unrealized_pnl(self):
        pass
