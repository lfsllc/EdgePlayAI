import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import logging

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EdgePlayAI")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

@tree.command(name="ping", description="Check bot status")
async def ping(interaction: discord.Interaction):
    logger.info("Received /ping command")
    await interaction.response.send_message("🏓 Pong! Bot is alive and well.")

@bot.event
async def on_ready():
    logger.info(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await tree.sync()
        logger.info(f"🔁 Synced {len(synced)} command(s): {[cmd.name for cmd in synced]}")
    except Exception as e:
        logger.error("❌ Failed to sync commands", exc_info=True)

# Run bot
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    logger.critical("❌ DISCORD_TOKEN is missing from environment")
else:
    try:
        bot.run(TOKEN)
    except Exception as e:
        logger.critical("❌ Bot crashed during startup", exc_info=True)
