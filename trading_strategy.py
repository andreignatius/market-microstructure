import numpy as np
from scipy.signal import find_peaks
from gtda.homology import VietorisRipsPersistence
from gtda.diagrams import BettiCurve
from gtda.time_series import SlidingWindow
import pandas as pd
import csv

class TradingStrategy:
    def __init__(self, queue):
        self.queue = queue
        self.data = []
        self.peaks = []
        self.troughs = []

    def collect_new_data(self):
        new_data = []
        while not self.queue.empty():
            new_data.append(self.queue.get())
        self.data.extend(new_data)
        return new_data

    def analyze_data(self):
        times, prices = zip(*self.data)
        times = [t.timestamp() for t in times]

        min_height = np.std(prices)
        min_distance = 10
        prominence = min_height * 0.25

        peaks, _ = find_peaks(prices, distance=min_distance, prominence=prominence)
        neg_prices = -np.array(prices)
        troughs, _ = find_peaks(neg_prices, distance=min_distance, prominence=prominence)

        self.peaks, self.troughs = peaks, troughs
        return times, prices, peaks, troughs

    def compute_betti_curves(self, window_size=10, max_dimension=1, n_bins=10, filename='betti_curves.csv'):
        prices = np.array([price for _, price in self.data])
        sliding_window = SlidingWindow(size=window_size, stride=1)
        windows = sliding_window.fit_transform(prices.reshape(-1, 1))

        VR_persistence = VietorisRipsPersistence(homology_dimensions=list(range(max_dimension+1)))
        diagrams = VR_persistence.fit_transform(windows)

        betti_curves = BettiCurve(n_bins=n_bins)
        betti_curves_values = betti_curves.fit_transform(diagrams)

        betti_curve_df = pd.DataFrame(
            betti_curves_values.reshape(-1, max_dimension+1),
            columns=[f'BettiCurve_{dim}' for dim in range(max_dimension+1)]
        )

        betti_curve_df.to_csv(filename, index=False)
        return betti_curve_df

    def compute_persistence_norms(self, filename='persistence_norms.csv'):
        prices = np.array([price for _, price in self.data])
        prices_reshaped = prices.reshape(1, -1, 1)

        VR_persistence = VietorisRipsPersistence(homology_dimensions=[0, 1])
        diagrams = VR_persistence.fit_transform(prices_reshaped)

        l1_norms = []
        l2_norms = []

        for dim in range(diagrams.shape[1]):
            lifetimes = diagrams[0, :, 1] - diagrams[0, :, 0]
            l1_norm = np.sum(np.abs(lifetimes))
            l2_norm = np.sqrt(np.sum(lifetimes ** 2))
            l1_norms.append(l1_norm)
            l2_norms.append(l2_norm)

        norms_df = pd.DataFrame({
            'L1_Persistence': l1_norms,
            'L2_Persistence': l2_norms
        })

        norms_df.to_csv(filename, index=False)
        return norms_df

    def generate_signals(self, filename='signals.csv'):
        times, prices, peaks, troughs = self.analyze_data()
        betti_curves_df = self.compute_betti_curves()
        persistence_norms_df = self.compute_persistence_norms()

        signals = []
        for i in range(len(prices)):
            if i in peaks:
                signals.append('Sell')
            elif i in troughs:
                signals.append('Buy')
            else:
                signals.append('Hold')

        signal_df = pd.DataFrame({
            'Timestamp': times,
            'Price': prices,
            'Signal': signals
        })

        signal_df.to_csv(filename, index=False)
        return signals, betti_curves_df, persistence_norms_df
