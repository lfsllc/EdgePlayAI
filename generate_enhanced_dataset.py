import pandas as pd

# === Load the enriched dataset ===
df = pd.read_csv("data/historical_matches_with_form.csv", low_memory=False)
df.columns = df.columns.str.strip().str.lower()  # ✅ normalize column names

# Rename team columns if needed
df = df.rename(columns={
    "hometeam": "home_team",
    "awayteam": "away_team"
})

# === Add dummy features for training ===
# You can replace these with real logic later
df["form_diff"] = df["home_last5_wins"] - df["away_last5_wins"]
df["goal_diff"] = df["fthg"] - df["ftag"]
df["momentum_diff"] = 0
df["home_away_split_diff"] = 0
df["h2h_home_wins_last3"] = 0
df["h2h_away_wins_last3"] = 0
df["h2h_goal_diff_last3"] = 0
df["draw_rate_last5"] = 0
df["avg_goal_diff_last5"] = 0
df["days_since_last_match"] = 3
df["fixture_density_flag"] = 0

# === Add target column ===
df["result"] = df["goal_diff"].apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))

# === Save fully enhanced dataset ===
df.to_csv("data/historical_matches_fully_enhanced.csv", index=False)
print("✅ Saved fully enhanced dataset to data/historical_matches_fully_enhanced.csv")