import numpy as np
from scipy.signal import find_peaks

class TradingStrategy:
    '''
    - assume you can buy the ask price and sell the bid price on demand
    - will be in charge of producing buy / sell / hold signals of a security
    - for UAT / backtesting, we assume we buy / sell on demand at market price to observe behaviour for backtesting
    - BookKeeper will calculate MTM / PnL accordingly
    - work with websocket market data to compute all technical indicators realtime and make a call when to buy or sell a security
    - produces signals to TradeExecutor
    '''

    def __init__(self, queue):
        self.queue = queue
        self.data = []
        self.peaks = []
        self.troughs = []

    def collect_new_data(self):
        new_data = []
        while not self.queue.empty():
            new_data.append(self.queue.get())
        return new_data

    def analyze_data(self):
        times, prices = zip(*self.data)
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

        self.peaks, self.troughs = peaks, troughs
        return times, prices, peaks, troughs
