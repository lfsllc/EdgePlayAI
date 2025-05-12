import os
import discord
from discord.ext import commands
import requests

# ✅ Load token from environment variable
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# ✅ Your FastAPI endpoint on Render
FASTAPI_URL = "https://edgeplay-ai.onrender.com/predict"

# ✅ Enable message content (needed for reading commands)
intents = discord.Intents.default()
intents.message_content = True

# ✅ Set up command prefix
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")

@bot.command()
async def predict(ctx, odds_home: float, odds_draw: float, odds_away: float):
    try:
        # Send request to your FastAPI
        response = requests.post(FASTAPI_URL, json={
            "odds_home": odds_home,
            "odds_draw": odds_draw,
            "odds_away": odds_away
        })

        if response.status_code != 200:
            await ctx.send("⚠️ API error. Please try again later.")
            return

        data = response.json()

        # Check if expected keys are present
        if all(k in data for k in ["Home Win Probability", "Draw Probability", "Away Win Probability"]):
            await ctx.send(
                f"📊 **EdgePlay AI Prediction**\n"
                f"🏠 Home Win: `{data['Home Win Probability']}%`\n"
                f"🤝 Draw: `{data['Draw Probability']}%`\n"
                f"🚀 Away Win: `{data['Away Win Probability']}%`"
            )
        else:
            await ctx.send("⚠️ Unexpected response from API.")

    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

# ✅ Start the bot
bot.run(BOT_TOKEN)

