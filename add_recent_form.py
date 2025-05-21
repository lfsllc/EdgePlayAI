# 🧠 Add recent team form (last 5 games) to training
import pandas as pd

df = pd.read_csv("data/historical_matches.csv")

# Make sure Date is datetime
df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors='coerce')
df = df.dropna(subset=["Date"])

# Sort by date
df = df.sort_values("Date")

# Create helper function to compute rolling stats
def compute_form_features(df, team_col, prefix):
    form_features = []
    grouped = df.groupby(team_col)

    for team, group in grouped:
        group = group.sort_values("Date")
        rolling_wins = []
        rolling_draws = []
        rolling_losses = []
        rolling_goals_scored = []
        rolling_goals_conceded = []

        for i in range(len(group)):
            past_matches = group.iloc[max(i-5, 0):i]  # last 5 matches before i

            wins = ((past_matches["FTHG"] > past_matches["FTAG"]) & (team_col == "HomeTeam")) | \
                   ((past_matches["FTAG"] > past_matches["FTHG"]) & (team_col == "AwayTeam"))
            draws = past_matches["FTHG"] == past_matches["FTAG"]
            losses = ~wins & ~draws

            if team_col == "HomeTeam":
                goals_scored = past_matches["FTHG"].sum()
                goals_conceded = past_matches["FTAG"].sum()
            else:
                goals_scored = past_matches["FTAG"].sum()
                goals_conceded = past_matches["FTHG"].sum()

            rolling_wins.append(wins.sum())
            rolling_draws.append(draws.sum())
            rolling_losses.append(losses.sum())
            rolling_goals_scored.append(goals_scored)
            rolling_goals_conceded.append(goals_conceded)

        form_features.append(pd.DataFrame({
            f"{prefix}_last5_wins": rolling_wins,
            f"{prefix}_last5_draws": rolling_draws,
            f"{prefix}_last5_losses": rolling_losses,
            f"{prefix}_last5_scored": rolling_goals_scored,
            f"{prefix}_last5_conceded": rolling_goals_conceded
        }, index=group.index))

    return pd.concat(form_features)

# Apply to both Home and Away teams
home_form = compute_form_features(df, "HomeTeam", "home")
away_form = compute_form_features(df, "AwayTeam", "away")

# Merge back
df = pd.concat([df, home_form, away_form], axis=1)

# Save the enriched dataset
form_output_path = "data/historical_matches_with_form.csv"
df.to_csv(form_output_path, index=False)
print(f"✅ Saved new dataset with form to: {form_output_path}")