import pandas as pd
import os
import requests
from io import BytesIO

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

urls = {
    "EPL_2023": "https://www.football-data.co.uk/mmz4281/2324/E0.csv",
    "LaLiga_2023": "https://www.football-data.co.uk/mmz4281/2324/SP1.csv"
}

def download_data():
    for name, url in urls.items():
        print(f"Downloading {name}...")
        r = requests.get(url)
        if r.status_code == 200:
            df = pd.read_csv(BytesIO(r.content))
            file_path = os.path.join(DATA_DIR, f"{name}.csv")
            df.to_csv(file_path, index=False)
            print(f"Saved to {file_path}")
        else:
            print(f"Failed to download {name}")

def load_and_clean():
    dfs = []
    for file in os.listdir(DATA_DIR):
        if file.endswith(".csv"):
            df = pd.read_csv(os.path.join(DATA_DIR, file))
            df = df[['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR', 'B365H', 'B365D', 'B365A']]
            df['League'] = file.replace('.csv', '')
            dfs.append(df)

    combined = pd.concat(dfs, ignore_index=True)
    combined['Date'] = pd.to_datetime(combined['Date'], errors='coerce')
    combined.dropna(inplace=True)
    combined.columns = ['date', 'home_team', 'away_team', 'home_goals', 'away_goals', 'result',
                        'odds_home', 'odds_draw', 'odds_away', 'league']
    return combined

if __name__ == "__main__":
    download_data()
    data = load_and_clean()
    data.to_csv("data/cleaned_combined_data.csv", index=False)
    print("✅ Cleaned data saved to data/cleaned_combined_data.csv")
