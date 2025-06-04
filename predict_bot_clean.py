import os
import discord
import logging
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

from predict_engine import predict_match, get_upcoming_matches, get_all_teams

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EdgePlayAI")

intents = discord.Intents.default()
client = commands.Bot(command_prefix="!", intents=intents)
tree = client.tree

@client.event
async def on_ready():
    try:
        guild = discord.Object(id=GUILD_ID)
        await tree.sync(guild=guild)
        logger.info(f"🔁 Slash commands synced to guild {GUILD_ID}")
    except Exception as e:
        logger.warning(f"Guild sync failed: {e}, attempting global sync.")
        await tree.sync()
        logger.info("🔁 Slash commands synced globally")

    logger.info(f"✅ Logged in as {client.user} (ID: {client.user.id})")

@tree.command(name="predict", description="Predict the result of a match", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(home_team="Home team name", away_team="Away team name")
async def predict(interaction: discord.Interaction, home_team: str, away_team: str):
    await interaction.response.defer()
    logger.info(f"Predicting: {home_team} vs {away_team}")
    try:
        prediction = predict_match(home_team, away_team)
        if prediction is None:
            await interaction.followup.send("❌ Could not make a prediction for this match.")
            return

        home_prob, draw_prob, away_prob = prediction
        response = (
            f"📊 **EdgePlay AI Prediction for {home_team} vs {away_team}:**\n"
            f"🏠 {home_team} Win: {home_prob:.2f}%\n"
            f"🤝 Draw: {draw_prob:.2f}%\n"
            f"🚀 {away_team} Win: {away_prob:.2f}%"
        )
        await interaction.followup.send(response)
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        await interaction.followup.send("⚠️ There was an error while making the prediction.")

@tree.command(name="teams", description="List all available teams", guild=discord.Object(id=GUILD_ID))
async def teams(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        teams_list = get_all_teams()
        teams_str = ", ".join(teams_list[:50]) + "..."
        await interaction.followup.send(f"📋 Available teams (partial list):\n{teams_str}")
    except Exception as e:
        logger.error(f"Teams command error: {e}")
        await interaction.followup.send("⚠️ Failed to retrieve teams.")

@tree.command(name="upcoming", description="Show upcoming Premier League matches", guild=discord.Object(id=GUILD_ID))
async def upcoming(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        matches = get_upcoming_matches()
        if not matches:
            await interaction.followup.send("📭 No upcoming matches found.")
            return

        message = "📅 Upcoming Premier League Matches:\n"
        for match in matches:
            message += f"• {match['home_team']} vs {match['away_team']} - {match['date']}\n"
        await interaction.followup.send(message)
    except Exception as e:
        logger.error(f"Upcoming matches error: {e}")
        await interaction.followup.send("⚠️ Failed to retrieve upcoming matches.")

# Run the bot
client.run(DISCORD_TOKEN)
