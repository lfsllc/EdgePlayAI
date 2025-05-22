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
    
    # Get unique teams for debugging
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
    """Normalize team name using the mapping"""
    team_name_lower = team_name.strip().lower()
    if team_name_lower in team_aliases:
        return team_aliases[team_name_lower]
    return team_name.strip()

def engineer_features(home_team, away_team, elo_ratings):
    """Create the features required by the model for a given match"""
    try:
        # Check if teams exist in ELO ratings
        if len(elo_ratings[elo_ratings["Club"] == home_team]) == 0:
            print(f"❌ Team not found in ELO ratings: {home_team}")
            return None
            
        if len(elo_ratings[elo_ratings["Club"] == away_team]) == 0:
            print(f"❌ Team not found in ELO ratings: {away_team}")
            return None
        
        # Get ELO ratings - using correct column names (case sensitive)
        home_elo = elo_ratings[elo_ratings["Club"] == home_team]["Elo"].values[0]
        away_elo = elo_ratings[elo_ratings["Club"] == away_team]["Elo"].values[0]
        home_rank = elo_ratings[elo_ratings["Club"] == home_team]["Rank"].values[0]
        away_rank = elo_ratings[elo_ratings["Club"] == away_team]["Rank"].values[0]
        
        # Create the features dictionary with default values
        features = {
            "elo_diff": home_elo - away_elo,
            "form_diff": 0,  # Default value
            "goal_diff": 0,  # Default value
            "rank_diff": away_rank - home_rank,
            "momentum_diff": 0,  # Default value
            "home_away_split_diff": 0,  # Default value
            "h2h_home_wins_last3": 0,  # Default value
            "h2h_away_wins_last3": 0,  # Default value
            "h2h_goal_diff_last3": 0,  # Default value
            "draw_rate_last5": 0,  # Default value
            "avg_goal_diff_last5": 0,  # Default value
            "days_since_last_match": 3,  # Default value
            "fixture_density_flag": 0  # Default value
        }
        
        # Create a DataFrame with the engineered features
        features_df = pd.DataFrame([features])
        return features_df
        
    except Exception as e:
        print(f"❌ Error engineering features: {e}")
        import traceback
        traceback.print_exc()
        return None

def predict_match(home_team, away_team, model, elo_ratings, team_aliases):
    """Predict match outcome using the loaded model and engineered features"""
    # Normalize team names
    home_team = normalize_team_name(home_team, team_aliases)
    away_team = normalize_team_name(away_team, team_aliases)
    
    print(f"Looking for match: {home_team} vs {away_team}")
    
    # Engineer the features required by the model
    features = engineer_features(home_team, away_team, elo_ratings)
    
    if features is None:
        print(f"❌ Failed to engineer features for {home_team} vs {away_team}")
        return None
    
    try:
        # Make prediction
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
        # Return mock data as fallback
        return {
            'home_team': home_team,
            'away_team': away_team,
            'home_win': 50.0,
            'draw': 25.0,
            'away_win': 25.0
        }

# === Predict command ===
@tree.command(name="predict", description="Predict the outcome of a match")
@app_commands.describe(match="Enter match like: Arsenal vs Chelsea")
async def predict(interaction: discord.Interaction, match: str):
    # Respond immediately to prevent timeout
    await interaction.response.defer(thinking=True)
    
    try:
        # Check if resources are loaded
        if model is None or elo_ratings is None or team_aliases is None:
            await interaction.followup.send("⚠️ Bot resources are not loaded. Please try again later.")
            return
            
        # Process the prediction
        try:
            home, away = [team.strip() for team in match.split("vs")]
        except ValueError:
            await interaction.followup.send("⚠️ Invalid format. Please use: Team1 vs Team2")
            return
            
        prediction = predict_match(home, away, model, elo_ratings, team_aliases)

        if prediction is None:
            # Get available teams similar to the ones requested
            available_teams = sorted(elo_ratings['Club'].unique())
            
            # Find similar teams for suggestions
            home_normalized = normalize_team_name(home, team_aliases)
            away_normalized = normalize_team_name(away, team_aliases)
            
            # Provide helpful error message with suggestions
            await interaction.followup.send(
               print(f"⚠️ Match not found in dataset. Could not find teams: {home_team} vs {away_team}")

"
                f"Try using the exact team names as they appear in the dataset. For example:
"
                f"- Use `Man United` instead of `Manchester United`
"
                f"- Use `Man City` instead of `Manchester City`
"
                f"- Use `Ath Madrid` instead of `Atletico Madrid`
"
                f"- Use `Milan` instead of `AC Milan`

"
                f"Use the `/teams` command to see all available teams."
            )
            return

        msg = (
            f"📊 **EdgePlay AI Prediction for {prediction['home_team']} vs {prediction['away_team']}:**
"
            f"🏠 {prediction['home_team']} Win: {prediction['home_win']}%
"
            f"🤝 Draw: {prediction['draw']}%
"
            f"🚀 {prediction['away_team']} Win: {prediction['away_win']}%"
        )
        await interaction.followup.send(msg)

    except Exception as e:
        await interaction.followup.send("⚠️ Internal error. Please try again later.")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

# === Teams command to show available teams ===
@tree.command(name="teams", description="Show available teams for prediction")
async def teams(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    
    try:
        if elo_ratings is None:
            await interaction.followup.send("⚠️ Bot resources are not loaded. Please try again later.")
            return
            
        unique_teams = sorted(elo_ratings['Club'].unique())
        
        # Split into chunks to avoid message length limits
        chunks = [unique_teams[i:i+20] for i in range(0, len(unique_teams), 20)]
        
        await interaction.followup.send("**Available teams for prediction:**")
        for i, chunk in enumerate(chunks):
            await interaction.followup.send(f"**Team List {i+1}:**
" + "
".join(chunk))
            
    except Exception as e:
        await interaction.followup.send("⚠️ Internal error. Please try again later.")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

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
    try:
        bot.run(token)
    except Exception as e:
        print(f"❌ Bot crashed: {e}")
        import traceback
        traceback.print_exc()
