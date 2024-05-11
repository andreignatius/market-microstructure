import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv('historical_labels.csv')

# Ensure the 'Timestamp' column is in datetime format
df['Timestamp'] = pd.to_datetime(df['Timestamp'])

# Create a figure and a set of subplots
fig, ax1 = plt.subplots()

# Plot Price
ax1.plot(df['Timestamp'], df['Price'], 'b-', label='Price')
ax1.set_xlabel('Time')
ax1.set_ylabel('Price', color='b')
ax1.tick_params(axis='y', labelcolor='b')

# # Create a second y-axis for BettiCurve_0
# ax2 = ax1.twinx()
# ax2.plot(df['Timestamp'], df['BettiCurve_0'], 'g-', label='BettiCurve_0')
# ax2.set_ylabel('BettiCurve_0', color='g')
# ax2.tick_params(axis='y', labelcolor='g')

# Create a third y-axis for BettiCurve_1
ax3 = ax1.twinx()
ax3.plot(df['Timestamp'], df['BettiCurve_1'], 'r-', label='BettiCurve_1')
ax3.set_ylabel('BettiCurve_1', color='r')
ax3.tick_params(axis='y', labelcolor='r')

# Adjust the position of the third y-axis
ax3.spines['right'].set_position(('outward', 60))

# Add legends
ax1.legend(loc='upper left')
# ax2.legend(loc='upper center')
ax3.legend(loc='upper right')

# Add a title
plt.title('Price and Betti Curves Over Time')

# Show the plot
plt.show()
