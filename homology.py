import websocket
import json
import numpy as np
from ripser import Rips
import persim
import matplotlib.pyplot as plt
import warnings
import logging
import os
import time
import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)  # You can change the level to DEBUG, ERROR, WARNING, CRITICAL

warnings.filterwarnings("ignore")

WINDOW_SIZE = 500

# Data buffer for storing a sliding window of prices
class DataBuffer:
    def __init__(self, window_size=WINDOW_SIZE):
        self.window_size = window_size
        self.prices = []
        self.log_returns = []

    def update(self, price):
        if len(self.prices) >= self.window_size:
            self.prices.pop(0)
        self.prices.append(price)
        if len(self.prices) > 1:
            self.update_log_returns()

    # def update_log_returns(self):
    #     self.log_returns = np.log(np.divide(self.prices[1:], self.prices[:-1]))
    def update_log_returns(self):
        if len(self.prices) > 1:
            self.log_returns = np.log(np.divide(self.prices[1:], self.prices[:-1]))
            logging.info(f"Updated log returns: {self.log_returns}")
        else:
            logging.warning("Not enough prices to calculate log returns.")

    def get_log_returns(self):
        if len(self.log_returns) == 0:
            logging.warning("Attempt to access empty log returns.")
        return np.array(self.log_returns)

    def get_data_stream(self):
        return self.prices


def analyze_homology(data_stream, save_dir='plots'):
    if len(data_stream) >= WINDOW_SIZE:  # Ensure there's enough data
        # Convert price data to a distance matrix or other suitable format
        data_array = np.array(data_stream)
        distances = np.abs(data_array[:, None] - data_array[None, :])

        # Perform persistent homology analysis
        rips = Rips(maxdim=2, verbose=False)
        dgm = rips.fit_transform(distances)

        # Ensure directory exists
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        # Visualize and save results
        plt.figure()
        persim.plot_diagrams(dgm, show=False)  # Set show=False to prevent plotting window from opening
        plt.title("Real-time Persistent Homology")

        # Generate a filename based on current time or other unique identifier
        # filename = f"{save_dir}/homology_{int(time.time())}.png"
        timestamp = '_'.join(str(datetime.datetime.now()).split())
        filename = f"{save_dir}/homology_{timestamp}.png"
        print("check filename: ", filename)
        plt.savefig(filename)  # Save the figure
        plt.close()  # Close the figure to free up memory

        print(f"Saved plot to {filename}")

    else:
        print("Accumulating more data for analysis...")

# WebSocket Callback (make sure data handling is correct)
def on_message(ws, message):
    try:
        data = json.loads(message)
        if 'p' in data:
            price = float(data['p'])
            data_buffer.update(price)
            # log_returns = data_buffer.get_log_returns()
            data_stream = data_buffer.get_data_stream()
            logging.info(f"data buffer: {data_stream}")

            # Only call analyze_homology if there are enough log returns
            if len(data_stream) == WINDOW_SIZE:  # Adjust this number based on your analysis needs
                analyze_homology(data_stream)
            else:
                logging.info("Not enough data points for analysis")
        else:
            logging.error("Price field 'p' not found in the message.")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")


def on_open(ws):
    print("WebSocket opened")
    subscribe_message = {
        "method": "SUBSCRIBE",
        "params": ["btcusdt@trade"],
        "id": 1
    }
    ws.send(json.dumps(subscribe_message))

if __name__ == "__main__":
    data_buffer = DataBuffer(window_size=WINDOW_SIZE)
    
    # WebSocket setup
    ws = websocket.WebSocketApp("wss://stream.binance.com:9443/ws/btcusdt@trade",
                                on_message=on_message,
                                on_open=on_open)
    ws.run_forever()

    # rips = Rips(maxdim=2, verbose=False)  # Instantiate Rips without verbosity
    # logging.info("rips")
    # dgm = rips.fit_transform([1,2,3])
    # print("dgm: ", dgm)
