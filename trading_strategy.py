import numpy as np
from scipy.signal import find_peaks

class TradingStrategy:
    def __init__(self, queue):
        self.queue = queue
        self.data = []

    def analyze_data(self):
        new_data = []
        while not self.queue.empty():
            new_data.append(self.queue.get())

        if new_data:
            times, prices = zip(*new_data)
            times = [t.timestamp() for t in times]  # Convert datetime to timestamp for plotting

            # Calculate parameters based on price fluctuations
            min_height = np.std(prices)  # Minimum height based on standard deviation of prices
            min_distance = 10  # Minimum samples between peaks or troughs
            prominence = min_height * 0.25  # Adjust prominence to be 25% of the standard deviation

            # Detect peaks with refined parameters
            peaks, _ = find_peaks(prices, distance=min_distance, prominence=prominence)

            # Detect troughs - Note that 'height' should be negative for the inverted prices
            neg_prices = -np.array(prices)
            troughs, _ = find_peaks(neg_prices, distance=min_distance, prominence=prominence)

            return times, prices, peaks, troughs
        return [], [], [], []