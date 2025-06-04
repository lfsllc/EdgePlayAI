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
    # ← use the ENV VAR name, not the literal key!
    api_key = os.getenv("THE_ODDS_API_KEY")
    if not api_key:
        logger.warning("⚠️ THE_ODDS_API_KEY not set in environment")
        return 0.0, 0.0

    try:
        url = (
            f"https://api.the-odds-api.com/v4/sports/soccer_epl/odds/"
            f"?regions=eu&markets=h2h&apiKey={api_key}"
        )
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            for match in data:
                if home in match["home_team"] and away in match["away_team"]:
                    outcomes = match["bookmakers"][0]["markets"][0]["outcomes"]
                    home_price = next((o["price"] for o in outcomes if o["name"] == match["home_team"]), None)
                    away_price = next((o["price"] for o in outcomes if o["name"] == match["away_team"]), None)
                    if home_price and away_price:
                        odds_diff = home_price - away_price
                        implied_prob_home = 1.0 / home_price
                        return odds_diff, implied_prob_home
        logger.warning("⚠️ Odds not found for %s vs %s", home, away)
        return 0.0, 0.0

    except Exception as e:
        logger.error(f"Error fetching odds: {e}")
        return 0.0, 0.0


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
        # If the team is not found in ELO data, bail out
        logger.warning("⚠️ Teams not found in ELO: %s vs %s", home_raw, away_raw)
        return None

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
        proba = model.predict_proba(features)[0]
        # proba[0] = home‐win probability, proba[1] = draw, proba[2] = away‐win
        return {
            "home_win": round(proba[0] * 100, 2),
            "draw": round(proba[1] * 100, 2),
            "away_win": round(proba[2] * 100, 2)
        }
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return None


def get_upcoming_matches():
    # Temporary static list of upcoming matches. Replace with a real API call later.
    return [
        {"home_team": "Manchester City", "away_team": "Liverpool", "date": "2025-06-08"},
        {"home_team": "Arsenal", "away_team": "Chelsea", "date": "2025-06-09"},
        {"home_team": "Tottenham", "away_team": "Manchester United", "date": "2025-06-10"},
    ]


def get_all_teams():
    """Return a sorted list of all clubs from your ELO ratings CSV."""
    clubs = elo_ratings["club"].dropna().unique().tolist()
    return sorted(clubs)
