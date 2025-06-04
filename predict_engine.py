
import os
import pandas as pd
import requests
import joblib
import logging

logger = logging.getLogger("EdgePlayAI")

# === Load shared data ===
model = joblib.load("model.pkl")
elo_ratings = pd.read_csv("data/clubelo_ratings.csv")
elo_ratings.columns = elo_ratings.columns.str.lower()

with open("data/club_name_mapping.json", "r", encoding="utf-8") as f:
    import json
    team_aliases = {k.lower(): v for k, v in json.load(f).items()}

def normalize_team_name(name):
    clean = name.strip().lower().replace("fc", "").strip()
    return team_aliases.get(clean, clean).title()

def fetch_odds(home, away):
    api_key = os.getenv("c5f2b6a97f2600608383ebfb3acbd9b3")
    if not api_key:
        logger.warning("⚠️ THEODDS_API_KEY not set in environment")
        return 0, 0  # fallback

    try:
        url = f"https://api.the-odds-api.com/v4/sports/soccer_epl/odds/?regions=eu&markets=h2h&apiKey={api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            for match in data:
                if home in match['home_team'] and away in match['away_team']:
                    odds = match['bookmakers'][0]['markets'][0]['outcomes']
                    home_odds = [o['price'] for o in odds if o['name'] == match['home_team']]
                    away_odds = [o['price'] for o in odds if o['name'] == match['away_team']]
                    if home_odds and away_odds:
                        odds_diff = home_odds[0] - away_odds[0]
                        implied_prob_home = 1 / home_odds[0]
                        return odds_diff, implied_prob_home
        logger.warning("⚠️ Odds not found.")
        return 0, 0
    except Exception as e:
        logger.error(f"Error fetching odds: {e}")
        return 0, 0

def predict_match(home_raw, away_raw):
    home = normalize_team_name(home_raw)
    away = normalize_team_name(away_raw)

    try:
        home_row = elo_ratings[elo_ratings["club"] == home]
        away_row = elo_ratings[elo_ratings["club"] == away]
        home_elo = home_row["elo"].values[0]
        away_elo = away_row["elo"].values[0]
        home_rank = home_row["rank"].values[0]
        away_rank = away_row["rank"].values[0]
    except IndexError:
        return None, f"⚠️ Match not found. Could not find teams: {home_raw} vs {away_raw}"

    odds_diff, implied_prob_home = fetch_odds(home, away)

    features = pd.DataFrame([{
        "elo_diff": home_elo - away_elo,
        "form_diff": 0,
        "goal_diff": 0,
        "rank_diff": away_rank - home_rank,
        "momentum_diff": 0,
        "home_away_split_diff": 0,
        "h2h_home_wins_last3": 0,
        "h2h_away_wins_last3": 0,
        "h2h_goal_diff_last3": 0,
        "draw_rate_last5": 0,
        "avg_goal_diff_last5": 0,
        "days_since_last_match": 0,
        "fixture_density_flag": 0,
        "odds_diff": odds_diff,
        "implied_prob_home": implied_prob_home
    }])

    try:
        prediction = model.predict_proba(features)[0]
        return prediction, None
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return None, "⚠️ Internal model error"

def get_upcoming_matches():
    # Temporary static list of upcoming matches (you can connect to an API later)
    return [
        {"home_team": "Manchester City", "away_team": "Liverpool", "date": "2025-06-08"},
        {"home_team": "Arsenal", "away_team": "Chelsea", "date": "2025-06-09"},
        {"home_team": "Tottenham", "away_team": "Manchester United", "date": "2025-06-10"},
    ]

