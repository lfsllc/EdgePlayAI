import os
import discord
from discord.ext import commands
from discord import app_commands
import pandas as pd
import joblib
from dotenv import load_dotenv
import json
import time

# === Load environment variables ===
load_dotenv()

# === Initialize resources at startup ===
print("Loading model and data...")
model = None
match_data = None
team_aliases = None

try:
    start_time = time.time()
    model = joblib.load("model.pkl")
    print(f"Model loaded in {time.time() - start_time:.2f} seconds")
    
    start_time = time.time()
    match_data = pd.read_csv("data/historical_matches_fully_enhanced.csv")
    print(f"Match data loaded in {time.time() - start_time:.2f} seconds")
    print(f"✅ Dataset shape: {match_data.shape}")
    print("✅ Sample match entries:")
    print(match_data[['home_team', 'away_team']].drop_duplicates().head(5))
    
    start_time = time.time()
    with open("data/club_name_mapping.json", "r", encoding="utf-8") as f:
        team_aliases = {k.lower(): v for k, v in json.load(f).items()}
    print(f"Team aliases loaded in {time.time() - start_time:.2f} seconds")

    print("✅ Resources loaded successfully")
except Exception as e:
    print(f"❌ Failed to load resources: {e}")

# === Initialize bot ===
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

def normalize_team_name(team_name, team_aliases):
    return team_aliases.get(team_name.strip().lower(), team_name.strip())

def predict_match(home_team, away_team, model, match_data, team_aliases):
    home_team = normalize_team_name(home_team, team_aliases)
    away_team = normalize_team_name(away_team, team_aliases)

    match = match_data[
        (match_data['home_team'].str.strip().str.lower() == home_team.lower()) &
        (match_data['away_team'].str.strip().str.lower() == away_team.lower())
    ]

    if match.empty:
        print(f"⚠️ Match not found: {home_team} vs {away_team}")
        return None

    numeric_features = match.select_dtypes(include=['number'])

    try:
        prediction = model.predict_proba(numeric_features)[0]
        return {
            'home_win': round(prediction[0] * 100, 2),
            'draw': round(prediction[1] * 100, 2),
            'away_win': round(prediction[2] * 100, 2)
        }
    except Exception as e:
        print(f"Prediction error: {e}")
        return {
            'home_win': 50.0,
            'draw': 25.0,
            'away_win': 25.0
        }

@tree.command(name="predict", description="Predict the outcome of a match")
@app_commands.describe(match="Enter match like: Arsenal vs Bournemouth")
async def predict(interaction: discord.Interaction, match: str):
    await interaction.response.defer(thinking=True)

    try:
        if model is None or match_data is None or team_aliases is None:
            await interaction.followup.send("⚠️ Bot resources are not loaded. Please try again later.")
            return

        home, away = [team.strip() for team in match.split("vs")]
        prediction = predict_match(home, away, model, match_data, team_aliases)

        if prediction is None:
            await interaction.followup.send("⚠️ Match not found in dataset. Please check team names.")
            return

        msg = (
            f"\U0001F4CA **EdgePlay AI Prediction for {home} vs {away}:**\n"
            f"\U0001F3E0 {home} Win: {prediction['home_win']}%\n"
            f"\U0001F91D Draw: {prediction['draw']}%\n"
            f"\U0001F680 {away} Win: {prediction['away_win']}%"
        )
        await interaction.followup.send(msg)

    except Exception as e:
        await interaction.followup.send("⚠️ Internal error. Please try again later.")
        print(f"Error: {e}")

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await tree.sync()
        print(f"🔁 Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

token = os.getenv("DISCORD_TOKEN")
if not token:
    print("❌ DISCORD_TOKEN not found in environment or .env file")
else:
    try:
        bot.run(token)
    except Exception as e:
        print(f"❌ Bot crashed: {e}")
