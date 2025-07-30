import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# Load your CSV file
df = pd.read_csv('Untitled.csv')  # Replace with your file path

# Extract the difference columns
flash_diffs = df['flash - 4.1'].values
gpt4o_diffs = df['4o - 4.1'].values

# Remove any NaN values
flash_diffs = flash_diffs[~np.isnan(flash_diffs)]
gpt4o_diffs = gpt4o_diffs[~np.isnan(gpt4o_diffs)]

# Create figure with two subplots (red style histograms)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# Create custom bins from -1 to 1
bins = np.linspace(-0.75, 0.75, 31)  # 

# Histogram for Gemini 2.5 Flash (red style)
ax1.hist(flash_diffs, bins=bins, color='#ff6b6b', alpha=0.8, edgecolor='white', linewidth=0.5)
ax1.set_xlabel('Difference from GPT-4.1')
ax1.set_ylabel('Frequency')
ax1.set_title('Distribution of Gemini Flash Errors')
ax1.set_xlim(-0.75, 0.75)
ax1.grid(True, alpha=0.3)
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)

# Histogram for GPT-4o (red style)
ax2.hist(gpt4o_diffs, bins=bins, color='#ff6b6b', alpha=0.8, edgecolor='white', linewidth=0.5)
ax2.set_xlabel('Difference from GPT-4.1')
ax2.set_ylabel('Frequency')
ax2.set_title('Distribution of GPT-4o Errors')
ax1.set_xlim(-0.7, 0.7)
ax2.grid(True, alpha=0.3)
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)

plt.tight_layout()
plt.show()

# Print basic stats
print(f"Gemini Flash - Mean: {np.mean(flash_diffs):.4f}, Std: {np.std(flash_diffs):.4f}")
print(f"GPT-4o - Mean: {np.mean(gpt4o_diffs):.4f}, Std: {np.std(gpt4o_diffs):.4f}")