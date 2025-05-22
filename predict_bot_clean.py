import os
import discord
from discord.ext import commands
from discord import app_commands
import pandas as pd
import joblib
from dotenv import load_dotenv
import json
import time
import requests
from datetime import datetime
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EdgePlayAI")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# === Load model and data ===
logger.info("Loading model and data...")
model = joblib.load("model.pkl")
elo_ratings = pd.read_csv("data/clubelo_ratings.csv")
with open("data/club_name_mapping.json", "r", encoding="utf-8") as f:
    team_aliases = {k.lower(): v for k, v in json.load(f).items()}
logger.info("✅ Resources loaded successfully")

def normalize_team_name(team_name):
    return team_aliases.get(team_name.strip().lower(), team_name.strip())

def engineer_features(home_team, away_team):
    try:
        home = elo_ratings[elo_ratings["Club"] == home_team]
        away = elo_ratings[elo_ratings["Club"] == away_team]
        if home.empty or away.empty:
            logger.warning(f"Missing teams: {home_team} or {away_team}")
            return None

        features = {
            "elo_diff": home["Elo"].values[0] - away["Elo"].values[0],
            "form_diff": 0, "goal_diff": 0, "rank_diff": away["Rank"].values[0] - home["Rank"].values[0],
            "momentum_diff": 0, "home_away_split_diff": 0, "h2h_home_wins_last3": 0,
            "h2h_away_wins_last3": 0, "h2h_goal_diff_last3": 0, "draw_rate_last5": 0,
            "avg_goal_diff_last5": 0, "days_since_last_match": 3, "fixture_density_flag": 0
        }
        return pd.DataFrame([features])
    except Exception as e:
        logger.error("Feature engineering error", exc_info=True)
        return None

def predict_match(home_team, away_team):
    home = normalize_team_name(home_team)
    away = normalize_team_name(away_team)
    logger.info(f"Predicting: {home} vs {away}")
    features = engineer_features(home, away)
    if features is None:
        return None
    try:
        prediction = model.predict_proba(features)[0]
        return {
            'home_team': home, 'away_team': away,
            'home_win': round(prediction[0] * 100, 2),
            'draw': round(prediction[1] * 100, 2),
            'away_win': round(prediction[2] * 100, 2)
        }
    except Exception as e:
        logger.error("Prediction error", exc_info=True)
        return None

@tree.command(name="predict", description="Predict the outcome of a match")
@app_commands.describe(match="Enter match like: Arsenal vs Chelsea")
async def predict(interaction: discord.Interaction, match: str):
    await interaction.response.defer(thinking=True)
    try:
        home, away = [team.strip() for team in match.split("vs")]
    except ValueError:
        await interaction.followup.send("⚠️ Invalid format. Please use: Team1 vs Team2")
        return

    prediction = predict_match(home, away)
    if prediction is None:
        await interaction.followup.send(
            f"⚠️ Match not found. Please check team names.\n"
            f"Try using short forms like 'Man United', 'PSG', etc.\n"
            f"Use `/teams` to view supported teams."
        )
        return

    msg = (
        f"📊 **EdgePlay AI Prediction for {prediction['home_team']} vs {prediction['away_team']}:**\n"
        f"🏠 {prediction['home_team']} Win: {prediction['home_win']}%\n"
        f"🤝 Draw: {prediction['draw']}%\n"
        f"🚀 {prediction['away_team']} Win: {prediction['away_win']}%"
    )
    await interaction.followup.send(msg)

@tree.command(name="teams", description="Show available teams for prediction")
async def teams(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    team_list = sorted(elo_ratings['Club'].unique())
    chunks = [team_list[i:i+20] for i in range(0, len(team_list), 20)]
    for i, chunk in enumerate(chunks):
        await interaction.followup.send(f"**Teams {i+1}:**\n" + "\n".join(chunk))

@tree.command(name="upcoming", description="Show upcoming Premier League matches with date and time")
async def upcoming(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    api_key = os.getenv("FOOTBALL_DATA_API_KEY")
    headers = {'X-Auth-Token': api_key}
    url = 'https://api.football-data.org/v2/competitions/PL/matches?status=SCHEDULED'

    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        matches = data.get("matches", [])
        logger.info(f"Fetched {len(matches)} upcoming matches.")

        if not matches:
            await interaction.followup.send("⚠️ No upcoming Premier League matches found.")
            return

        msg_lines = ["📅 **Upcoming Premier League Matches:**"]
        for match in matches[:10]:
            dt = datetime.strptime(match['utcDate'], "%Y-%m-%dT%H:%M:%SZ")
            msg_lines.append(f"{dt.strftime('%Y-%m-%d %H:%M UTC')} — {match['homeTeam']['name']} vs {match['awayTeam']['name']}")
        await interaction.followup.send("\n".join(msg_lines))
    except Exception as e:
        logger.error("Failed to fetch upcoming matches", exc_info=True)
        await interaction.followup.send("⚠️ Error fetching upcoming matches.")

@bot.event
async def on_ready():
    logger.info(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await tree.sync()
        logger.info(f"🔁 Synced {len(synced)} command(s): {[cmd.name for cmd in synced]}")
    except Exception as e:
        logger.error("❌ Failed to sync commands", exc_info=True)

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    logger.critical("❌ DISCORD_TOKEN is missing from environment")
else:
    try:
        bot.run(TOKEN)
    except Exception as e:
        logger.critical("❌ Bot crashed during startup", exc_info=True)