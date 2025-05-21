import soccerdata as sd
import pandas as pd

elo = sd.ClubElo()
all_elo = elo.read_by_date()
all_elo.to_csv("data/clubelo_ratings.csv", index=False)
print("✅ ClubElo data saved.")
