# import datetime
# import matplotlib.pyplot as plt
# from matplotlib.animation import FuncAnimation
# import tkinter as tk

# class LivePlotter:
#     def __init__(self, master, strategy):
#         self.master = master
#         self.strategy = strategy
#         self.fig, self.ax = plt.subplots()
#         self.line, = self.ax.plot([], [], 'b-', label='BTC Price')
#         self.peaks_plot, = self.ax.plot([], [], 'r^', label='Peaks')
#         self.troughs_plot, = self.ax.plot([], [], 'gv', label='Troughs')
#         self.ax.legend()
#         self.ax.grid(True)
#         plt.xlabel('Time')
#         plt.ylabel('Price')
#         self.ani = FuncAnimation(self.fig, self.update_plot, interval=1000)
#         self.data_buffer = []
#         self.data_window = 60
#         self.plot_button = tk.Button(master, text="Start Plotting", command=self.run_plot)
#         self.plot_button.pack()
#         self.last_price = None
#         self.file = open("btc_peaks_troughs_log.txt", "w")

#     def update_plot(self, frame):
#         current_time = datetime.datetime.now()
#         new_data = self.strategy.collect_new_data()
#         self.data_buffer.extend(new_data)
#         self.data_buffer = [(t, p) for (t, p) in self.data_buffer if (current_time - t).total_seconds() <= self.data_window]

#         if self.data_buffer:
#             times, prices = zip(*self.data_buffer)
#             self.strategy.data = self.data_buffer
#             self.strategy.analyze_data()

#             self.line.set_data(times, prices)
#             self.peaks_plot.set_data([times[p] for p in self.strategy.peaks], [prices[p] for p in self.strategy.peaks])
#             self.troughs_plot.set_data([times[t] for t in self.strategy.troughs], [prices[t] for t in self.strategy.troughs])
            
#             if self.last_price is not None:
#                 diff = prices[-1] - self.last_price
#                 print(f"Latest BTC Price: ${prices[-1]:.2f}, {diff:.2f}")
#                 print("Peaks: ", [times[p] for p in self.strategy.peaks], [prices[p] for p in self.strategy.peaks])
#                 print("Troughs: ", [times[p] for p in self.strategy.troughs], [prices[p] for p in self.strategy.troughs])
#                 self.file.write(f"{times[-1]}: ${prices[-1]:.2f}, Change: {diff:.2f}\n")
#                 self.file.flush()
            
#             self.last_price = prices[-1]
            
#             # Log peaks, troughs, Betti curves, and persistence norms
#             peaks = [(times[p].strftime("%Y-%m-%d %H:%M:%S.%f"), prices[p]) for p in self.strategy.peaks]
#             troughs = [(times[t].strftime("%Y-%m-%d %H:%M:%S.%f"), prices[t]) for t in self.strategy.troughs]
#             # self.log_data("Peaks", peaks)
#             # self.log_data("Troughs", troughs)
            
#             self.file.write(f"Peaks:  {peaks}\n")
#             self.file.write(f"Troughs: {troughs}\n")
#             self.file.flush()

#         self.ax.relim()
#         self.ax.autoscale_view()

#     def log_data(self, label, data):
#         if data:
#             self.file.write(f"{label}: {data}\n")
#             self.file.flush()

#     def run_plot(self):
#         plt.show()

#     def close(self):
#         self.file.close()
#         plt.close(self.fig)

#     def __del__(self):
#         self.close()

import datetime
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import tkinter as tk
import pandas as pd

class LivePlotter:
    def __init__(self, master, strategy):
        self.master = master
        self.strategy = strategy
        self.fig, self.ax = plt.subplots()
        self.line, = self.ax.plot([], [], 'b-', label='BTC Price')
        self.peaks_plot, = self.ax.plot([], [], 'r^', label='Peaks')
        self.troughs_plot, = self.ax.plot([], [], 'gv', label='Troughs')
        self.ax.legend()
        self.ax.grid(True)
        plt.xlabel('Time')
        plt.ylabel('Price')
        self.ani = FuncAnimation(self.fig, self.update_plot, interval=1000, save_count=100)
        self.data_buffer = pd.DataFrame(columns=['Timestamp', 'Price'])
        self.data_window = 60
        self.plot_button = tk.Button(master, text="Start Plotting", command=self.run_plot)
        self.plot_button.pack()
        self.last_price = None
        self.file = open("btc_peaks_troughs_log.txt", "w")

    def update_plot(self, frame):
        current_time = datetime.datetime.now()
        new_data = self.strategy.collect_new_data()

        # Append new data to the buffer
        if not new_data.empty:
            self.data_buffer = pd.concat([self.data_buffer, new_data])

        # Filter out data older than the data window
        cutoff_time = current_time - pd.Timedelta(seconds=self.data_window)
        self.data_buffer = self.data_buffer[self.data_buffer['Timestamp'] >= cutoff_time]

        if not self.data_buffer.empty:
            # Perform analysis if there is new data
            self.strategy.data = self.data_buffer  # Ensure strategy's data is up-to-date
            self.strategy.analyze_data()

            # Extract times and prices for plotting
            times = self.data_buffer['Timestamp']
            prices = self.data_buffer['Price']

            # Update plot data
            self.line.set_data(times, prices)
            self.peaks_plot.set_data(times[self.strategy.peaks], prices[self.strategy.peaks])
            self.troughs_plot.set_data(times[self.strategy.troughs], prices[self.strategy.troughs])

            if self.last_price is not None:
                diff = prices.iloc[-1] - self.last_price
                print(f"Latest BTC Price: ${prices.iloc[-1]:.2f}, Change: {diff:.2f}")

            self.last_price = prices.iloc[-1] if not prices.empty else self.last_price

            # Redraw the plot
            self.ax.relim()
            self.ax.autoscale_view()

        return self.line, self.peaks_plot, self.troughs_plot

    def run_plot(self):
        plt.show()

    def close(self):
        self.file.close()
        plt.close(self.fig)

    def __del__(self):
        self.close()
