import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv
from predict_engine import predict_match, get_all_teams, get_upcoming_matches

load_dotenv()
print("DEBUG - DISCORD_BOT_TOKEN:", os.getenv("DISCORD_BOT_TOKEN"))


TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        guild = discord.Object(id=GUILD_ID)
        await tree.sync(guild=guild)
        print(f"🌍 Slash commands synced to guild {GUILD_ID}")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

@tree.command(name="predict", description="🔮 Predict match outcome and BTTS (both teams to score)", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(match="Format: Team A vs Team B")
async def predict(interaction: discord.Interaction, match: str):
    await interaction.response.defer()
    try:
        predictions = predict_match(match)
        if predictions is None:
            await interaction.followup.send("❌ Could not make a prediction for this match.")
            return

        home, draw, away = predictions["1X2"]
        btts = predictions["BTTS"]

        result_lines = []
        result_lines.append(f"📊 **Predicción para {match}:**")
        result_lines.append(f"🏠 {match.split(' vs ')[0]} gana: `{home:.2f}%`")
        result_lines.append(f"🤝 Empate: `{draw:.2f}%`")
        result_lines.append(f"🚀 {match.split(' vs ')[1]} gana: `{away:.2f}%`")
        result_lines.append("")
        result_lines.append("🔥 **¿Ambos equipos marcan?**")
        result_lines.append("✅ *Sí*" if btts else "❌ *No*")

        await interaction.followup.send("\n".join(result_lines))
    except Exception as e:
        await interaction.followup.send(f"⚠️ Error processing prediction: {e}")

@tree.command(name="teams", description="📋 Show all available teams", guild=discord.Object(id=GUILD_ID))
async def teams(interaction: discord.Interaction):
    try:
        all_teams = get_all_teams()
        team_list = ", ".join(all_teams[:50])  # Show only first 50 for brevity
        await interaction.response.send_message(f"⚽ Equipos disponibles:\n{team_list}...")
    except Exception as e:
        await interaction.response.send_message(f"⚠️ Error fetching teams: {e}")

@tree.command(name="upcoming", description="📅 Show upcoming matches", guild=discord.Object(id=GUILD_ID))
async def upcoming(interaction: discord.Interaction):
    try:
        matches = get_upcoming_matches()
        if not matches:
            await interaction.response.send_message("❌ No upcoming matches found.")
            return
        msg = "**🔜 Próximos partidos:**\n" + "\n".join(matches[:10])
        await interaction.response.send_message(msg)
    except Exception as e:
        await interaction.response.send_message(f"⚠️ Error fetching upcoming matches: {e}")

print(f"TOKEN is: {TOKEN}")

bot.run(TOKEN)