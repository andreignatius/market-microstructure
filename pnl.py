import pandas as pd

# Load the CSV file into a DataFrame
df = pd.read_csv('signals.csv')

# Initialize variables
pnl = 0
positions = []

# Iterate through the DataFrame rows
for index, row in df.iterrows():
    if row['Signal'] == 'Buy':
        positions.append(row['Price'])  # Add buy price to positions
    elif row['Signal'] == 'Sell' and positions:
        buy_price = positions.pop(0)  # Get the earliest buy price
        sell_price = row['Price']
        pnl += sell_price - buy_price  # Calculate profit for this trade

# Output the total PnL
print(f"Total PnL: ${pnl:.2f}")
