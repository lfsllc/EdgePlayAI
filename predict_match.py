import json

with open("data/club_name_mapping.json", "r", encoding="utf-8") as f:
    TEAM_ALIASES = {k.lower(): v for k, v in json.load(f).items()}

def predict_match(home_team, away_team, model, match_data):
    home_team = normalize_team_name(home_team)
    away_team = normalize_team_name(away_team)

    # Find matching row in historical data
    match = match_data[
        (match_data['home_team'].str.lower() == home_team.lower()) &
        (match_data['away_team'].str.lower() == away_team.lower())
    ]

    if match.empty:
        return None  # Match not found

    features = match.drop(columns=['home_team', 'away_team', 'match_date', 'actual_result'])
    prediction = model.predict_proba(features)[0]
    return {
        'home_win': round(prediction[0] * 100, 2),
        'draw': round(prediction[1] * 100, 2),
        'away_win': round(prediction[2] * 100, 2)
    }
