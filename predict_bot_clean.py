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

# === Load environment variables ===
load_dotenv()

# === Initialize resources at startup ===
print("Loading model and data...")
model = None
elo_ratings = None
team_aliases = None

try:
    start_time = time.time()
    model = joblib.load("model.pkl")
    print(f"Model loaded in {time.time() - start_time:.2f} seconds")

    start_time = time.time()
    elo_ratings = pd.read_csv("data/clubelo_ratings.csv")
    print(f"ELO ratings loaded in {time.time() - start_time:.2f} seconds")
    print(f"✅ ELO ratings shape: {elo_ratings.shape}")

    unique_teams = sorted(elo_ratings['Club'].unique())
    print(f"✅ Found {len(unique_teams)} unique teams in ELO ratings")
    print(f"Sample teams: {unique_teams[:10]}")

    start_time = time.time()
    with open("data/club_name_mapping.json", "r", encoding="utf-8") as f:
        team_aliases = {k.lower(): v for k, v in json.load(f).items()}
    print(f"Team aliases loaded in {time.time() - start_time:.2f} seconds")
    print(f"✅ Loaded {len(team_aliases)} team aliases")

    print("✅ Resources loaded successfully")
except Exception as e:
    print(f"❌ Failed to load resources: {e}")
    import traceback
    traceback.print_exc()

# === Initialize bot ===
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

def normalize_team_name(team_name, team_aliases):
    team_name_lower = team_name.strip().lower()
    return team_aliases.get(team_name_lower, team_name.strip())

def engineer_features(home_team, away_team, elo_ratings):
    try:
        if len(elo_ratings[elo_ratings["Club"] == home_team]) == 0:
            print(f"❌ Team not found in ELO ratings: {home_team}")
            return None

        if len(elo_ratings[elo_ratings["Club"] == away_team]) == 0:
            print(f"❌ Team not found in ELO ratings: {away_team}")
            return None

        home_elo = elo_ratings[elo_ratings["Club"] == home_team]["Elo"].values[0]
        away_elo = elo_ratings[elo_ratings["Club"] == away_team]["Elo"].values[0]
        home_rank = elo_ratings[elo_ratings["Club"] == home_team]["Rank"].values[0]
        away_rank = elo_ratings[elo_ratings["Club"] == away_team]["Rank"].values[0]

        features = {
            "elo_diff": home_elo - away_elo,
            "form_diff": 0,
            "goal_diff": 0,
            "rank_diff": away_rank - home_rank,
            "momentum_diff": 0,
            "home_away_split_diff": 0,
            "h2h_home_wins_last3": 0,
            "h2h_away_wins_last3": 0,
            "h2h_goal_diff_last3": 0,
            "draw_rate_last5": 0,
            "avg_goal_diff_last5": 0,
            "days_since_last_match": 3,
            "fixture_density_flag": 0
        }

        return pd.DataFrame([features])
    except Exception as e:
        print(f"❌ Error engineering features: {e}")
        import traceback
        traceback.print_exc()
        return None

def predict_match(home_team, away_team, model, elo_ratings, team_aliases):
    home_team = normalize_team_name(home_team, team_aliases)
    away_team = normalize_team_name(away_team, team_aliases)

    print(f"Looking for match: {home_team} vs {away_team}")
    features = engineer_features(home_team, away_team, elo_ratings)

    if features is None:
        print(f"❌ Failed to engineer features for {home_team} vs {away_team}")
        return None

    try:
        prediction = model.predict_proba(features)[0]
        return {
            'home_team': home_team,
            'away_team': away_team,
            'home_win': round(prediction[0] * 100, 2),
            'draw': round(prediction[1] * 100, 2),
            'away_win': round(prediction[2] * 100, 2)
        }
    except Exception as e:
        print(f"❌ Prediction error: {e}")
        import traceback
        traceback.print_exc()
        return {
            'home_team': home_team,
            'away_team': away_team,
            'home_win': 50.0,
            'draw': 25.0,
            'away_win': 25.0
        }

