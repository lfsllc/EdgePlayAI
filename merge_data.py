import pandas as pd
import os

folder_path = "data/seasons"
files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]

print(f"📁 Found {len(files)} CSV files in {folder_path}")

all_dfs = []
for file in files:
    path = os.path.join(folder_path, file)
    try:
        df = pd.read_csv(path)
        print(f"✅ Loaded {file} with {len(df)} rows")
        df.columns = [c.strip() for c in df.columns]
        df['source_file'] = file
        all_dfs.append(df)
    except Exception as e:
        print(f"❌ Failed to load {file}: {e}")

if all_dfs:
    df_combined = pd.concat(all_dfs, ignore_index=True)
    df_combined.drop_duplicates(subset=['Date', 'HomeTeam', 'AwayTeam'], inplace=True)
    df_combined.to_csv("data/historical_matches.csv", index=False)
    print(f"✅ Saved merged data with {len(df_combined)} rows to data/historical_matches.csv")
else:
    print("⚠️ No valid data to merge.")
