import discord
from discord.ext import commands
import requests

# Your FastAPI server endpoint
FASTAPI_URL = "http://localhost:8000/predict"

# Your actual bot token
BOT_TOKEN = "MTM3MDA1OTczODcyOTE1NjczMA.GNkX57.Dc0zO7VZ5LzgGDXHO5iCEz4F4IvopcsMd9gEhs"

# Bot setup
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")

@bot.command()
async def predict(ctx, odds_home: float, odds_draw: float, odds_away: float):
    try:
        payload = {
            "odds_home": odds_home,
            "odds_draw": odds_draw,
            "odds_away": odds_away
        }

        res = requests.post(FASTAPI_URL, json=payload)
        data = res.json()

        message = (
            f"🏟 **Match Prediction**\n"
            f"Home Win: {data['Home Win Probability']}%\n"
            f"Draw: {data['Draw Probability']}%\n"
            f"Away Win: {data['Away Win Probability']}%"
        )

        await ctx.send(message)

    except Exception as e:
        print("❌ ERROR:", e)
        await ctx.send("⚠️ Something went wrong trying to fetch the prediction.")

bot.run(BOT_TOKEN)
