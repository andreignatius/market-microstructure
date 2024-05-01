import websocket
import json
import numpy as np
import matplotlib.pyplot as plt
from scipy import sparse
from ripser import Rips
import persim
import logging
import os
import datetime
plt.rcParams['text.usetex'] = False
# Configure logging
logging.basicConfig(level=logging.INFO)

WINDOW_SIZE = 50
SAVE_DIR = 'plots'

class DataBuffer:
    def __init__(self, window_size=WINDOW_SIZE):
        self.window_size = window_size
        self.data = []

    def update(self, value):
        if len(self.data) >= self.window_size:
            self.data.pop(0)  # Remove the oldest element to make room for a new one
        self.data.append(value)

    def is_full(self):
        return len(self.data) == self.window_size

# def analyze_homology(data_stream):
#     if len(data_stream) >= WINDOW_SIZE:
#         # Convert price data to a distance matrix
#         data_array = np.array(data_stream)
#         distances = np.abs(data_array[:, None] - data_array[None, :])

#         # Perform persistent homology analysis
#         rips = Rips(maxdim=2, verbose=False)
#         diagrams = rips.fit_transform(distances, distance_matrix=True)

#         # Ensure the output directory exists
#         if not os.path.exists(SAVE_DIR):
#             os.makedirs(SAVE_DIR)
#         timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
#         filename = f"{SAVE_DIR}/homology_{timestamp}.png"
#         plt.figure()
#         persim.plot_diagrams(diagrams, show=False)
#         plt.savefig(filename)
#         plt.close()
#         logging.info(f"Saved plot to {filename}")
#     else:
#         logging.info("Accumulating more data for analysis...")

# Initialize a place to store persistence diagrams
previous_diagram = None
wasserstein_dists = []

def analyze_homology(data_stream, save_dir='wasserstein'):
    global previous_diagram
    rips = Rips(maxdim=2, verbose=False)
    data_array = np.array(data_stream)
    distances = np.abs(data_array[:, None] - data_array[None, :])
    # Compute persistence diagram
    diagram = rips.fit_transform(distances, distance_matrix=True)
    # Ensure directory exists
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    if previous_diagram is not None:
        # Compute Wasserstein distance between current and previous diagrams
        dist = persim.wasserstein(diagram[0], previous_diagram[0])
        wasserstein_dists.append(dist)
        logging.info(f"Wasserstein distance: {dist}")

        # Optionally, update a plot or save it
        plt.figure(figsize=(10, 4))
        plt.plot(wasserstein_dists)
        plt.title('Wasserstein Distances Over Time')
        plt.xlabel('Time Window Index')
        plt.ylabel('Distance')
        plt.grid(True)
        filename = f'{save_dir}/wasserstein_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.png'
        plt.savefig(filename)
        plt.close()
        logging.info(f"Saved plot to {filename}")

    # Update the previous diagram
    previous_diagram = diagram


def on_message(ws, message):
    data = json.loads(message)
    if 'p' in data:
        price = float(data['p'])
        data_buffer.update(price)

        if data_buffer.is_full():
            analyze_homology(data_buffer.data)

def on_open(ws):
    subscribe_message = {"method": "SUBSCRIBE", "params": ["btcusdt@trade"], "id": 1}
    ws.send(json.dumps(subscribe_message))
    logging.info("WebSocket subscription successful")

if __name__ == "__main__":
    data_buffer = DataBuffer()
    ws = websocket.WebSocketApp("wss://stream.binance.com:9443/ws/btcusdt@trade",
                                on_message=on_message, on_open=on_open)
    ws.run_forever()
