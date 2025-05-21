import pandas as pd

df = pd.read_csv("data/historical_matches_with_form.csv", low_memory=False)
df.columns = df.columns.str.strip().str.lower()
print("📄 Columns in historical_matches_with_form.csv:")
print(df.columns.tolist())
