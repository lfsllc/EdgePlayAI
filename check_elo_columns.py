import pandas as pd

elo_df = pd.read_csv("data/clubelo_ratings.csv")
print("Columns in Elo file:")
print(elo_df.columns.tolist())
