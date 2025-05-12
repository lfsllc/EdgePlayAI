import os
import discord
from discord.ext import commands
import requests
import logging

# ✅ Logging config
logging.basicConfig(level=logging.INFO)

# ✅ Use your actual API key here (can switch back to env later)
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
ODDS_API_KEY = "e30a14f36b81cb121cc46c4fdf5adf47"

FASTAPI_URL = "https://edgeplay-ai.onrender.com/predict"

# ✅ Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    logging.info(f"✅ Bot is online as {bot.user}")

# ✅ Match odds fetcher
def fetch_match_odds(team1, team2):
    url = f"https://api.the-odds-api.com/v4/sports/soccer_epl/odds/?regions=us&markets=h2h&apiKey={ODDS_API_KEY}"
    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()

        for match in data:
            home = match.get("home_team", "").lower()
            away = match.get("away_team", "").lower()

            if team1.lower() in home and team2.lower() in away or \
               team1.lower() in away and team2.lower() in home:

                outcomes = match["bookmakers"][0]["markets"][0]["outcomes"]
                odds_dict = {o["name"].lower(): o["price"] for o in outcomes}

                return [
                    odds_dict.get(home),
                    odds_dict.get("draw"),
                    odds_dict.get(away)
                ]
    except Exception as e:
        logging.error(f"❌ Error fetching odds: {e}")

    return None

# ✅ Predict command
@bot.command()
async def predict(ctx, *, message: str):
    logging.info(f"📥 Raw predict input: {message}")
    
    try:
        parts = message.lower().split(" vs ")
        if len(parts) != 2:
            await ctx.send("⚠️ Please use the format: `!predict TeamA vs TeamB`")
            return

        team1 = parts[0].strip()
        team2 = parts[1].strip()
    except Exception as e:
        await ctx.send("⚠️ Invalid input format.")
        logging.error(f"❌ Input parse error: {e}")
        return

    odds = fetch_match_odds(team1, team2)

    if not odds or None in odds:
        await ctx.send("⚠️ Could not fetch odds. Try again later or check the team names.")
        return

    try:
        response = requests.post(FASTAPI_URL, json={
            "odds_home": odds[0],
            "odds_draw": odds[1],
            "odds_away": odds[2]
        })

        if response.status_code != 200:
            await ctx.send("⚠️ API error. Please try again later.")
            return

        data = response.json()
        await ctx.send(
            f"📊 **EdgePlay AI Prediction** for `{team1.title()}` vs `{team2.title()}`:\n"
            f"🏠 {team1.title()} Win: `{data['Home Win Probability']}%`\n"
            f"🤝 Draw: `{data['Draw Probability']}%`\n"
            f"🚀 {team2.title()} Win: `{data['Away Win Probability']}%`"
        )

    except Exception as e:
        await ctx.send(f"❌ Prediction error: {e}")
        logging.error(f"❌ Prediction error: {e}")

# ✅ Upcoming command (fixed)
@bot.command()
async def upcoming(ctx):
    logging.info("📢 !upcoming command triggered")
    logging.info("🧪 Using hardcoded key: e30a14f36b81cb121cc46c4fdf5adf47")

    url = f"https://api.the-odds-api.com/v4/sports/soccer_epl/odds/?regions=us&markets=h2h&apiKey={ODDS_API_KEY}"
    try:
        logging.info(f"🔍 Sending request to: {url}")
        res = requests.get(url)

        logging.info(f"🔁 Status code: {res.status_code}")
        logging.info(f"📄 Response preview: {res.text[:300]}")

        if res.status_code != 200:
            await ctx.send("⚠️ Failed to fetch match list. Check logs for details.")
            return

        data = res.json()
        logging.info("✅ JSON decoded")

        if not data:
            await ctx.send("❌ No upcoming EPL matches found.")
            return

        message = "**🗓 Upcoming EPL Matches:**\n"
        for match in data[:10]:
            home = match["home_team"]
            away = match["away_team"]
            message += f"- {home} vs {away}\n"

        await ctx.send(message)
        logging.info("✅ Match list sent to Discord")

    except Exception as e:
        logging.error(f"❌ Exception in upcoming command: {e}")
        await ctx.send("⚠️ Exception occurred when fetching match list.")

# ✅ Ping command
@bot.command()
async def ping(ctx):
    await ctx.send("✅ Bot is alive.")

# ✅ Launch bot
bot.run(BOT_TOKEN)
