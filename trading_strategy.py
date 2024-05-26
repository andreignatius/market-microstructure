import numpy as np
from scipy.signal import find_peaks
from gtda.homology import VietorisRipsPersistence
from gtda.diagrams import BettiCurve
from gtda.time_series import SlidingWindow
import pandas as pd
import csv
import pywt
import joblib

import pandas as pd
from scipy.fft import fft
import numpy as np
from scipy.signal import find_peaks
from sklearn.preprocessing import StandardScaler
from pykalman import KalmanFilter

# import talib
from hurst import compute_Hc
from sklearn.utils import resample


class TradingStrategy:
    def __init__(self, queue):
        self.queue = queue
        self.data = pd.DataFrame(columns=["Timestamp", "Price"])
        self.peaks = []
        self.troughs = []
        self.smoothed_prices = []
        self.model = joblib.load("logistic_regression_model.pkl")

    def collect_new_data(self):
        new_rows = []
        while not self.queue.empty():
            data_point = self.queue.get()
            new_row = {"Timestamp": data_point[0], "Price": data_point[1]}
            new_rows.append(new_row)

        if new_rows:
            new_data = pd.DataFrame(new_rows)
            new_data["Timestamp"] = pd.to_datetime(new_data["Timestamp"])
            if not self.data.empty:
                self.data = pd.concat([self.data, new_data], ignore_index=True)
            else:
                self.data = new_data
            if "Timestamp" not in self.data.index.names:
                self.data.set_index("Timestamp", inplace=True, drop=False)
        return self.data

    # def smooth_with_wavelets(self, y):
    #     coeffs = pywt.wavedec(y, 'sym5', mode='symmetric')
    #     for i in range(5):
    #         coeffs[i + 5] = np.zeros(coeffs[i + 5].shape)
    #     y_rec = pywt.waverec(coeffs, 'sym5', mode='symmetric')[1:]
    #     return y_rec

    # def smooth_with_wavelets(self, y, wavelet='sym5', level=5):
    #     # Perform wavelet decomposition
    #     coeffs = pywt.wavedec(y, wavelet, mode='symmetric')

    #     # Ensure the level does not exceed the number of coefficient arrays
    #     num_coeffs = len(coeffs)
    #     if level >= num_coeffs:
    #         level = num_coeffs - 1

    #     # Zero out the specified number of detail coefficients
    #     for i in range(level, num_coeffs):
    #         coeffs[i] = np.zeros_like(coeffs[i])

    #     # Perform wavelet reconstruction
    #     y_rec = pywt.waverec(coeffs, wavelet, mode='symmetric')

    #     # Return the reconstructed signal, trimmed to match original length
    #     return y_rec[:len(y)]

    def smooth_with_wavelets(self, y, wavelet="sym5", level=5):
        # Perform wavelet decomposition
        coeffs = pywt.wavedec(y, wavelet, mode="symmetric")

        # Ensure the level does not exceed the number of coefficient arrays
        num_coeffs = len(coeffs)
        if level >= num_coeffs:
            level = num_coeffs - 1

        # Zero out the specified number of detail coefficients
        for i in range(level, num_coeffs):
            coeffs[i] = np.zeros_like(coeffs[i])

        # Perform wavelet reconstruction
        y_rec = pywt.waverec(coeffs, wavelet, mode="symmetric")

        # Return the reconstructed signal as a Series to maintain compatibility with pandas operations
        return pd.Series(y_rec[: len(y)], index=y.index)

    # feature_set = [
    #          # 'Short_Moving_Avg',
    #          # 'Short_Moving_Avg_1st_Deriv',
    #          'Short_Moving_Avg_2nd_Deriv',
    #          # 'Long_Moving_Avg',
    #          # 'Long_Moving_Avg_1st_Deriv',
    #          'Long_Moving_Avg_2nd_Deriv',
    #          'RSI',
    #          # 'Bollinger_PercentB',
    #          'MinutesSincePeak',
    #          'MinutesSinceTrough',
    #          'FourierSignalSell',
    #          'FourierSignalBuy',
    #          '%K',
    #          '%D',
    #          'Slow %K',
    #          'Slow %D',
    #          # 'KalmanFilterEst',
    #          'KalmanFilterEst_1st_Deriv',
    #          'KalmanFilterEst_2nd_Deriv',
    #          # 'HurstExponent',
    #          # 'Interest_Rate_Difference',
    #          # 'Interest_Rate_Difference_Change',
    #          # 'Currency_Account_difference'
    #         ]
    #     self.X_train = self.train_data[
    #         feature_set
    #     ]

    #     # ].iloc[:self.split_idx]
    #     self.X_test = self.test_data[
    #         feature_set
    #     ]

    def perform_fourier_transform_analysis(self):
        # Fourier Transform Analysis
        # close_prices = self.smoothed_prices.to_numpy()

        close_prices = self.smoothed_prices.to_numpy()
        # print("close_prices: ", close_prices)
        N = len(close_prices)
        T = 1.0  # 1 day
        close_fft = fft(close_prices)
        fft_freq = np.fft.fftfreq(N, T)
        positive_frequencies = fft_freq[: N // 2]
        positive_fft_values = 2.0 / N * np.abs(close_fft[0 : N // 2])
        amplitude_threshold = 0.1  # This can be adjusted
        significant_peaks, _ = find_peaks(
            positive_fft_values, height=amplitude_threshold
        )
        significant_frequencies = positive_frequencies[significant_peaks]
        significant_amplitudes = positive_fft_values[significant_peaks]
        days_per_cycle = 1 / significant_frequencies
        self.fft_features = pd.DataFrame(
            {
                "Frequency": significant_frequencies,
                "Amplitude": significant_amplitudes,
                "MinutesPerCycle": days_per_cycle,
            }
        )

    def detect_fourier_signals(self):
        # Add in fourier transform
        print("check fft_features: ", self.fft_features)
        dominant_period_lengths = sorted(
            set((self.fft_features.loc[:10, "MinutesPerCycle"].values / 2).astype(int)),
            reverse=True,
        )
        dominant_period_lengths = [i for i in dominant_period_lengths if i < 30]
        dominant_period_lengths = dominant_period_lengths[:5]
        print("check dominant_period_lengths: ", dominant_period_lengths)
        self.data["FourierSignalSell"] = self.data["MinutesSinceTrough"].isin(
            dominant_period_lengths
        )
        self.data["FourierSignalBuy"] = self.data["MinutesSincePeak"].isin(
            dominant_period_lengths
        )
        # self.data.at[index, 'DaysSincePeak'] = days_since_peak
        # self.data.at[index, 'DaysSinceTrough'] = days_since_bottom
        print("FourierSignalSell: ", self.data["FourierSignalSell"])
        print("FourierSignalBuy: ", self.data["FourierSignalBuy"])

    # def detect_rolling_peaks_and_troughs(self, window_size=5):
    #     print("checking self.data: ", self.data)
    #     # Initialize columns to store the results
    #     self.data['isLocalPeak'] = False
    #     self.data['isLocalTrough'] = False

    #     # Iterate through the DataFrame using a rolling window
    #     for end_idx in range(window_size, len(self.data)):
    #         start_idx = max(0, end_idx - window_size)

    #         # Subset the data for the current window
    #         window_data = self.smoothed_prices[start_idx:end_idx]

    #         # Find peaks
    #         peaks, _ = find_peaks(window_data)
    #         peaks_global_indices = [start_idx + p for p in peaks]
    #         # print("peaks: ", peaks)
    #         self.data.loc[peaks_global_indices, 'isLocalPeak'] = True

    #         # Find troughs by inverting the data
    #         troughs, _ = find_peaks(-window_data)
    #         troughs_global_indices = [start_idx + t for t in troughs]
    #         # print("troughs: ", troughs)
    #         self.data.loc[troughs_global_indices, 'isLocalTrough'] = True

    #     # Assign labels based on peaks and troughs
    #     self.data['Label'] = 'Hold'  # Default label
    #     self.data.loc[self.data['isLocalPeak'], 'Label'] = 'Sell'
    #     self.data.loc[self.data['isLocalTrough'], 'Label'] = 'Buy'

    def detect_rolling_peaks_and_troughs(self, window_size=5):
        # print("checking self.data: ", self.data)
        # Reset index to ensure numerical indexing works, save the old index if needed
        old_index = self.data.index
        self.data.reset_index(drop=True, inplace=True)

        # Initialize columns to store the results
        self.data["isLocalPeak"] = False
        self.data["isLocalTrough"] = False

        # Convert 'Price' column to a numpy array for processing
        prices = self.data["Price"].to_numpy()

        # Iterate through the DataFrame using a rolling window
        for end_idx in range(window_size, len(self.data)):
            start_idx = max(0, end_idx - window_size)

            # Subset the data for the current window
            window_data = prices[start_idx:end_idx]

            # Find peaks
            peaks, _ = find_peaks(window_data)
            peaks_global_indices = [start_idx + p for p in peaks]
            self.data.loc[peaks_global_indices, "isLocalPeak"] = True

            # Find troughs by inverting the data
            troughs, _ = find_peaks(-window_data)
            troughs_global_indices = [start_idx + t for t in troughs]
            self.data.loc[troughs_global_indices, "isLocalTrough"] = True

        # Optionally restore the original index if needed
        self.data.set_index(old_index, inplace=True)
        # Assign labels based on peaks and troughs
        self.data["Label"] = "Hold"  # Default label
        self.data.loc[self.data["isLocalPeak"], "Label"] = "Sell"
        self.data.loc[self.data["isLocalTrough"], "Label"] = "Buy"

    # Calculating Moving Averages and RSI manually
    def calculate_rsi(self, window=14):
        """Calculate the Relative Strength Index (RSI) for a given dataset and window"""
        delta = self.smoothed_prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_moving_averages_and_rsi(self):
        if self.data.index.duplicated().any():
            self.data.reset_index(drop=True, inplace=True)
        short_window = 5
        long_window = 20
        rsi_period = 14
        self.data["Short_Moving_Avg"] = self.smoothed_prices.rolling(
            window=short_window
        ).mean()
        self.data["Long_Moving_Avg"] = self.smoothed_prices.rolling(
            window=long_window
        ).mean()
        self.data["RSI"] = self.calculate_rsi(window=rsi_period)

    def calculate_days_since_peaks_and_troughs(self):
        self.data["MinutesSincePeak"] = 0
        self.data["MinutesSinceTrough"] = 0
        self.data["PriceChangeSincePeak"] = 0
        self.data["PriceChangeSinceTrough"] = 0

        checkpoint_date_bottom = None  # Initialize to a sensible default or first date
        checkpoint_date_top = None  # Initialize to a sensible default or first date
        checkpoint_price_bottom = None
        checkpoint_price_top = None
        price_change_since_bottom = 0
        price_change_since_peak = 0

        for index, row in self.data.iterrows():
            # print("rowwwww: ", row)
            current_price = row["Price"]
            today_date = pd.to_datetime(row["Timestamp"])

            if row["Label"] == "Buy":
                checkpoint_date_bottom = today_date
                checkpoint_price_bottom = current_price
            if row["Label"] == "Sell":
                checkpoint_date_top = today_date
                checkpoint_price_top = current_price

            days_since_bottom = (
                (today_date - checkpoint_date_bottom).days
                if checkpoint_date_bottom
                else 0
            )
            days_since_peak = (
                (today_date - checkpoint_date_top).days if checkpoint_date_top else 0
            )

            if checkpoint_price_bottom is not None:
                price_change_since_bottom = current_price - checkpoint_price_bottom
            if checkpoint_price_top is not None:
                price_change_since_peak = current_price - checkpoint_price_top

            # final_dataset_with_new_features.at[index, 'DaysSincePeakTrough'] = max(days_since_bottom, days_since_peak)
            self.data.at[index, "MinutesSincePeak"] = days_since_peak
            self.data.at[index, "MinutesSinceTrough"] = days_since_bottom
            # self.data.at[index, 'FourierSignalSell'] = ( (days_since_peak % 6 == 0) or (days_since_peak % 7 == 0) )
            # self.data.at[index, 'FourierSignalBuy'] = ( (days_since_bottom % 6 == 0) or (days_since_bottom % 7 == 0) )
            self.data.at[index, "PriceChangeSincePeak"] = price_change_since_peak
            self.data.at[index, "PriceChangeSinceTrough"] = price_change_since_bottom

    # def construct_kalman_filter(self):
    #     close_prices = self.smoothed_prices
    #     # Construct a Kalman Filter
    #     kf = KalmanFilter(initial_state_mean=0, n_dim_obs=1)

    #     # Use the observed data (close prices) to estimate the state
    #     state_means, _ = kf.filter(close_prices)

    #     # Convert state means to a Pandas Series for easy plotting
    #     kalman_estimates = pd.Series(
    #         state_means.flatten(), index=self.data.index)

    #     # Combine the original close prices and Kalman Filter estimates
    #     kalman_estimates = pd.DataFrame({
    #         'KalmanFilterEst': kalman_estimates
    #     })
    #     self.data = self.data.join(kalman_estimates)

    #     # print('KalmanFilterEst: ', self.data['KalmanFilterEst'])  # Display the first few rows of the dataframe

    # def construct_kalman_filter(self):
    #     close_prices = self.smoothed_prices

    #     # Assuming close_prices is a numpy array or a list; otherwise, convert appropriately
    #     if isinstance(close_prices, list):
    #         close_prices = np.array(close_prices)

    #     # Construct a Kalman Filter
    #     kf = KalmanFilter(initial_state_mean=0, n_dim_obs=1)

    #     # Use the observed data (close prices) to estimate the state
    #     state_means, _ = kf.filter(close_prices)

    #     # If you don't have timestamps or other index data, create a range index
    #     index = pd.RangeIndex(start=0, stop=len(state_means), step=1)

    #     # Convert state means to a Pandas DataFrame for easy handling or plotting
    #     kalman_estimates = pd.DataFrame({
    #         'KalmanFilterEst': state_means.flatten()
    #     }, index=index)

    #     self.data = self.data.join(kalman_estimates)

    # TODO fix
    def construct_kalman_filter(self):
        close_prices = self.smoothed_prices

        # Assuming close_prices is a numpy array or a list; otherwise, convert appropriately
        if isinstance(close_prices, list):
            close_prices = np.array(close_prices)

        # Construct a Kalman Filter
        kf = KalmanFilter(initial_state_mean=0, n_dim_obs=1)

        # Use the observed data (close prices) to estimate the state
        state_means, _ = kf.filter(close_prices)

        # Match the index with the main data if timestamps are needed
        if not self.data.empty:
            index = self.data.index
        else:
            index = pd.RangeIndex(start=0, stop=len(state_means), step=1)

        # Convert state means to a Pandas DataFrame for easy handling or plotting
        kalman_estimates = pd.DataFrame(
            {"KalmanFilterEst": state_means.flatten()}, index=index
        )

        self.data = self.data.join(kalman_estimates, how="outer")

    def calculate_first_second_order_derivatives(self):
        # Calculate first and second order derivatives for selected features
        # for feature in ['KalmanFilterEst', 'Short_Moving_Avg', 'Long_Moving_Avg']:
        for feature in ["Short_Moving_Avg", "Long_Moving_Avg"]:
            self.data[f"{feature}_1st_Deriv"] = self.data[feature].diff() * 100
            self.data[f"{feature}_2nd_Deriv"] = (
                self.data[f"{feature}_1st_Deriv"].diff() * 100
            )

        # Fill NaN values that were generated by diff()
        self.data.bfill(inplace=True)

    def analyze_data(self):
        # Ensure there's data to analyze
        if not self.data.empty:
            # Directly access the 'Timestamp' and 'Price' columns
            times = self.data["Timestamp"]
            prices = self.data["Price"]

            # Example analysis logic
            # Here you would perform your actual analysis, such as smoothing, peak detection, etc.
            # Update self.peaks and self.troughs as per the results of your analysis
            # For example:
            self.smoothed_prices = self.smooth_with_wavelets(prices)
            self.smoothed_prices = self.smoothed_prices[:100]
            print("smoothed_prices: ", self.smoothed_prices)
            self.perform_fourier_transform_analysis()
            self.detect_rolling_peaks_and_troughs()
            # times, prices = zip(*self.data)
            # times = [t.timestamp() for t in times]

            # # Smooth the price data
            # self.smoothed_prices = self.smooth_with_wavelets(prices)
            self.perform_fourier_transform_analysis()
            # self.construct_kalman_filter()
            self.detect_rolling_peaks_and_troughs()

            # self.calculate_moving_averages_and_rsi()

            # self.estimate_hurst_exponent()
            self.calculate_days_since_peaks_and_troughs()
            self.detect_fourier_signals()
            # self.calculate_first_second_order_derivatives()

            min_height = np.std(self.smoothed_prices)
            min_distance = 10
            prominence = min_height * 0.25

            peaks, _ = find_peaks(
                self.smoothed_prices, distance=min_distance, prominence=prominence
            )
            neg_prices = -np.array(self.smoothed_prices)
            troughs, _ = find_peaks(
                neg_prices, distance=min_distance, prominence=prominence
            )

            # self.peaks, self.troughs = peaks, troughs

        # feature_set = [
        #     peaks,
        #     troughs
        # ]
        # self.model.predict(feature_set)

        # return times, prices, peaks, troughs
        return times, self.smoothed_prices, peaks, troughs

    def reference_model(self):
        raw_data.to_csv("temp_data.csv")

        # Initialize and use the BaseModel for advanced analysis
        # model = BaseModel(file_path='temp_data.csv', train_start='2013-01-01', train_end='2018-01-01', test_start='2018-01-01', test_end='2023-01-01')
        model = LogRegModel(
            file_path="temp_data.csv",
            train_start="2013-01-01",
            train_end="2018-01-01",
            test_start="2018-01-01",
            test_end="2023-01-01",
        )
        model.load_preprocess_data()  # Load and preprocess the data
        model.train_test_split_time_series()  # Split data into training and testing
        model.train()  # Placeholder for training method

        data = model.retrieve_test_set()
