from threading import Thread
from queue import Queue
import tkinter as tk
from trading_engine.main import TradingStrategy
from gateway.market_data_stream import MarketDataStream
from visualization.live_plotter import LivePlotter
from book_keeper.main import BookKeeper
from gateway.main import TradeExecutor
from risk_manager.main import RiskManager
from training_engine.review_engine import ReviewEngine

if __name__ == "__main__":
    queue = Queue()
    strategy = TradingStrategy(queue)
    root = tk.Tk()
    plotter = LivePlotter(root, strategy)

    data_stream = MarketDataStream(queue)
    data_thread = Thread(target=data_stream.fetch_data, daemon=True)
    data_thread.start()

    # hypothetical usage of classes
    # book_keeper = BookKeeper()
    # trade_executor = TradeExecutor(book_keeper)
    # risk_manager = RiskManager(book_keeper)
    # review_engine = ReviewEngine(model)

    root.mainloop()
