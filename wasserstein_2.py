import websocket
import json
import numpy as np
import matplotlib.pyplot as plt
from ripser import Rips
import persim
import logging
import os
import datetime

# Setup basic configuration for logging
logging.basicConfig(level=logging.INFO)

# Define window size and the directory for saving plots
WINDOW_SIZE = 200
SAVE_DIR = 'wasserstein'

class DataBuffer:
    def __init__(self, window_size=WINDOW_SIZE):
        self.window_size = window_size
        self.data = []
        self.prices = []  # Store prices for plotting

    def update(self, value):
        if len(self.data) >= self.window_size:
            self.data.pop(0)  # Remove oldest data point
            self.prices.pop(0)  # Remove oldest price
        self.data.append(value[0])  # Assuming value contains distance data
        self.prices.append(value[1])  # Assuming value contains price data

    def is_full(self):
        return len(self.data) == self.window_size

# Initialize a place to store persistence diagrams
previous_diagram = None
wasserstein_dists = []
timestamps = []

def analyze_homology(data_buffer):
    global previous_diagram

    if data_buffer.is_full():
        # Convert data to a suitable format for persistence analysis
        data_array = np.array(data_buffer.data)
        distances = np.abs(data_array[:, None] - data_array[None, :])

        # Perform persistent homology analysis
        rips = Rips(maxdim=2, verbose=False)
        diagram = rips.fit_transform(distances, distance_matrix=True)

        # Setup the plot with specified subplot configuration
        fig, axs = plt.subplots(2, 2, figsize=(12, 10))  # Creates a 2x2 grid of subplots
        axs[1, 1].axis('off')  # Disable the bottom left subplot

        # Plot the persistence diagram in the top left
        ax1 = axs[0, 0]
        persim.plot_diagrams(diagram, ax=ax1, show=False)
        ax1.set_title('Persistence Diagram')

        # Plot the price data in the top right
        ax2 = axs[0, 1]
        ax2.plot(data_buffer.prices)
        ax2.set_title('Binance Price Data')
        ax2.set_xlabel('Time')
        ax2.set_ylabel('Price')

        if previous_diagram is not None:
            # Compute Wasserstein distance between current and previous diagrams
            dist = persim.wasserstein(diagram[0], previous_diagram[0])
            wasserstein_dists.append(dist)
            timestamps.append(datetime.datetime.now())  # Storing timestamps for each analysis

            # Plot Wasserstein distances over time in the bottom right
            ax3 = axs[1, 0]
            ax3.plot(timestamps, wasserstein_dists)
            ax3.set_title('Wasserstein Distances Over Time')
            ax3.set_xlabel('Time')
            ax3.set_ylabel('Distance')
            ax3.grid(True)

        # Save or show the plot
        if not os.path.exists(SAVE_DIR):
            os.makedirs(SAVE_DIR)
        filename = f"{SAVE_DIR}/combined_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        plt.savefig(filename)
        plt.close()
        logging.info(f"Saved combined plot to {filename}")

        # Update the previous diagram
        previous_diagram = diagram
    else:
        logging.info("Accumulating more data for analysis...")

def on_message(ws, message):
    try:
        data = json.loads(message)
        if 'p' in data:
            price = float(data['p'])
            # Example of updating buffer with both distance and price
            data_buffer.update((np.random.rand(), price))  # Simulate distance data for example
            analyze_homology(data_buffer)
    except Exception as e:
        logging.error(f"Error processing message: {e}")

def on_open(ws):
    subscribe_message = {"method": "SUBSCRIBE", "params": ["btcusdt@trade"], "id": 1}
    ws.send(json.dumps(subscribe_message))
    logging.info("WebSocket subscription successful")

if __name__ == "__main__":
    data_buffer = DataBuffer()
    ws = websocket.WebSocketApp("wss://stream.binance.com:9443/ws/btcusdt@trade",
                                on_message=on_message, on_open=on_open)
    ws.run_forever()
