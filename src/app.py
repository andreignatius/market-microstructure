import tkinter as tk
from queue import Queue
from threading import Thread

from book_keeper.main import BookKeeper
from gateway.market_data_stream import MarketDataStream
from gateway.data_stream import DataStream
from gateway.main import TradeExecutor
from risk_manager.main import RiskManager
from trading_engine.main import TradingStrategy
from datetime import datetime

# use this to create get requests
from rest_connect.rest_factory import *
from dotenv import load_dotenv
import os

# from training_engine.review_engine import ReviewEngine
import time
import random

# this is offset to timestamp, ensure it is in sync with server
offset = 15000
MAX_OPEN_ORDER_COUNT = 1
MAX_OPEN_ORDER_LIFE_SECONDS = 60
MAX_MODEL_NONE_COUNT = 20


global_time_elapsed = 0

class ExecManager:
    def __init__(
        self, tradeExecutorObj, bookKeeperObj, restGateway, riskManagerObj
    ) -> None:
        self.queue = Queue()
        self.tradeExecutor = tradeExecutorObj
        self.bookKeeper = bookKeeperObj
        self.riskManager = riskManagerObj
        self.restGateway = restGateway

        # probably pass a obj
        self.strategy = TradingStrategy(self.queue)
        self.tradeExecutor.connect()
        self.reattempt_liquidate = False

        # keep track of model none
        self.model_none_count = 0

    def updateQueue(self, s):
        output = (s["datetime"], s["lastprice"])
        print(f"test the callback {output}")
        self.queue.put(output)

    def execStrat(self, s):
        check = s["lastprice"]
        print(f"what is S even {check}")
        # what is S even {'lastprice': '', 'lastquantity': '', 'bestbidprice': '67150.00', 'bestbidquantity': '3.000', 'bestaskprice': '67430.90', 'bestaskquantity': '6.000', 'datetime': datetime.datetime(2024, 6, 1, 19, 13, 48, 104897)}

        if s["lastprice"] != "":
            """
            1. update book
            2. after book update, check with risk if need liquidate
            3. if risk_liquidate
                a. create liquidate order
                b. cancel standing order
            4. if no risk_liquidate
                a. call strategy to generate signal
                b. call risk to check order doable or not
                    i   ) Risk Metrics OK?
                    ii  ) Check if there is a pending order.
                    iii ) If have pending order, cancel the pending to replace with new order or?
            5. if risk say not doable, do nothing --> THIS ONE SHOULD CHECK ALSO IF THERE ARE ANY PENDING ORDERS
            6. if risk say doable --> send to trade executor
            """

            # 1. GET ENTER EXEC STRAT TIME
            response = self.restGateway.time()
            servertime = int(response["serverTime"])
            servertime_dt = datetime.fromtimestamp(servertime / 1000)
            the_date = servertime_dt.date()

            # 2. UPDATE THE BOOK KEEPER
            self.bookKeeper.update_bookkeeper(the_date, check, servertime)

            # 3. CHECK ANY OLDER ORDERS NEED TO CANCEL OR NOT
            # regardless of signal, check if there is any super old unfilled orders
            print(
                "XXXXXXXXXXXXXXXXXX   FIRST, LET US CHECK POSITION    XXXXXXXXXXXXXXXXXX"
            )
            current_open_orders = self.restGateway.get_all_open_orders(
                "BTCUSDT", servertime
            )
            print(current_open_orders)
            order_queue_ok = True
            if len(current_open_orders) >= MAX_OPEN_ORDER_COUNT:
                # see if we can cancel
                for x in current_open_orders:
                    servertime_dt = datetime.fromtimestamp(servertime / 1000)
                    x_dt = datetime.fromtimestamp(x["time"] / 1000)
                    timediff = servertime_dt - x_dt
                    timediff_seconds = timediff.total_seconds()
                    print(f"the time diff is {timediff_seconds}")

                    if timediff_seconds > MAX_OPEN_ORDER_LIFE_SECONDS:
                        print("CANCELLING ORDERS")
                        self.restGateway.cancel_order(
                            "BTCUSDT", servertime, x["orderId"]
                        )
                        order_queue_ok = True
                    else:
                        print("NO CANCELLABLE ORDERS")
                        order_queue_ok = False
            else:
                order_queue_ok = True

            # 4. LIQUIDATE CHECK
            stop_loss_trigger = self.riskManager.trigger_stop_loss()
            trading_halt_trigger = self.riskManager.trigger_trading_halt()
            print(
                f"stop_loss_trig {stop_loss_trigger} ; trading_halt_trig {trading_halt_trigger}"
            )
            liquidate_approval = stop_loss_trigger or trading_halt_trigger

            print(
                f"LIQUIDATE CHECK : {liquidate_approval} OR {self.reattempt_liquidate}"
            )
            # if we get approval to liquidate i.e. stoploss triggered
            if liquidate_approval or self.reattempt_liquidate:
                current_position_resp = self.restGateway.get_position_info(
                    "BTCUSDT", servertime
                )
                print(f"we will be liquidating all")
                # response = self.restGateway.time()
                if response != None:
                    # clear the reattempt liquidate flag
                    self.reattempt_liquidate = False

                    servertime = int(response["serverTime"])
                    # 1. CANCEL ALL STANDING ORDERS
                    cancel_resp = self.restGateway.cancel_all_order(
                        "BTCUSDT", servertime
                    )
                    print(cancel_resp)

                    # 2. CLOSE ALL POSITIONS
                    current_position_resp = self.restGateway.get_position_info(
                        "BTCUSDT", servertime
                    )
                    if current_position_resp != None:
                        position_amt = float(current_position_resp[0]["positionAmt"])
                        if position_amt > 0:
                            liquidate_data = {
                                "symbol": "BTCUSDT",
                                "side": "SELL",
                                "type": "MARKET",
                                "quantity": position_amt,
                                "timestamp": servertime - offset,
                                "recvWindow": 60000,
                            }
                            print(liquidate_data)
                            self.tradeExecutor.execute_trade(liquidate_data, "trade")
                            print(
                                "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                            )
                        else:
                            print("NO POSITION TO LIQUIDATE")
                            print(
                                "xxxxxxxxxxxxxxxxxxxxxxxxx NO POSITION TO LIQUIDATE xxxxxxxxxxxxxxxxxxxxxxxxx"
                            )
                else:
                    print("cannot get response from server !")
                    self.reattempt_liquidate = True

            # 5. PROCEED AS NORMAL IF NOT LIQUIDATED
            else:
                self.updateQueue(s)
                self.strategy.collect_new_data()
                self.strategy.aggregate_data()  # Only aggregate data, do not collect here
                # if time_elapsed > 40:
                if global_time_elapsed % 60 == 1:
                    return
                print("***checking model output***")
                output = (
                    self.strategy.analyze_data()
                )  # analyse data and gather prediction
                print("model output: ", output)
                if output != None:
                    # create the order
                    direction = output[0].upper()
                    limit_price = float(output[1])

                    # USE THIS TO FORCE IF NEEDED
                    # final_check_price = float(
                    #    self.restGateway.get_price_ticker("BTCUSDT")["price"]
                    # )
                    # randomnumber = random.randint(0, 6)
                    # if randomnumber > 2:
                    #    direction = "SELL"
                    # else:
                    #    direction = "BUY"
                    # limit_price = final_check_price

                    # get our gateway time before send order
                    response = self.restGateway.time()
                    servertime = int(response["serverTime"])

                    if response != None:
                        order_quantity = 0

                        if direction == "BUY":
                            dollar_amt_buy = (
                                self.riskManager.get_available_tradable_balance()
                            )  # get dollar amount we can use to buy
                            order_quantity = round(
                                dollar_amt_buy / limit_price, 3
                            )  # convert this to quantity based on limit price
                            buy_balance_check = (
                                self.riskManager.check_available_balance(dollar_amt_buy)
                            )  # get approval from balance checking
                            buy_price_check = self.riskManager.check_buy_order_value(
                                limit_price
                            )  # get approval from buy price checking
                            buy_position_check = (
                                self.riskManager.check_buy_position()
                            )  # get approval from position checking
                            print(
                                f"buy_balance_check: {buy_balance_check} ,buy_price_check : {buy_price_check}, buy_position_check{buy_position_check}"
                            )
                            approval = (
                                buy_balance_check
                                and buy_price_check
                                and buy_position_check
                            )

                        elif direction == "SELL":
                            current_position_resp = self.restGateway.get_position_info(
                                "BTCUSDT", servertime
                            )
                            order_quantity = float(
                                current_position_resp[0]["positionAmt"]
                            )  # get current position, this will be our order quantity

                            short_pos_check = self.riskManager.check_short_position(
                                order_quantity
                            )  # get approval by checking if we are shorting
                            sell_price_check = self.riskManager.check_sell_order_value(
                                limit_price
                            )  # get approval from sell price checking
                            sell_position_check = (
                                self.riskManager.check_sell_position()
                            )  # get approval from position checking
                            print(
                                f"short pos check: {short_pos_check} , sell_price_check : {sell_price_check}, sell_position_check:{sell_position_check}"
                            )
                            approval = short_pos_check and sell_price_check
                        elif direction == "HOLD":
                            approval = 0
                            print("MODEL SIGNALS HOLD")
                        else:
                            approval = 0
                            print("invalid direction")

                        print(
                            f" {direction} --> ORDER QUANTITY {order_quantity}, approved ? {approval} and order queue {order_queue_ok}"
                        )

                        if approval and order_queue_ok:
                            # THIS IS TERRIBLE BTW
                            print(f"what is current {direction} : {order_quantity}")
                            if len(current_open_orders) < MAX_OPEN_ORDER_COUNT:
                                self.model_none_count = 0
                                data = {
                                    "symbol": "BTCUSDT",
                                    "price": limit_price,
                                    "side": direction,
                                    "type": "LIMIT",
                                    "quantity": order_quantity,
                                    "timestamp": servertime - offset,
                                    "recvWindow": 60000,
                                    "timeinforce": "GTC",
                                }
                                print(data)
                                self.tradeExecutor.execute_trade(data, "trade")
                                print("my limit price: ", limit_price)
                                self.bookKeeper.update_bookkeeper(
                                    datetime.now(), limit_price, servertime
                                )
                                get_pnl = self.bookKeeper.return_historical_data()
                                print(
                                    f"check historical position : {self.bookKeeper.historical_positions.tail(3)}"
                                )
                                get_pnl.to_csv("historical_data.csv")
                        else:
                            print("SORRY CANT TRADE")
                else:
                    print("MODEL SAYS NOTHING")
                    self.model_none_count = self.model_none_count + 1
                    if self.model_none_count >= MAX_MODEL_NONE_COUNT:
                        print("possible model error? Cancel All orders")
                        cancel_resp = self.restGateway.cancel_all_order(
                            "BTCUSDT", servertime
                        )
                        print(f"CANCEL MODEL NONE: {cancel_resp}")
                    print(f"MODEL NONE COUNT VALUE = {self.model_none_count}")


def on_exec():
    print("Lorem ipsum dolor sit amet, consectetur adipiscing elit.")


# create this app.py to serve as our actual strat file, the main.py is used by strategy already.
if __name__ == "__main__":
    load_dotenv(dotenv_path=".env")
    API_KEY = os.getenv("API_KEY")
    API_SECRET = os.getenv("API_SECRET")
    # program begins
    print("PROGRAM BEGINS")

    # 1. symbol and API key. someone can help the getenv thing pls
    symbol = "BTCUSDT"
    api_key = API_KEY
    api_secret = API_SECRET

    # print("1api_key: ", api_key)
    # print("1api_secret: ", api_secret)

    # 2. create a rest api caller object for rest requests. I only use this to get server time
    my_restfactory = RestFactory()
    futuretestnet_base_url = "https://testnet.binancefuture.com"
    # 2a. in our case its this
    futuretestnet_gateway = my_restfactory.create_gateway(
        "BINANCE_TESTNET_FUTURE",
        futuretestnet_base_url,
        api_key,
        api_secret,
    )
    print(api_key)
    # 3. create EdJacob trade executor object. Will call the TradeExecutor.connect in the Exec Manager constructor
    print("instantiate trade executor")
    myTradeExecutor = TradeExecutor(symbol, api_key, api_secret)
    myTradeExecutor.register_exec_callback(
        on_exec
    )  # this is dummy it is literally just a lorem ipsum

    myBookKeeper = BookKeeper("BTCUSDT", api_key, api_secret)
    myRiskManager = RiskManager(myBookKeeper)

    # 4. create the Execution Manager.
    # Impl wise can be cleaner, but for now pass the rest request caller and EdJacob trade executor
    myExecManager = ExecManager(
        myTradeExecutor, myBookKeeper, futuretestnet_gateway, myRiskManager
    )

    # 5. create the Datastream object, this is to stream data
    myDataStream = DataStream(symbol, api_key, api_secret)

    # 6. register the trading strategy itself as a callback for data stream
    # essentially its saying if there is new data, run the strategy
    # room for improvement probably pass the TradingStrategy as an object. At the moment the proj supports Andre's trading strategy object
    myDataStream.register_tick_callback(myExecManager.execStrat)

    # 7. start connection data stream
    myDataStream.connect()

    # 8. I think this is just for looping.
    while True:
        time.sleep(1)
        global_time_elapsed +=1
        print("global_time_elapsed: ", global_time_elapsed)
        print("done wait")
