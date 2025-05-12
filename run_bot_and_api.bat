@echo off
echo Starting FastAPI server...
start cmd /k "cd /d C:\Users\usago\OneDrive\Desktop\discord-soccer-bot && uvicorn api.main:app --reload"

timeout /t 5

echo Starting Discord bot...
start cmd /k "cd /d C:\Users\usago\OneDrive\Desktop\discord-soccer-bot && py -3.10 discord_bot.py"

exit
