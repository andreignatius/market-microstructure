import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import tkinter as tk
import time
import datetime

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
        self.last_update_time = time.time()
        self.ani = FuncAnimation(self.fig, self.update_plot, interval=1000, cache_frame_data=False)  # 1-second interval for UI update
        self.data_buffer = []  # Initialize data buffer here
        self.data_window = 60  # 60 seconds window

        # Setup the button to start plotting
        self.plot_button = tk.Button(master, text="Start Plotting", command=self.run_plot)
        self.plot_button.pack()
        self.last_price = None

    def update_plot(self, frame):
        current_time = datetime.datetime.now()
        # Collect new data from the strategy
        new_data = self.strategy.collect_new_data()
        self.data_buffer.extend(new_data)

        # Remove data outside the 60-second window
        self.data_buffer = [(t, p) for (t, p) in self.data_buffer if (current_time - t).total_seconds() <= self.data_window]
        
        # Always perform analysis on the current buffer
        if self.data_buffer:
            times, prices = zip(*self.data_buffer)
            self.strategy.data = self.data_buffer
            self.strategy.analyze_data()
            self.line.set_data(times, prices)
            if self.last_price is not None:
                diff = prices[-1] - self.last_price
                print(f"Latest BTC Price: ${prices[-1]:.2f}, {diff:.2f}")
            self.last_price = prices[-1]
            self.peaks_plot.set_data([times[p] for p in self.strategy.peaks], [prices[p] for p in self.strategy.peaks])
            self.troughs_plot.set_data([times[t] for t in self.strategy.troughs], [prices[t] for t in self.strategy.troughs])

        # Always recompute the axes bounds and redraw
        self.ax.relim()
        self.ax.autoscale_view()

        return self.line, self.peaks_plot, self.troughs_plot


    def run_plot(self):
        plt.show()



