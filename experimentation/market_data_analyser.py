import websocket
import json
import numpy as np
from scipy.signal import find_peaks
import time
from threading import Thread, Lock
import datetime

class MarketDataAnalyzer:
    def __init__(self):
        self.data = []  # Store tuples of (price, timestamp)
        self.lock = Lock()
    
    def add_data(self, price):
        with self.lock:
            # Append price along with the current timestamp
            self.data.append((price, datetime.datetime.now()))
    
    def analyze_data(self):
        while True:
            time.sleep(5)  # Time window for analysis
            with self.lock:
                if len(self.data) > 0:
                    # Unpack prices and timestamps into separate lists
                    prices, timestamps = zip(*self.data)
                    prices_array = np.array(prices)
                    
                    # Find local maxima and minima
                    peaks, _ = find_peaks(prices_array)
                    troughs, _ = find_peaks(-prices_array)

                    # Extract the corresponding timestamps for maxima and minima
                    # peak_points = [(prices_array[i], timestamps[i]) for i in peaks]
                    # trough_points = [(prices_array[i], timestamps[i]) for i in troughs]
                    peak_points = [(prices_array[i], timestamps[i].strftime('%d-%m-%y %H:%M:%S.%f')[:-3]) for i in peaks]
                    trough_points = [(prices_array[i], timestamps[i].strftime('%d-%m-%y %H:%M:%S.%f')[:-3]) for i in troughs]


                    print("Local Maxima:", peak_points)
                    print("Local Minima:", trough_points)
                    
                    # Clear the data after analysis
                    self.data = []

def on_message(ws, message):
    data = json.loads(message)
    if 'p' in data:
        price = float(data['p'])
        analyzer.add_data(price)

def on_error(ws, error):
    print("Error:", error)

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    params = {
        "method": "SUBSCRIBE",
        "params": [
            "btcusdt@trade"
        ],
        "id": 1
    }
    ws.send(json.dumps(params))

if __name__ == "__main__":
    websocket.enableTrace(False) # can set to True to have debug output of market data stream
    analyzer = MarketDataAnalyzer()
    ws = websocket.WebSocketApp("wss://stream.binance.com:9443/ws/btcusdt@trade",
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open
    
    # Start the analysis thread
    analysis_thread = Thread(target=analyzer.analyze_data)
    analysis_thread.start()

    # Start the websocket connection
    ws.run_forever()
