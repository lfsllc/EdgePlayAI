import pandas as pd
import numpy as np
from xgboost import XGBClassifier
import joblib

# === Load Data ===
new_results = pd.read_csv("data/new_results.csv")
full_data = pd.read_csv("data/historical_matches_fully_enhanced.csv", low_memory=False)
elo_df = pd.read_csv("data/clubelo_ratings.csv")
elo_df.columns = elo_df.columns.str.lower()

# === Preprocess New Results ===
new_results["result"] = np.sign(new_results["home_score"] - new_results["away_score"])

# Fill required features with default values
for col in [
    "form_diff", "momentum_diff", "goal_diff", "home_away_split_diff",
    "h2h_home_wins_last3", "h2h_away_wins_last3", "h2h_goal_diff_last3",
    "avg_goal_diff_last5", "draw_rate_last5", "days_since_last_match",
    "fixture_density_flag"
]:
    new_results[col] = 0

# Add Elo data
elo_home = elo_df.rename(columns={"club": "home_team", "elo": "home_elo", "rank": "home_rank"})
elo_away = elo_df.rename(columns={"club": "away_team", "elo": "away_elo", "rank": "away_rank"})
new_results = new_results.merge(elo_home, on="home_team", how="left")
new_results = new_results.merge(elo_away, on="away_team", how="left")
new_results["elo_diff"] = new_results["home_elo"] - new_results["away_elo"]
new_results["rank_diff"] = new_results["away_rank"] - new_results["home_rank"]

# Append new data
updated_df = pd.concat([full_data, new_results], ignore_index=True)
updated_df.to_csv("data/historical_matches_fully_enhanced.csv", index=False)
print(f"✅ Appended {len(new_results)} new matches to historical dataset.")

# === Train Model ===
required_cols = [
    "form_diff", "goal_diff", "elo_diff", "rank_diff", "momentum_diff",
    "home_away_split_diff", "h2h_home_wins_last3", "h2h_away_wins_last3",
    "h2h_goal_diff_last3", "draw_rate_last5", "avg_goal_diff_last5",
    "days_since_last_match", "fixture_density_flag"
]

updated_df = updated_df.dropna(subset=required_cols + ["result"])
X = updated_df[required_cols]
y = updated_df["result"].map({-1: 0, 0: 1, 1: 2})

if len(set(y)) < 3:
    print("⚠️ Not enough variety in match results to retrain. Skipping.")
else:
    model = XGBClassifier(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        gamma=0.2,
        min_child_weight=3,
        eval_metric='mlogloss',
        random_state=42
    )
    model.fit(X, y)
    joblib.dump(model, "model.pkl")
    print("✅ Model retrained and saved as model.pkl")
