import csv

import joblib
import numpy as np
import pandas as pd
import pywt
from gtda.diagrams import BettiCurve
from gtda.homology import VietorisRipsPersistence
from gtda.time_series import SlidingWindow

# import talib
from hurst import compute_Hc
from pykalman import KalmanFilter
from scipy.fft import fft
from scipy.signal import find_peaks
from sklearn.preprocessing import StandardScaler
from sklearn.utils import resample

import os


class TradingStrategy:
    def __init__(self, queue):
        self.queue = queue
        self.data = pd.DataFrame(columns=["Timestamp", "Price"])
        self.file_path = "ohlc_minutes_new.csv"
        self.peaks = []
        self.troughs = []
        self.smoothed_prices = []
        self.model = joblib.load(
            "training_engine/outputs/logistic_regression_model.pkl"
        )

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
        print("self.data111: ", self.data.head())
        print("len: ", len(self.data))
        return self.data

    def aggregate_data(self):
        if self.data.empty:
            return

        if 'Timestamp' not in self.data.index.names:
            self.data.set_index('Timestamp', inplace=True)

        # Resample the data by minute and compute OHLC
        ohlc = self.data['Price'].resample('T').ohlc()

        # Capitalize the column headers
        ohlc.columns = [col.capitalize() for col in ohlc.columns]

        # # Check if file exists to handle headers
        # file_exists = os.path.exists('ohlc_minutes_new.csv')

        # # Append or update the CSV file instead of rewriting it entirely
        # ohlc.to_csv('ohlc_minutes.csv', mode='a', header=not file_exists)
        ohlc.to_csv('ohlc_minutes_new.csv')

        # Display the resulting OHLC values
        print("OHLC data: ", ohlc)


    def analyze_data(self):
        self.data = pd.read_csv(self.file_path)
        self.data["Date"] = pd.to_datetime(self.data["Timestamp"])
        self.data.bfill(inplace=True)
        self.calculate_daily_percentage_change()

        self.perform_fourier_transform_analysis()
        self.calculate_stochastic_oscillator()
        self.calculate_slow_stochastic_oscillator()
        self.construct_kalman_filter()
        self.detect_rolling_peaks_and_troughs()

        self.calculate_moving_averages_and_rsi()

        # self.estimate_hurst_exponent()
        self.calculate_days_since_peaks_and_troughs()
        self.detect_fourier_signals()
        self.calculate_first_second_order_derivatives()

        # self.preprocess_data()
        self.predict()

    def calculate_daily_percentage_change(self):
        self.data["Daily_Change"] = self.data["Close"].pct_change() * 100
        self.data["Daily_Change_Open_to_Close"] = (
            (self.data["Open"] - self.data["Close"].shift(1))
            / self.data["Close"].shift(1)
        ) * 100

    def perform_fourier_transform_analysis(self):
        # Fourier Transform Analysis
        # close_prices = self.data['Close'].to_numpy()
        # print("check000: ", type(self.train_end - pd.DateOffset(months=12)))
        # print("check111: ", type(self.train_end))
        # print("check222: ", self.data["Date"])
        # d1 = self.train_end - pd.DateOffset(days=14)
        # d2 = self.train_end

        # data_window = self.data[
        #     (self.data["Date"] >= d1) & (self.data["Date"] < d2)
        # ].copy()
        # print("data_window: ", data_window)
        data_window = self.data

        close_prices = data_window["Close"].to_numpy()
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

    def calculate_stochastic_oscillator(self, k_window=14, d_window=3, slow_k_window=3):
        """
        Calculate the Stochastic Oscillator.
        %K = (Current Close - Lowest Low)/(Highest High - Lowest Low) * 100
        %D = 3-day SMA of %K

        Where:
        - Lowest Low = lowest low for the look-back period
        - Highest High = highest high for the look-back period
        - %K is multiplied by 100 to move the decimal point two places

        The result is two time series: %K and %D
        """
        # Calculate %K
        low_min = self.data["Low"].rolling(window=k_window).min()
        high_max = self.data["High"].rolling(window=k_window).max()
        self.data["%K"] = 100 * (self.data["Close"] - low_min) / (high_max - low_min)

        # Calculate %D as the moving average of %K
        self.data["%D"] = self.data["%K"].rolling(window=d_window).mean()

        # Handle any NaN values that may have been created
        self.data["%K"].bfill(inplace=True)
        self.data["%D"].bfill(inplace=True)

    def calculate_slow_stochastic_oscillator(self, d_window=3, slow_k_window=3):
        """
        Calculate the Slow Stochastic Oscillator.
        Slow %K = 3-period SMA of %K
        Slow %D = 3-day SMA of Slow %K
        """
        # Calculate Slow %K, which is the moving average of %K
        self.data["Slow %K"] = self.data["%K"].rolling(window=slow_k_window).mean()

        # Calculate Slow %D, which is the moving average of Slow %K
        self.data["Slow %D"] = self.data["Slow %K"].rolling(window=d_window).mean()

        # Handle any NaN values
        self.data["Slow %K"].bfill(inplace=True)
        self.data["Slow %D"].bfill(inplace=True)

    def detect_fourier_signals(self):
        # Add in fourier transform
        print("check fft_features: ", self.fft_features)
        dominant_period_lengths = sorted(
            set((self.fft_features.loc[:10, "MinutesPerCycle"].values / 2).astype(int)),
            reverse=True,
        )
        dominant_period_lengths = [i for i in dominant_period_lengths if i < 30]
        dominant_period_lengths = dominant_period_lengths[:1]
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

    def detect_rolling_peaks_and_troughs(self, window_size=5):
        # Initialize columns to store the results
        self.data["isLocalPeak"] = False
        self.data["isLocalTrough"] = False

        # Iterate through the DataFrame using a rolling window
        for end_idx in range(window_size, len(self.data)):
            start_idx = max(0, end_idx - window_size)

            # Subset the data for the current window
            window_data = self.data["Close"][start_idx:end_idx]

            # Find peaks
            peaks, _ = find_peaks(window_data)
            peaks_global_indices = [start_idx + p for p in peaks]
            # print("peaks: ", peaks)
            self.data.loc[peaks_global_indices, "isLocalPeak"] = True
            print("peaks_global_indices: ", peaks_global_indices)

            # Find troughs by inverting the data
            troughs, _ = find_peaks(-window_data)
            troughs_global_indices = [start_idx + t for t in troughs]
            # print("troughs: ", troughs)
            self.data.loc[troughs_global_indices, "isLocalTrough"] = True
            print("troughs_global_indices: ", troughs_global_indices)

        print("CHECK LOCAL PEAK: ", self.data["isLocalPeak"])
        print("CHECK LOCAL TROUGH: ", self.data["isLocalTrough"])
        # Assign labels based on peaks and troughs
        self.data["Label"] = "Hold"  # Default label
        self.data.loc[self.data["isLocalPeak"], "Label"] = "Sell"
        self.data.loc[self.data["isLocalTrough"], "Label"] = "Buy"
        print("CHECK LABEL: ", self.data["Label"])

    # Calculating Moving Averages and RSI manually
    def calculate_rsi(self, window=14):
        """Calculate the Relative Strength Index (RSI) for a given dataset and window"""
        delta = self.data["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_moving_averages_and_rsi(self):
        short_window = 5
        long_window = 20
        rsi_period = 14
        self.data["Short_Moving_Avg"] = (
            self.data["Close"].rolling(window=short_window).mean()
        )
        self.data["Long_Moving_Avg"] = (
            self.data["Close"].rolling(window=long_window).mean()
        )
        self.data["RSI"] = self.calculate_rsi(window=rsi_period)

    # Bollinger Bands
    def calculate_bollinger_bands(self):
        (
            self.data["BBand_Upper"],
            self.data["BBand_Middle"],
            self.data["BBand_Lower"],
        ) = talib.BBANDS(self.data["Close"], timeperiod=20)

    # Bollinger Bandwidth
    def calculate_bollinger_bandwidth(self):
        self.data["Bollinger_Bandwidth"] = (
            self.data["BBand_Upper"] - self.data["BBand_Lower"]
        ) / self.data["BBand_Middle"]

    # Bollinger %B
    def calculate_bollinger_percent_b(self):
        self.data["Bollinger_PercentB"] = (
            self.data["Close"] - self.data["BBand_Lower"]
        ) / (self.data["BBand_Upper"] - self.data["BBand_Lower"])

    def construct_kalman_filter(self):
        close_prices = self.data["Close"]
        # Construct a Kalman Filter
        kf = KalmanFilter(initial_state_mean=0, n_dim_obs=1)

        # Use the observed data (close prices) to estimate the state
        state_means, _ = kf.filter(close_prices.values)

        # Convert state means to a Pandas Series for easy plotting
        kalman_estimates = pd.Series(state_means.flatten(), index=self.data.index)

        # Combine the original close prices and Kalman Filter estimates
        kalman_estimates = pd.DataFrame({"KalmanFilterEst": kalman_estimates})
        self.data = self.data.join(kalman_estimates)

        # print('KalmanFilterEst: ', self.data['KalmanFilterEst'])  # Display the first few rows of the dataframe

    # Function to estimate Hurst exponent over multiple sliding windows
    def estimate_hurst_exponent(self, window_size=100, step_size=1):
        """
        Calculates the Hurst exponent over sliding windows and appends the results to the DataFrame.

        :param window_size: Size of each sliding window.
        :param step_size: Step size for moving the window.
        """
        # Prepare an empty list to store Hurst exponent results and corresponding dates
        hurst_exponents = []

        for i in range(0, len(self.data) - window_size + 1, step_size):
            # Extract the window
            window = self.data["Close"].iloc[i : i + window_size]

            # Calculate the Hurst exponent
            H, _, _ = compute_Hc(window, kind="price", simplified=True)

            # Store the result along with the starting date of the window
            hurst_exponents.append(
                {"Date": self.data["Date"].iloc[i], "HurstExponent": H}
            )

        # Convert the results list into a DataFrame
        hurst_exponents = pd.DataFrame(hurst_exponents)

        # Combine the original DataFrame and Hurst exponent estimates
        self.data = self.data.merge(hurst_exponents, on="Date", how="left")

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
            current_price = row["Open"]

            today_date = pd.to_datetime(row["Date"])

            if row["Label"] == "Buy":
                checkpoint_date_bottom = today_date
                checkpoint_price_bottom = current_price
            if row["Label"] == "Sell":
                checkpoint_date_top = today_date
                checkpoint_price_top = current_price
            if checkpoint_date_bottom:
                print("CHECK TIMEDELTA: ", (today_date - checkpoint_date_bottom))
            days_since_bottom = (
                (today_date - checkpoint_date_bottom).seconds // 60
                if checkpoint_date_bottom
                else 0
            )
            print("current_price: ", current_price)
            print("checkpoint_date_top: ", checkpoint_date_top)
            print("checkpoint_price_top: ", checkpoint_price_top)
            print("checkpoint_date_bottom: ", checkpoint_date_bottom)
            print("checkpoint_price_bottom: ", checkpoint_price_bottom)
            days_since_peak = (
                (today_date - checkpoint_date_top).seconds // 60 if checkpoint_date_top else 0
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
            print("MINUTESSINCEPEAK:", self.data["MinutesSincePeak"])
            print("MinutesSinceTrough: ", self.data["MinutesSinceTrough"])

    def calculate_first_second_order_derivatives(self):
        # Calculate first and second order derivatives for selected features
        # for feature in ["KalmanFilterEst", "Short_Moving_Avg", "Long_Moving_Avg"]:
        for feature in ["KalmanFilterEst", "Short_Moving_Avg"]:
            self.data[f"{feature}_1st_Deriv"] = self.data[feature].diff() * 100
            self.data[f"{feature}_2nd_Deriv"] = (
                self.data[f"{feature}_1st_Deriv"].diff() * 100
            )

        # Fill NaN values that were generated by diff()
        self.data.bfill(inplace=True)

    def preprocess_data(self):
        self.data.dropna(inplace=True)

    def train_test_split_time_series(self):
        # Convert 'Date' column to datetime if it's not already
        # self.data['Date'] = pd.to_datetime(self.data['Date'])

        # # Filter the data for training and testing periods
        # train_data = self.data[(self.data['Date'] >= self.train_start) & (self.data['Date'] < self.train_end)]
        # test_data = self.data[(self.data['Date'] >= self.test_start) & (self.data['Date'] < self.test_end)]

        # Sort the data by date to ensure correct time sequence
        self.data.sort_values("Date", inplace=True)

        # Find the split point
        # self.split_idx = int(len(self.data) * (1 - test_size))
        self.data.to_csv("final_dataset_with_new_features.csv")
        # Split the data without shuffling

        # # Filter the data for training and testing periods
        # self.train_data = self.data[(self.data['Date'] >= self.train_start) & (self.data['Date'] < self.train_end)]
        # self.test_data  = self.data[(self.data['Date'] >= self.test_start) & (self.data['Date'] < self.test_end)]

        # Filter the data for training and testing periods and create copies
        self.train_data = self.data[
            (self.data["Date"] >= self.train_start)
            & (self.data["Date"] < self.train_end)
        ].copy()
        self.test_data = self.data[
            (self.data["Date"] >= self.test_start) & (self.data["Date"] < self.test_end)
        ].copy()

        # # let's avoid age sampling / filtering for time being
        # # Calculate the age of each data point in days
        # current_date = self.train_end
        # self.train_data['DataAge'] = (current_date - self.train_data['Date']).dt.days

        # # Apply exponential decay to calculate weights
        # decay_rate = 0.05  # This is a parameter you can tune
        # self.train_data['Weight'] = np.exp(-decay_rate * self.train_data['DataAge'])

        # # Now sample from training data with these weights
        # sample_size = min(len(self.train_data), 1500)
        # self.train_data = self.train_data.sample(n=sample_size, replace=False, weights=self.train_data['Weight'])

        self.train_data.sort_values("Date", inplace=True)
        self.train_data.to_csv("inspect_training_set.csv")
        self.test_data.to_csv("inspect_testing_set.csv")

        # num trades:  6420
        # Final Portfolio Value Before Cost: 10987.401457466523
        # Final Portfolio Value After Cost: 10987.401457466523
        # PnL per trade:  0.1538008500726672

        # num trades:  6420
        # Final Portfolio Value Before Cost: 10987.401457466523
        # Final Portfolio Value After Cost: 10987.401457466523
        # PnL per trade:  0.1538008500726672

        feature_set = [
            # 'Short_Moving_Avg',
            "Short_Moving_Avg_1st_Deriv",
            "Short_Moving_Avg_2nd_Deriv",
            # 'Long_Moving_Avg',
            # "Long_Moving_Avg_1st_Deriv",
            # "Long_Moving_Avg_2nd_Deriv",
            # 'RSI',
            # 'Bollinger_PercentB',
            "MinutesSincePeak",
            "MinutesSinceTrough",
            "FourierSignalSell",
            "FourierSignalBuy",
            "%K",
            "%D",
            # 'Slow %K',
            # 'Slow %D',
            # 'KalmanFilterEst',
            "KalmanFilterEst_1st_Deriv",
            "KalmanFilterEst_2nd_Deriv",
            # 'HurstExponent',
            # 'Interest_Rate_Difference',
            # 'Interest_Rate_Difference_Change',
            # 'Currency_Account_difference'
        ]

       #  ['Timestamp', 'Price', 'isLocalPeak', 'isLocalTrough', 'Label',
       # 'MinutesSincePeak', 'MinutesSinceTrough', 'PriceChangeSincePeak',
       # 'PriceChangeSinceTrough', 'FourierSignalSell', 'FourierSignalBuy']
        self.X_train = self.train_data[feature_set]

        # ].iloc[:self.split_idx]
        self.X_test = self.test_data[feature_set]
        # ].iloc[self.split_idx:]

        # self.y_train = self.data['Label'].iloc[:self.split_idx]
        # self.y_test = self.data['Label'].iloc[self.split_idx:]
        self.y_train = self.train_data["Label"]
        self.y_test = self.test_data["Label"]

        print("len X train: ", len(self.X_train))
        print("len X test: ", len(self.X_test))
        print("len y train: ", len(self.y_train))
        print("len y test: ", len(self.y_test))

    def retrieve_test_set(self):
        return self.test_data

    def train(self):
        # Implement or leave empty to override in derived classes
        pass

    def predict(self):
        # Implement or leave empty to override in derived classes
        feature_set = [
            # 'Short_Moving_Avg',
            "Short_Moving_Avg_1st_Deriv",
            "Short_Moving_Avg_2nd_Deriv",
            # 'Long_Moving_Avg',
            # "Long_Moving_Avg_1st_Deriv",
            # "Long_Moving_Avg_2nd_Deriv",
            # 'RSI',
            # 'Bollinger_PercentB',
            "MinutesSincePeak",
            "MinutesSinceTrough",
            "FourierSignalSell",
            "FourierSignalBuy",
            "%K",
            "%D",
            # 'Slow %K',
            # 'Slow %D',
            # 'KalmanFilterEst',
            "KalmanFilterEst_1st_Deriv",
            "KalmanFilterEst_2nd_Deriv",
            # 'HurstExponent',
            # 'Interest_Rate_Difference',
            # 'Interest_Rate_Difference_Change',
            # 'Currency_Account_difference'
        ]
        test_data = self.data[feature_set]
        print("check test_data: ", test_data)
        test_data.to_csv("test_data.csv")
        output = self.model.predict(test_data)
        print("check output: ", output)

    def evaluate(self, X, y):
        # Implement evaluation logic
        pass
