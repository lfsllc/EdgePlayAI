import pandas as pd
import joblib

def predict_result(home_team, away_team):
    # Load Elo ratings
    elo_df = pd.read_csv("data/clubelo_ratings.csv")
    elo_df.columns = elo_df.columns.str.lower()

    try:
        home_elo = elo_df[elo_df["club"] == home_team]["elo"].values[0]
        away_elo = elo_df[elo_df["club"] == away_team]["elo"].values[0]
        home_rank = elo_df[elo_df["club"] == home_team]["rank"].values[0]
        away_rank = elo_df[elo_df["club"] == away_team]["rank"].values[0]
    except IndexError:
        return "❌ One or both team names are invalid."

    # Construct input
    features = {
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
        "days_since_last_match": 3,
        "fixture_density_flag": 0
    }

    X_input = pd.DataFrame([features])

    # Load model
    try:
        model = joblib.load("model.pkl")
    except FileNotFoundError:
        return "❌ Prediction model not found. Please retrain first."

    # Predict
    probs = model.predict_proba(X_input)[0]
    pred = model.predict(X_input)[0]
    outcome_map = {0: "Away Win", 1: "Draw", 2: "Home Win"}

    return f"""📊 Prediction: **{outcome_map[pred]}**
🔢 Probabilities:
• Away Win: {probs[0]:.2%}
• Draw    : {probs[1]:.2%}
• Home Win: {probs[2]:.2%}"""
