from discord.ext import commands
import discord
import config
import utils

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

utils.setup(bot)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

bot.run(config.DISCORD_TOKEN)