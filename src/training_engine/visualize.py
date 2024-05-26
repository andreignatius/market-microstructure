import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv("inputs/historical_labels.csv")

# Ensure the 'Timestamp' column is in datetime format
df["Timestamp"] = pd.to_datetime(df["Timestamp"])

# Mask BettiCurve_1 values less than 3
betti_1_masked = np.where(df["BettiCurve_1"] >= 3, df["BettiCurve_1"], np.nan)

# Create a figure and a set of subplots
fig, ax1 = plt.subplots()

# Plot Price
ax1.plot(df["Timestamp"], df["Price"], "b-", label="Price")
ax1.set_xlabel("Time")
ax1.set_ylabel("Price", color="b")
ax1.tick_params(axis="y", labelcolor="b")

# Create a second y-axis for BettiCurve_2
ax2 = ax1.twinx()
ax2.plot(df["Timestamp"], df["BettiCurve_2"], "g-", label="BettiCurve_2")
ax2.set_ylabel("BettiCurve_2", color="g")
ax2.tick_params(axis="y", labelcolor="g")

# Create a third y-axis for BettiCurve_1
ax3 = ax1.twinx()
ax3.plot(df["Timestamp"], betti_1_masked, "r-", label="BettiCurve_1")
ax3.set_ylabel("BettiCurve_1", color="r")
ax3.tick_params(axis="y", labelcolor="r")

# Adjust the position of the third y-axis
ax3.spines["right"].set_position(("outward", 60))

# Add legends
ax1.legend(loc="upper left")
ax2.legend(loc="upper center")
ax3.legend(loc="upper right")

# Add a title
plt.title("Price and Betti Curves Over Time")

# Show the plot
plt.show()
