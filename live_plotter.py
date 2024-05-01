import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import tkinter as tk
import time

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
        self.ani = FuncAnimation(self.fig, self.update_plot, interval=1000)

        # Setup the button to start plotting
        self.plot_button = tk.Button(master, text="Start Plotting", command=self.run_plot)
        self.plot_button.pack()

    def update_plot(self, frame):
        current_time = time.time()
        if current_time - self.last_update_time >= 20:
            times, prices, peaks, troughs = self.strategy.analyze_data()
            if times:
                self.line.set_data(times, prices)
                self.peaks_plot.set_data([times[p] for p in peaks], [prices[p] for p in peaks])
                self.troughs_plot.set_data([times[t] for t in troughs], [prices[t] for t in troughs])

                self.ax.relim()
                self.ax.autoscale_view()
                self.last_update_time = current_time  # Reset the timer

        return self.line, self.peaks_plot, self.troughs_plot

    def run_plot(self):
        plt.show()

