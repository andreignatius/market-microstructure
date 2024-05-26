import numpy as np
import pandas as pd
from gtda.diagrams import BettiCurve
from gtda.homology import VietorisRipsPersistence
from gtda.time_series import SlidingWindow
from scipy.signal import find_peaks


class HistoricalDataAnalyzer:
    def __init__(self, data_file):
        self.data = pd.read_csv(data_file)
        self.peaks = []
        self.troughs = []
        self.betti_curves_df = None
        self.persistence_norms_df = None

    def analyze_data(self):
        times = pd.to_datetime(self.data["Timestamp"])
        prices = self.data["Close"].values

        min_height = np.std(prices)
        min_distance = 10
        prominence = min_height * 0.25

        peaks, _ = find_peaks(prices, distance=min_distance, prominence=prominence)
        neg_prices = -np.array(prices)
        troughs, _ = find_peaks(
            neg_prices, distance=min_distance, prominence=prominence
        )

        self.peaks, self.troughs = peaks, troughs
        return times, prices, peaks, troughs

    def compute_betti_curves(self, window_size=10, max_dimension=2, n_bins=10):
        prices = self.data["Close"].values
        sliding_window = SlidingWindow(size=window_size, stride=1)
        windows = sliding_window.fit_transform(prices.reshape(-1, 1))

        VR_persistence = VietorisRipsPersistence(
            homology_dimensions=list(range(max_dimension + 1))
        )
        diagrams = VR_persistence.fit_transform(windows)

        betti_curves = BettiCurve(n_bins=n_bins)
        betti_curves_values = betti_curves.fit_transform(diagrams)

        self.betti_curves_df = pd.DataFrame(
            betti_curves_values.reshape(-1, max_dimension + 1),
            columns=[f"BettiCurve_{dim}" for dim in range(max_dimension + 1)],
        )
        return self.betti_curves_df

    def compute_persistence_norms(self):
        prices = self.data["Close"].values
        prices_reshaped = prices.reshape(1, -1, 1)

        VR_persistence = VietorisRipsPersistence(homology_dimensions=[0, 1])
        diagrams = VR_persistence.fit_transform(prices_reshaped)

        l1_norms = []
        l2_norms = []

        for dim in range(diagrams.shape[1]):
            lifetimes = diagrams[0, :, 1] - diagrams[0, :, 0]
            l1_norm = np.sum(np.abs(lifetimes))
            l2_norm = np.sqrt(np.sum(lifetimes**2))
            l1_norms.append(l1_norm)
            l2_norms.append(l2_norm)

        self.persistence_norms_df = pd.DataFrame(
            {"L1_Persistence": l1_norms, "L2_Persistence": l2_norms}
        )
        return self.persistence_norms_df

    def generate_labels(self, filename="inputs/historical_labels.csv"):
        times, prices, peaks, troughs = self.analyze_data()
        print("1")
        betti_curves_df = self.compute_betti_curves()
        print("2")
        # persistence_norms_df = self.compute_persistence_norms()
        # print("3")

        signals = []
        for i in range(len(prices)):
            if i in peaks:
                signals.append("Sell")
            elif i in troughs:
                signals.append("Buy")
            else:
                signals.append("Hold")

        # Ensure times are properly formatted
        times = [t.strftime("%Y-%m-%d %H:%M:%S") for t in times]

        # Create the labels dataframe
        labels_df = pd.DataFrame(
            {"Timestamp": times, "Price": prices, "Signal": signals}
        )

        # Ensure betti_curves_df and persistence_norms_df have the same length as labels_df
        betti_curves_df = betti_curves_df.reindex(labels_df.index, method="ffill")
        # persistence_norms_df = persistence_norms_df.reindex(labels_df.index, method='ffill')

        # Concatenate all dataframes
        # combined_df = pd.concat([labels_df, betti_curves_df, persistence_norms_df], axis=1)
        combined_df = pd.concat([labels_df, betti_curves_df], axis=1)

        # Save to CSV
        combined_df.to_csv(filename, index=False)
        return combined_df


if __name__ == "__main__":
    data_file = (
        "inputs/binance_btcusdt_1min_ccxt.csv"  # Replace with your historical data file
    )
    analyzer = HistoricalDataAnalyzer(data_file)
    combined_df = analyzer.generate_labels()
    print(f"Labels saved to historical_labels.csv")
