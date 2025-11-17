import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
intents = discord.Intents.default()
intents.message_content = True   # important

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.lower() == "hello":
        await message.channel.send("world")

    await bot.process_commands(message)

bot.run(os.getenv("DISCORD_TOKEN"))