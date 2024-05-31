import tkinter as tk
from queue import Queue
from threading import Thread

from book_keeper.main import BookKeeper
from gateway.market_data_stream import MarketDataStream
from gateway.data_stream import DataStream
from gateway.main import TradeExecutor
from risk_manager.main import RiskManager
from trading_engine.main import TradingStrategy
#from training_engine.review_engine import ReviewEngine
import schedule
import time


class ExecManager:
    def __init__(self) -> None:
        self.queue = Queue()

        #probably pass a obj
        self.strategy = TradingStrategy(self.queue)
        
    def updateQueue(self, s):
        output = (s["datetime"], s["lastprice"])
        print(f"test the callback {output}")
        self.queue.put(output)
    
    def execStrat(self,s):
        self.updateQueue(s)
        self.strategy.collect_new_data()
        self.strategy.aggregate_data()  # Only aggregate data, do not collect here    
        #if time_elapsed > 40:
        output = self.strategy.analyze_data() # analyse data and gather prediction
        print("model output: ", output)

def on_tick(s):
    return s

# create this app.py to serve as our actual strat file, the main.py is used by strategy already.
if __name__ == "__main__":
    print("LETS FUCKING GO")
    myExecManager = ExecManager()
        # get api key and secret
    #dotenv_path = '/vault/binance_keys'
    #load_dotenv(dotenv_path=dotenv_path)
     
    #os.getenv('BINANCE_API_KEY')

    #os.getenv('BINANCE_API_SECRET')

    # strategy parameters
    symbol = 'BTCUSDT'
    api_key =""
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
    #strategy = PricingStrategy(symbol, order_size, sensitivity, binance_gateway)
    #binance_gateway.register_execution_callback(strategy.on_execution)
    #binance_gateway.register_depth_callback(strategy.on_orderbook)
#
    ## start
    #binance_gateway.connect()
    #strategy.start()
#
    #while True:
    #    time.sleep(2)