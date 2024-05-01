from threading import Thread
from queue import Queue
import tkinter as tk
from trading_strategy import TradingStrategy
from market_data_stream import MarketDataStream
from live_plotter import LivePlotter

if __name__ == "__main__":
    queue = Queue()
    strategy = TradingStrategy(queue)
    root = tk.Tk()
    plotter = LivePlotter(root, strategy)
    
    data_stream = MarketDataStream(queue)
    data_thread = Thread(target=data_stream.fetch_data, daemon=True)
    data_thread.start()

    root.mainloop()