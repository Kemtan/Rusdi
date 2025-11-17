from discord.ext import commands
from discord.ext import tasks
import discord
import github
import config
import utils

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

utils.setup(bot)

@tasks.loop(minutes=2)
async def check_github():
    result = await github.check_new_commit()
    if result:
        old_sha, new_sha = result
        channel = bot.get_channel(config.CHANNEL_ID)
        await channel.send(f"New commit!\nOld: `{old_sha}`\nNew: `{new_sha}`")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print(config.GITHUB_OWNER)
    print(config.GITHUB_REPO)
    check_github.start()

bot.run(config.DISCORD_TOKEN)