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
        self.file = open("btc_peaks_troughs_log.txt", "w")

    def update_plot(self, frame):
        current_time = datetime.datetime.now()
        new_data = self.strategy.collect_new_data()
        self.data_buffer.extend(new_data)
        self.data_buffer = [(t, p) for (t, p) in self.data_buffer if (current_time - t).total_seconds() <= self.data_window]

        if self.data_buffer:
            times, prices = zip(*self.data_buffer)
            self.strategy.data = self.data_buffer
            self.strategy.analyze_data()
            betti_curves_df = self.strategy.compute_betti_curves()
            persistence_norms_df = self.strategy.compute_persistence_norms()
            signals, _, _ = self.strategy.generate_signals()

            self.line.set_data(times, prices)
            self.peaks_plot.set_data([times[p] for p in self.strategy.peaks], [prices[p] for p in self.strategy.peaks])
            self.troughs_plot.set_data([times[t] for t in self.strategy.troughs], [prices[t] for t in self.strategy.troughs])
            
            if self.last_price is not None:
                diff = prices[-1] - self.last_price
                print(f"Latest BTC Price: ${prices[-1]:.2f}, {diff:.2f}")
                print("Peaks: ", [times[p] for p in self.strategy.peaks], [prices[p] for p in self.strategy.peaks])
                print("Troughs: ", [times[p] for p in self.strategy.troughs], [prices[p] for p in self.strategy.troughs])
                print("Betti Curves: \n", betti_curves_df)
                print("Persistence Norms: \n", persistence_norms_df)
                print("Signals: ", signals[-10:])
                self.file.write(f"{times[-1]}: ${prices[-1]:.2f}, Change: {diff:.2f}\n")
                self.file.flush()
            
            self.last_price = prices[-1]
            
            # Log peaks, troughs, Betti curves, and persistence norms
            peaks = [(times[p].strftime("%Y-%m-%d %H:%M:%S.%f"), prices[p]) for p in self.strategy.peaks]
            troughs = [(times[t].strftime("%Y-%m-%d %H:%M:%S.%f"), prices[t]) for t in self.strategy.troughs]
            self.log_data("Peaks", peaks)
            self.log_data("Troughs", troughs)
            self.log_data("Betti Curves", betti_curves_df.to_dict())
            self.log_data("Persistence Norms", persistence_norms_df.to_dict())
            self.log_data("Signals", signals)
            
            self.file.write(f"Peaks:  {peaks}\n")
            self.file.write(f"Troughs: {troughs}\n")
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
