import tkinter as tk
from queue import Queue
from threading import Thread
import os
from dotenv import load_dotenv

from book_keeper.main import BookKeeper
from gateway.data_stream import DataStream
from gateway.main import TradeExecutor
from risk_manager.main import RiskManager
from trading_engine.main import TradingStrategy
from training_engine.review_engine import ReviewEngine
from visualization.live_plotter import LivePlotter

if __name__ == "__main__":
    # get api key and secret
    load_dotenv()
    api_key = os.getenv('API_KEY')
    api_secret = os.getenv('API_SECRET')

    queue = Queue()
    strategy = TradingStrategy(queue)
    root = tk.Tk()
    plotter = LivePlotter(root, strategy)

    data_stream = MarketDataStream(queue)
    data_thread = Thread(target=data_stream.fetch_data, daemon=True)
    data_thread.start()

    # hypothetical usage of classes
    # book_keeper = BookKeeper()
    # trade_executor = TradeExecutor(book_keeper, api_key, api_secret)
    # risk_manager = RiskManager(book_keeper)
    # review_engine = ReviewEngine(model)

    root.mainloop()
