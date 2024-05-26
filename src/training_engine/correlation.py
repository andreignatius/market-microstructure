import pandas as pd
import numpy as np

# Load data
df = pd.read_csv("inputs/historical_labels.csv")
df["Timestamp"] = pd.to_datetime(df["Timestamp"])

# Calculate price changes
df["Price_Change"] = df["Price"].diff().shift(-1)

# Filter BettiCurve_2 values >= 1
betti_1_filtered = df[df["BettiCurve_2"] > 1]

# Calculate correlation
correlation = betti_1_filtered["BettiCurve_2"].corr(betti_1_filtered["Price_Change"])
print(f"Correlation between BettiCurve_2 and subsequent Price Change: {correlation}")

# Lag analysis
for lag in range(1, 20):
    df[f"BettiCurve_2_Lag{lag}"] = df["BettiCurve_2"].shift(lag)
    lag_correlation = df[f"BettiCurve_2_Lag{lag}"].corr(df["Price_Change"])
    print(f"Lag {lag} Correlation: {lag_correlation}")
