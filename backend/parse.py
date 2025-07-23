import pandas as pd

df = pd.read_csv("gemini_results.csv")

times = df['time']

average = times.mean()
min_time = times.min()
max_time = times.max()
p95 = times.quantile(0.95)
p90 = times.quantile(0.90)

print(f"Average time: {average:.3f}s")
print(f"Min time: {min_time:.3f}s")
print(f"Max time: {max_time:.3f}s")
print(f"95th percentile: {p95:.3f}s")
print(f"90th percentile: {p90:.3f}s")
print(f"Accuracy: {(df['predicted'] == df['true_emotion']).mean():.2%}")