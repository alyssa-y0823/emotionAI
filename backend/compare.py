import pandas as pd

# read CSV files
raw_df = pd.read_csv("4.1_tension_results.csv", usecols=["true_emotion", "sentence", "predicted_emotion", "tension_score"])
df2 = pd.read_csv("4.1_0to1_results.csv", usecols=["predicted_emotion", "predicted_score"])
df3 = pd.read_csv("4.1_3lev_results.csv", usecols=["predicted_emotion", "intensity_level"])

df = pd.concat([raw_df, df2, df3], axis=1)

df.columns = ["true_emotion", "sentence", "pred1", "tension", "pred2", "score", "pred3", "intensity"]
df = df[["sentence", "true_emotion", "pred1", "tension", "pred2", "score", "pred3", "intensity"]]

print("Combined dataframe shape:", df.shape)
print("\nColumn names:", df.columns.tolist())
print("\nFirst 5 rows:")
print(df.head())

df.to_excel("gpt_1call.xlsx", index=False)