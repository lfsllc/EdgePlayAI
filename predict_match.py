import json
import os
import pandas as pd

# Load team aliases
with open("data/club_name_mapping.json", "r", encoding="utf-8") as f:
    TEAM_ALIASES = {k.lower(): v for k, v in json.load(f).items()}

# Load ELO ratings for feature engineering
ELO_RATINGS = pd.read_csv("data/clubelo_ratings.csv")

def normalize_team_name(team_name):
    """Normalize team name using the mapping"""
    team_name_lower = team_name.strip().lower()
    if team_name_lower in TEAM_ALIASES:
        return TEAM_ALIASES[team_name_lower]
    return team_name.strip()

def engineer_features(home_team, away_team):
    """Create the features required by the model for a given match"""
    try:
        # Check if teams exist in ELO ratings
        if len(ELO_RATINGS[ELO_RATINGS["Club"] == home_team]) == 0:
            print(f"Team not found in ELO ratings: {home_team}")
            return None
            
        if len(ELO_RATINGS[ELO_RATINGS["Club"] == away_team]) == 0:
            print(f"Team not found in ELO ratings: {away_team}")
            return None
        
        # Get ELO ratings - using correct column names (case sensitive)
        home_elo = ELO_RATINGS[ELO_RATINGS["Club"] == home_team]["Elo"].values[0]
        away_elo = ELO_RATINGS[ELO_RATINGS["Club"] == away_team]["Elo"].values[0]
        home_rank = ELO_RATINGS[ELO_RATINGS["Club"] == home_team]["Rank"].values[0]
        away_rank = ELO_RATINGS[ELO_RATINGS["Club"] == away_team]["Rank"].values[0]
        
        # Create the features dictionary with default values
        features = {
            "elo_diff": home_elo - away_elo,
            "form_diff": 0,  # Default value
            "goal_diff": 0,  # Default value
            "rank_diff": away_rank - home_rank,
            "momentum_diff": 0,  # Default value
            "home_away_split_diff": 0,  # Default value
            "h2h_home_wins_last3": 0,  # Default value
            "h2h_away_wins_last3": 0,  # Default value
            "h2h_goal_diff_last3": 0,  # Default value
            "draw_rate_last5": 0,  # Default value
            "avg_goal_diff_last5": 0,  # Default value
            "days_since_last_match": 3,  # Default value
            "fixture_density_flag": 0  # Default value
        }
        
        # Create a DataFrame with the engineered features
        features_df = pd.DataFrame([features])
        return features_df
        
    except Exception as e:
        print(f"Error engineering features: {e}")
        return None

def predict_match(home_team, away_team, model, match_data=None):
    """Predict match outcome using the loaded model and engineered features"""
    # Normalize team names
    home_team = normalize_team_name(home_team)
    away_team = normalize_team_name(away_team)
    
    print(f"Predicting match: {home_team} vs {away_team}")
    
    # Engineer the features required by the model
    features = engineer_features(home_team, away_team)
    
    if features is None:
        print(f"Failed to engineer features for {home_team} vs {away_team}")
        return None
    
    try:
        # Make prediction
        prediction = model.predict_proba(features)[0]
        return {
            'home_team': home_team,
            'away_team': away_team,
            'home_win': round(prediction[0] * 100, 2),
            'draw': round(prediction[1] * 100, 2),
            'away_win': round(prediction[2] * 100, 2)
        }
    except Exception as e:
        print(f"Prediction error: {e}")
        # Return mock data as fallback
        return {
            'home_team': home_team,
            'away_team': away_team,
            'home_win': 50.0,
            'draw': 25.0,
            'away_win': 25.0
        }
