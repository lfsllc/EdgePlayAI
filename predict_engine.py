import pandas as pd
import joblib
import os
from sklearn.preprocessing import StandardScaler

# Load models
model_1x2 = joblib.load("model.pkl")
model_btts = joblib.load("model_btts.pkl")

# Load and prepare team list
df = pd.read_csv("historical_matches_fully_enhanced.csv")
all_teams = sorted(set(df["home_team"]).union(set(df["away_team"])))

def get_all_teams():
    return all_teams

def get_upcoming_matches():
    # This function could be updated to pull from an API in the future
    # For now, we return a hardcoded list
    return [
        "Manchester City vs Liverpool",
        "Arsenal vs Chelsea",
        "Barcelona vs Real Madrid",
        "Juventus vs Inter Milan",
        "Bayern Munich vs Borussia Dortmund"
    ]

def extract_features(df, home_team, away_team):
    match = df[(df["home_team"] == home_team) & (df["away_team"] == away_team)]
    if match.empty:
        return None
    return match.iloc[-1:]

def predict_match(match):
    try:
        home_team, away_team = map(str.strip, match.split("vs"))
    except ValueError:
        return None

    if home_team not in all_teams or away_team not in all_teams:
        return None

    match_data = extract_features(df, home_team, away_team)
    if match_data is None:
        return None

    features = match_data.drop(columns=["target", "btts", "home_team", "away_team"])
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)

    # Predict 1X2
    probabilities = model_1x2.predict_proba(features_scaled)[0]
    home_win = round(probabilities[0] * 100, 2)
    draw = round(probabilities[1] * 100, 2)
    away_win = round(probabilities[2] * 100, 2)

    # Predict BTTS
    btts_result = bool(model_btts.predict(features_scaled)[0])

    return {
        "1X2": (home_win, draw, away_win),
        "BTTS": btts_result
    }
