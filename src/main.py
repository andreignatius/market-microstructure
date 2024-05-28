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

# Main application loop
if __name__ == "__main__":
    queue = Queue()
    strategy = TradingStrategy(queue)
    data_stream = MarketDataStream(queue)

    # Start the data collection thread
    data_thread = Thread(target=data_stream.fetch_data, daemon=True)
    data_thread.start()

    def job():
        strategy.aggregate_data()  # Only aggregate data, do not collect here

    def job2():
        strategy.analyze_data() # analyse data and gather prediction

    # Schedule the job to aggregate data every minute
    # schedule.every().minute.at(":00").do(job)

    schedule.every().second.do(job)

    # 
    # schedule.every(20).minutes.do(job2)

    # Continuously collect data and analyze it
    while True:
        strategy.collect_new_data()  # Continuously collect data every cycle
        schedule.run_pending()
        time.sleep(1)  # Sleep briefly to avoid hogging CPU
        
# queue = Queue()
# strategy = TradingStrategy(queue)
# strategy.analyze_data()