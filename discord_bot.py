import os
import discord
from discord.ext import commands
import requests

BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
ODDS_API_KEY = os.getenv("98bd0e4fb6c1fc1647c66e7b1c3bc083")
FASTAPI_URL = "https://edgeplay-ai.onrender.com/predict"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")

def fetch_match_odds(team1, team2):
    url = f"https://api.the-odds-api.com/v4/sports/soccer_epl/odds/?regions=us&markets=h2h&apiKey={ODDS_API_KEY}"
    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()

        for match in data:
            teams = match.get("teams", [])
            lower_teams = [t.lower() for t in teams]

            if any(team1.lower() in t for t in lower_teams) and any(team2.lower() in t for t in lower_teams):
                outcomes = match["bookmakers"][0]["markets"][0]["outcomes"]
                odds_dict = {o["name"].lower(): o["price"] for o in outcomes}

                return [
                    odds_dict.get(teams[0].lower()),
                    odds_dict.get("draw"),
                    odds_dict.get(teams[1].lower())
                ]
    except Exception as e:
        print("❌ Error fetching odds:", e)

    return None

@bot.command()
async def predict(ctx, team1: str, team2: str):
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
            f"📊 **EdgePlay AI Prediction** for `{team1}` vs `{team2}`:\n"
            f"🏠 {team1} Win: `{data['Home Win Probability']}%`\n"
            f"🤝 Draw: `{data['Draw Probability']}%`\n"
            f"🚀 {team2} Win: `{data['Away Win Probability']}%`"
        )

    except Exception as e:
        await ctx.send(f"❌ Prediction error: {e}")

@bot.command()
async def upcoming(ctx):
    print("📢 !upcoming command triggered")
    print(f"🧪 ODDS_API_KEY is: {ODDS_API_KEY}")  # <== ADD THIS

    url = f"https://api.the-odds-api.com/v4/sports/soccer_epl/odds/?regions=us&markets=h2h&apiKey={ODDS_API_KEY}"
    ...
    try:
        print(f"🔍 Sending request to: {url}")
        res = requests.get(url)

        print(f"🔁 Status code: {res.status_code}")
        print(f"📄 Response preview: {res.text[:300]}")

        if res.status_code != 200:
            await ctx.send("⚠️ Failed to fetch match list. Check logs for details.")
            return

        data = res.json()
        print("✅ JSON decoded")

        if not data:
            await ctx.send("❌ No upcoming EPL matches found.")
            return

        message = "**🗓 Upcoming EPL Matches:**\n"
        for match in data[:10]:
            home, away = match["teams"]
            message += f"- {home} vs {away}\n"

        await ctx.send(message)
        print("✅ Match list sent to Discord")

    except Exception as e:
        print("❌ Exception in upcoming command:", e)
        await ctx.send("⚠️ Exception occurred when fetching match list.")

@bot.command()
async def ping(ctx):
    await ctx.send("✅ Bot is alive.")

bot.run(BOT_TOKEN)
