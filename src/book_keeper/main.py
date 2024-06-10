import pandas as pd
import time
from urllib.parse import urlencode
import hmac
import hashlib
import requests


class BookKeeper:
    """
    This class stores all executed trades and provides analyses based on executed trades.
    """

    def __init__(self, symbol, initial_cash, api_key, api_secret):
        # Base URLs
        self.BASE_URL = "https://testnet.binancefuture.com"  # hardcoded
        self.api_key = api_key
        self.api_secret = api_secret
        self.symbol = symbol
        self.initial_cash = initial_cash
        self.market_prices = pd.DataFrame(columns=["Date", "Symbol", "Price"])

        self.historical_data = pd.DataFrame(
            columns=[
                "Timestamp",
                "WalletBalance",
                "RealizedProfit",
                "UnrealizedProfit",
            ]
        )

        self.historical_positions = pd.DataFrame(
            columns=[
                "Timestamp",
                "Symbol",
                "EntryPrice",
                "PositionAmt",
            ]
        )

        self.market_prices = pd.DataFrame(columns=["Date", "Symbol", "Price"])

    @property
    def get_initial_cash(self):
        return self.initial_cash

    @property
    def get_unrealized_pnl(self):

        # Return last record in self.historical_position

        return self.historical_data["UnrealizedProfit"].iloc[-1]

    @property
    def get_realized_pnl(self):

        # Return last record in self.historical_position
        return self.historical_data["RealizedProfit"].iloc[-1]

    def update_bookkeeper(self, date, timestamp, middle_price):
        print("*************I AM CALLING UPDATE BOOK KEEPER*************")
        # 1. Append date and middle_price to df market prices
        # 2. Make API call to get realised and unrealised price, and positions
        # 3. Update historical_data, historical_positions
        # 4. Trim data
        params = {"timestamp": timestamp}

        query_string = urlencode(params)

        # signature
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # url
        url = (
            self.BASE_URL
            + "/fapi/v2/account"
            + "?"
            + query_string
            + "&signature="
            + signature
        )

        # post request
        session = requests.Session()
        session.headers.update(
            {
                "Content-Type": "application/json;charset=utf-8",
                "X-MBX-APIKEY": self.api_key,
            }
        )
        response = session.get(url=url, params={})

        # get order id
        response_map = response.json()

        # trim df if needed
        if self.historical_data.shape[0] == 86400:
            self.market_prices = self.market_prices.iloc[1:, :]
            self.historical_data = self.historical_data.iloc[1:, :]
            self.historical_positions = self.historical_positions.iloc[1:, :]

        # update market price df
        temp = pd.Series(
            data=[date, self.symbol, middle_price], index=["Date", "Symbol", "Price"]
        )
        self.market_prices = pd.concat(
            [self.market_prices, temp.to_frame().T], ignore_index=True
        )

        # update hist data df
        temp = pd.Series(
            data=[
                pd.to_datetime(int(time.time() * 1000), unit="ns"),
                float(response_map["totalWalletBalance"]),
                float(response_map["totalWalletBalance"]) - float(self.initial_cash),
                float(response_map["totalUnrealizedProfit"]),
            ],
            index=["Timestamp", "WalletBalance", "RealizedProfit", "UnrealizedProfit"],
        )

        self.historical_data = pd.concat(
            [self.historical_data, temp.to_frame().T], ignore_index=True
        )

        # update historical position df
        temp = pd.DataFrame(response_map["positions"])
        temp = temp[(temp["symbol"] == self.symbol)]

        temp = pd.Series(
            data=[
                pd.to_datetime(int(time.time() * 1000), unit="ns"),
                self.symbol,
                float(temp["entryPrice"]),
                float(temp["positionAmt"]),
            ],
            index=["Timestamp", "Symbol", "EntryPrice", "PositionAmt"],
        )

        self.historical_positions = pd.concat(
            [self.historical_positions, temp.to_frame().T], ignore_index=True
        )
        print("*************I AM DONE WITH UPDATE BOOK KEEPER*************")

    def calculate_max_drawdown(self):

        roll_max = self.historical_data["WalletBalance"].cummax()
        max_daily_drawdown = (
            self.historical_data["WalletBalance"] / roll_max - 1.0
        ).cummin()

        return max_daily_drawdown.iloc[-1]

    def calculate_sharpe_ratio(self, risk_free_rate=0):

        sharpe = (
            self.historical_data["WalletBalance"].pct_change().dropna().mean()
            / self.historical_data["WalletBalance"].pct_change().dropna().std()
        )

        return sharpe

    def calculate_vol(self):
        return self.market_prices["Price"].dropna().std()

    def return_historical_data(self):
        return self.historical_data

    def return_historical_market_prices(self):
        return self.market_prices

    def return_historical_positions(self):
        print(self.historical_positions)
        return self.historical_positions
