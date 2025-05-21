import requests
import pandas as pd
from datetime import datetime, timedelta

# === CONFIG ===
API_KEY = "fc82ebb5ce14fe2b37d27f5bac15bbf0"
LEAGUE_IDS = [39, 140, 135, 78, 61]  # EPL, La Liga, Serie A, Bundesliga, Ligue 1
YESTERDAY = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")

headers = {
    "x-apisports-key": API_KEY
}

base_url = "https://v3.football.api-sports.io/fixtures"

all_matches = []

# === Fetch Results for Each League ===
for league_id in LEAGUE_IDS:
    params = {
        "date": YESTERDAY,
        "league": league_id,
        "season": 2024
    }

    response = requests.get(base_url, headers=headers, params=params)
    data = response.json()

    if "response" in data:
        for match in data["response"]:
            home = match["teams"]["home"]["name"]
            away = match["teams"]["away"]["name"]
            home_score = match["goals"]["home"]
            away_score = match["goals"]["away"]
            status = match["fixture"]["status"]["short"]
            date = match["fixture"]["date"][:10]
            league = match["league"]["name"]

            # Only completed matches
            if status == "FT":
                all_matches.append({
                    "date": date,
                    "league": league,
                    "home_team": home,
                    "away_team": away,
                    "home_score": home_score,
                    "away_score": away_score
                })

# === Save to CSV ===
df = pd.DataFrame(all_matches)
output_path = "data/new_results.csv"
df.to_csv(output_path, index=False)
print(f"✅ Saved {len(df)} completed matches to {output_path}")
