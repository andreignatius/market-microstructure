import websocket
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from scipy.signal import find_peaks
import datetime
from threading import Thread
from queue import Queue
import tkinter as tk
import time

# Setup the queue outside to ensure it can be accessed by different components
data_queue = Queue()

def fetch_data():
    """WebSocket communication in the background thread."""
    def on_message(ws, message):
        data = json.loads(message)
        if 'p' in data:
            price = float(data['p'])
            timestamp = datetime.datetime.now()
            data_queue.put((timestamp, price))
    
    def on_open(ws):
        params = {"method": "SUBSCRIBE", "params": ["btcusdt@trade"], "id": 1}
        ws.send(json.dumps(params))
    
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://stream.binance.com:9443/ws/btcusdt@trade",
                                on_message=on_message,
                                on_open=on_open)
    ws.run_forever()

class LivePlotter:
    def __init__(self, master):
        self.master = master
        self.fig, self.ax = plt.subplots()
        self.line, = self.ax.plot([], [], 'b-', label='BTC Price')
        self.peaks_plot, = self.ax.plot([], [], 'r^', label='Peaks')
        self.troughs_plot, = self.ax.plot([], [], 'gv', label='Troughs')
        self.ax.legend()
        self.ax.grid(True)
        plt.xlabel('Time')
        plt.ylabel('Price')
        self.last_update_time = time.time()
        self.ani = FuncAnimation(self.fig, self.update_plot, interval=1000)
        
        # Setup the button to start plotting
        self.plot_button = tk.Button(master, text="Start Plotting", command=self.run_plot)
        self.plot_button.pack()

    def update_plot(self, frame):
        current_time = time.time()
        if current_time - self.last_update_time >= 20:
            new_data = []
            while not data_queue.empty():
                new_data.append(data_queue.get())

            if new_data:
                times, prices = zip(*new_data)
                times = [t.timestamp() for t in times]  # Convert datetime to timestamp for plotting
                self.line.set_data(times, prices)
                
                # # Detect peaks
                # peaks, _ = find_peaks(prices)
                # troughs, _ = find_peaks(-np.array(prices))

                # Calculate parameters based on price fluctuations
                min_height = np.std(prices)  # Minimum height based on standard deviation of prices
                min_distance = 10  # Minimum samples between peaks or troughs
                prominence = min_height * 0.25  # Adjust prominence to be 25% of the standard deviation

                # Detect peaks with refined parameters
                peaks, _ = find_peaks(prices, distance=min_distance, prominence=prominence)

                # Detect troughs - Note that 'height' should be negative for the inverted prices
                neg_prices = -np.array(prices)
                troughs, _ = find_peaks(neg_prices, distance=min_distance, prominence=prominence)
            
                
                # Update peaks and troughs on plot
                self.peaks_plot.set_data([times[p] for p in peaks], [prices[p] for p in peaks])
                self.troughs_plot.set_data([times[t] for t in troughs], [prices[t] for t in troughs])

                self.ax.relim()
                self.ax.autoscale_view()
                self.last_update_time = current_time  # Reset the timer

        return self.line, self.peaks_plot, self.troughs_plot

    def run_plot(self):
        plt.show()

if __name__ == "__main__":
    root = tk.Tk()
    plotter = LivePlotter(root)
    # Start data fetching in a separate thread
    Thread(target=fetch_data, daemon=True).start()
    root.mainloop()