@tree.command(name="predict", description="Predict the outcome of a match")
@app_commands.describe(match="Enter match like: Arsenal vs Chelsea")
async def predict(interaction: discord.Interaction, match: str):
    await interaction.response.defer(thinking=True)

    try:
        if model is None or elo_ratings is None or team_aliases is None:
            await interaction.followup.send("⚠️ Bot resources are not loaded. Please try again later.")
            return

        try:
            home, away = [team.strip() for team in match.split("vs")]
        except ValueError:
            await interaction.followup.send("⚠️ Invalid format. Please use: Team1 vs Team2")
            return

        prediction = predict_match(home, away, model, elo_ratings, team_aliases)

        if prediction is None:
            home_normalized = normalize_team_name(home, team_aliases)
            away_normalized = normalize_team_name(away, team_aliases)

            error_msg = (
                f"⚠️ Match not found in dataset. Could not find teams: {home_normalized} vs {away_normalized}\n\n"
                f"Try using the exact team names as they appear in the dataset. For example:\n"
                f"- Use `Man United` instead of `Manchester United`\n"
                f"- Use `Man City` instead of `Manchester City`\n"
                f"- Use `Atletico Madrid` instead of `Atletico de Madrid`\n"
                f"- Use `Milan` instead of `AC Milan`\n\n"
                f"Use the `/teams` command to see all available teams."
            )
            await interaction.followup.send(error_msg)
            return

        msg = (
            f"\U0001F4CA **EdgePlay AI Prediction for {prediction['home_team']} vs {prediction['away_team']}:**\n"
            f"\U0001F3E0 {prediction['home_team']} Win: {prediction['home_win']}%\n"
            f"\U0001F91D Draw: {prediction['draw']}%\n"
            f"\U0001F680 {prediction['away_team']} Win: {prediction['away_win']}%"
        )
        await interaction.followup.send(msg)

    except Exception as e:
        await interaction.followup.send("⚠️ Internal error. Please try again later.")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

@tree.command(name="teams", description="Show available teams for prediction")
async def teams(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    try:
        if elo_ratings is None:
            await interaction.followup.send("⚠️ Bot resources are not loaded. Please try again later.")
            return

        unique_teams = sorted(elo_ratings['Club'].unique())
        chunks = [unique_teams[i:i+20] for i in range(0, len(unique_teams), 20)]

        await interaction.followup.send("**Available teams for prediction:**")
        for i, chunk in enumerate(chunks):
            await interaction.followup.send(f"**Team List {i+1}:**\n" + "\n".join(chunk))

    except Exception as e:
        await interaction.followup.send("⚠️ Internal error. Please try again later.")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

@tree.command(name="upcoming", description="Show upcoming matches with date and time")
async def upcoming(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    try:
        api_key = os.getenv("FOOTBALL_DATA_API_KEY")
        headers = {'X-Auth-Token': api_key}
        url = 'https://api.football-data.org/v2/matches?status=SCHEDULED'

        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            await interaction.followup.send("⚠️ Could not fetch upcoming fixtures.")
            return

        data = response.json()
        matches = data.get("matches", [])

        if not matches:
            await interaction.followup.send("⚠️ No upcoming matches found.")
            return

        message_lines = ["📅 **Upcoming Matches:**"]
        for match in matches[:10]:
            utc_time = datetime.strptime(match["utcDate"], "%Y-%m-%dT%H:%M:%SZ")
            formatted_time = utc_time.strftime("%Y-%m-%d %H:%M UTC")
            home = match["homeTeam"]["name"]
            away = match["awayTeam"]["name"]
            message_lines.append(f"{formatted_time} — {home} vs {away}")

        await interaction.followup.send("\n".join(message_lines))

    except Exception as e:
        await interaction.followup.send("⚠️ Failed to load fixtures.")
        print(f"Error fetching fixtures: {e}")
        import traceback
        traceback.print_exc()

@bot.event
async def on_ready():
    try:
        print(f"✅ Logged in as {bot.user}")
        synced = await tree.sync()
        print(f"🔁 Synced {len(synced)} command(s): {[cmd.name for cmd in synced]}")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")
        import traceback
        traceback.print_exc()


# === Run bot with token ===
token = os.getenv("DISCORD_TOKEN")
if not token:
    print("❌ DISCORD_TOKEN not found in environment or .env file")
else:
    try:
        bot.run(token)
    except Exception as e:
        print(f"❌ Bot crashed: {e}")
        import traceback
        traceback.print_exc()
