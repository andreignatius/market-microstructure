import tkinter as tk
from queue import Queue
from threading import Thread

from book_keeper.main import BookKeeper
from gateway.market_data_stream import MarketDataStream
from gateway.data_stream import DataStream
from gateway.main import TradeExecutor
from risk_manager.main import RiskManager
from trading_engine.main import TradingStrategy

# from training_engine.review_engine import ReviewEngine
import time
import random


class ExecManager:
    def __init__(self) -> None:
        self.queue = Queue()

        # probably pass a obj
        self.strategy = TradingStrategy(self.queue)

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

            print("CALL BOOK FUNCTION")
            print("CALL RISK FUNCTION")

            # this is to model risk liquidate
            random_number = random.randint(0, 10)
            print(random_number)
            if random_number == 0:
                print(f"we will be liquidating all {random_number}")
                print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
            else:
                self.updateQueue(s)
                self.strategy.collect_new_data()
                self.strategy.aggregate_data()  # Only aggregate data, do not collect here
                # if time_elapsed > 40:
                output = (
                    self.strategy.analyze_data()
                )  # analyse data and gather prediction
                print("model output: ", output)
                print("MODEL RISK CALL")
                approve_random_number = random.randint(0, 5)
                if approve_random_number == 0:
                    print(f"not approved, do not do anything{approve_random_number}")
                else:
                    print(f"TRADE APPROVED{approve_random_number}")


# create this app.py to serve as our actual strat file, the main.py is used by strategy already.
if __name__ == "__main__":
    print("LETS FUCKING GO")
    myExecManager = ExecManager()
    # get api key and secret
    # dotenv_path = '/vault/binance_keys'
    # load_dotenv(dotenv_path=dotenv_path)

    # os.getenv('BINANCE_API_KEY')

    # os.getenv('BINANCE_API_SECRET')

    # strategy parameters
    symbol = "BTCUSDT"
    api_key = ""
    api_secret = ""

    # create a binance gateway object
    myDataStream = DataStream(symbol, api_key, api_secret)

    # register callbacks
    myDataStream.register_tick_callback(myExecManager.execStrat)

    # start connection
    myDataStream.connect()

    while True:
        time.sleep(40)
        print("done wait")

    ## create a strategy a register callbacks with gateway
#
# strategy = PricingStrategy(symbol, order_size, sensitivity, binance_gateway)
# binance_gateway.register_execution_callback(strategy.on_execution)
# binance_gateway.register_depth_callback(strategy.on_orderbook)
#
## start
# binance_gateway.connect()
# strategy.start()
#
# while True:
#    time.sleep(2)
