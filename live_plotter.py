import datetime
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import tkinter as tk

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
        self.ani = FuncAnimation(self.fig, self.update_plot, interval=1000)
        self.data_buffer = []
        self.data_window = 60
        self.plot_button = tk.Button(master, text="Start Plotting", command=self.run_plot)
        self.plot_button.pack()
        self.last_price = None
        self.file = open("btc_peaks_troughs_log.txt", "w")  # Separate file for peaks and troughs

    def update_plot(self, frame):
        current_time = datetime.datetime.now()
        new_data = self.strategy.collect_new_data()
        self.data_buffer.extend(new_data)
        self.data_buffer = [(t, p) for (t, p) in self.data_buffer if (current_time - t).total_seconds() <= self.data_window]

        if self.data_buffer:
            times, prices = zip(*self.data_buffer)
            self.strategy.data = self.data_buffer
            self.strategy.analyze_data()
            betti_curves_df = self.strategy.compute_betti_curves()  # Compute Betti curves
            persistence_norms_df = self.strategy.compute_persistence_norms()  # Compute Persistence norms
            self.line.set_data(times, prices)
            self.peaks_plot.set_data([times[p] for p in self.strategy.peaks], [prices[p] for p in self.strategy.peaks])
            self.troughs_plot.set_data([times[t] for t in self.strategy.troughs], [prices[t] for t in self.strategy.troughs])
            if self.last_price is not None:
                diff = prices[-1] - self.last_price
                print(f"Latest BTC Price: ${prices[-1]:.2f}, {diff:.2f}")
                print("peaks: ", [times[p] for p in self.strategy.peaks], [prices[p] for p in self.strategy.peaks])
                print("troughs: ", [times[p] for p in self.strategy.troughs], [prices[p] for p in self.strategy.troughs])
                print("Betti Curves: \n", betti_curves_df)
                print("Persistence Norms: \n", persistence_norms_df)
                self.file.write(f"{times[-1]}: ${prices[-1]:.2f}, Change: {diff:.2f}\n")  # Log each new price
                self.file.flush()
            self.last_price = prices[-1]
            # Log peaks and troughs
            peaks = [(times[p].strftime("%Y-%m-%d %H:%M:%S.%f"), prices[p]) for p in self.strategy.peaks]
            troughs = [(times[t].strftime("%Y-%m-%d %H:%M:%S.%f"), prices[t]) for t in self.strategy.troughs]
            self.log_data("Peaks", peaks)
            self.log_data("Troughs", troughs)
            self.file.write(f"peaks:  {peaks}, \n")  # Log each new price
            self.file.write(f"troughs: {troughs}, \n")  # Log each new price
            self.file.flush()

        self.ax.relim()
        self.ax.autoscale_view()

    def log_data(self, label, data):
        if data:
            self.file.write(f"{label}: {data}\n")
            self.file.flush()

    def run_plot(self):
        plt.show()

    def close(self):
        self.file.close()
        plt.close(self.fig)

    def __del__(self):
        self.close()
