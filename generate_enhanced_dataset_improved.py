import pandas as pd

# === Load the enriched dataset ===
df = pd.read_csv("data/historical_matches_with_form.csv", low_memory=False)
df.columns = df.columns.str.strip().str.lower()
df = df.rename(columns={
    "hometeam": "home_team",
    "awayteam": "away_team"
})

# === Calculate improved features ===

# Form diff: compare wins and goal performance
df["form_diff"] = (
    (df["home_last5_wins"] + 0.5 * df["home_last5_draws"]) -
    (df["away_last5_wins"] + 0.5 * df["away_last5_draws"])
)

# Goal diff from form
df["goal_diff"] = df["home_last5_scored"] - df["away_last5_scored"]

# Momentum: team scoring more in last 5 = momentum
df["momentum_diff"] = (
    (df["home_last5_scored"] - df["home_last5_conceded"]) -
    (df["away_last5_scored"] - df["away_last5_conceded"])
)

# Home/Away split diff — assume home advantage baseline
df["home_away_split_diff"] = 1

# Head-to-head placeholders (0 if unavailable)
df["h2h_home_wins_last3"] = 0
df["h2h_away_wins_last3"] = 0
df["h2h_goal_diff_last3"] = 0

# Draw rate in last 5
df["draw_rate_last5"] = (
    (df["home_last5_draws"] + df["away_last5_draws"]) / 10.0
)

# Average goal differential in recent games
df["avg_goal_diff_last5"] = (
    (df["home_last5_scored"] - df["home_last5_conceded"]) -
    (df["away_last5_scored"] - df["away_last5_conceded"])
) / 5.0

# Fixture info placeholder
df["days_since_last_match"] = 3
df["fixture_density_flag"] = 0

# Result target
df["result"] = (df["fthg"] - df["ftag"]).apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))

# === Save to enhanced file ===
df.to_csv("data/historical_matches_fully_enhanced.csv", index=False)
print("✅ Saved fully enhanced dataset to data/historical_matches_fully_enhanced.csv")