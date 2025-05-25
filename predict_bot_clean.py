
import discord
from discord.ext import commands
from discord import app_commands
import logging
import os
from predict_engine import predict_match, normalize_team_name

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EdgePlayAI")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

@bot.event
async def on_ready():
    await tree.sync()
    logger.info(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    logger.info(f"🔁 Synced {len(tree.get_commands())} command(s): {[cmd.name for cmd in tree.get_commands()]}")

@tree.command(name="predict", description="Get a match prediction (e.g. /predict Liverpool vs Arsenal)")
@app_commands.describe(home_team="Home team", away_team="Away team")
async def predict(interaction: discord.Interaction, home_team: str, away_team: str):
    await interaction.response.defer(thinking=True)

    prediction, error = predict_match(home_team, away_team)
    if error:
        await interaction.followup.send(error)
        return

    home = normalize_team_name(home_team)
    away = normalize_team_name(away_team)

    home_prob = prediction[0] * 100
    draw_prob = prediction[1] * 100
    away_prob = prediction[2] * 100

    response = (
        f"📊 **EdgePlay AI Prediction for {home} vs {away}:**\n"
        f"🏠 {home} Win: {home_prob:.2f}%\n"
        f"🤝 Draw: {draw_prob:.2f}%\n"
        f"🚀 {away} Win: {away_prob:.2f}%"
    )
    await interaction.followup.send(response)

@tree.command(name="teams", description="List supported teams in the dataset")
async def teams(interaction: discord.Interaction):
    with open("data/club_name_mapping.json", "r", encoding="utf-8") as f:
        import json
        mapping = json.load(f)

    unique_names = sorted(set(mapping.values()))
    chunks = [unique_names[i:i+20] for i in range(0, len(unique_names), 20)]

    await interaction.response.send_message("✅ List of supported team names:")
    for chunk in chunks:
await interaction.followup.send(f"```\n{chr(10).join(chunk)}\n```")

@tree.command(name="upcoming", description="See upcoming Premier League matches")
async def upcoming(interaction: discord.Interaction):
    import requests
    await interaction.response.defer(thinking=True)

    api_key = os.getenv("FOOTBALL_DATA_API_KEY")
    url = "https://api.football-data.org/v4/competitions/PL/matches?status=SCHEDULED"
    headers = {"X-Auth-Token": api_key}

    try:
        response = requests.get(url, headers=headers)
        data = response.json().get("matches", [])

        if not data:
            await interaction.followup.send("⚠️ No upcoming Premier League matches found.")
            return

        matches = []
        for match in data[:10]:
            date = match['utcDate'].replace("T", " ").replace("Z", "")
            matches.append(f"{date} — {match['homeTeam']['name']} vs {match['awayTeam']['name']}")

        await interaction.followup.send("📅 Upcoming Premier League Matches:
" + "\n".join(matches))
    except Exception as e:
        logger.error(f"Failed to fetch upcoming matches: {e}")
        await interaction.followup.send("⚠️ Failed to fetch upcoming matches.")

if __name__ == "__main__":
    bot.run(os.getenv("DISCORD_TOKEN"))
