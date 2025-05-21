import os
import discord
from discord.ext import commands
from discord import app_commands
import pandas as pd
import joblib
from dotenv import load_dotenv
from predict_match import predict_match

# === Load environment variables ===
load_dotenv()

# === Load model and match data ===
model = joblib.load("model.pkl")
match_data = pd.read_csv("data/historical_matches_fully_enhanced.csv")

# === Initialize bot ===
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# === Predict command ===
@tree.command(name="predict", description="Predict the outcome of a match")
@app_commands.describe(match="Enter match like: Arsenal vs Bournemouth")
async def predict(interaction: discord.Interaction, match: str):
    await interaction.response.defer()
    try:
        home, away = [team.strip() for team in match.split("vs")]
        prediction = predict_match(home, away, model, match_data)

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

# === On ready ===
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await tree.sync()
        print(f"🔁 Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

# === Run bot with token ===
token = os.getenv("DISCORD_TOKEN")
if not token:
    print("❌ DISCORD_TOKEN not found in environment or .env file")
else:
    bot.run(token)