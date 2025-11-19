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

@tasks.loop(minutes=1)
async def check_github():
    result = await github.check_new_commit()

    # cached channel
    channel = bot.get_channel(config.CHANNEL_ID)

    # fetch channel
    if channel is None:
        try:
            channel = await bot.fetch_channel(config.CHANNEL_ID)
            # print("Fetched channel from API:", channel, type(channel))
        except discord.Forbidden:
            print("ERROR: Bot has no permission to view/send in this channel")
            return
        except discord.HTTPException as e:
            print("ERROR: Failed to fetch channel:", e)
            return

    if result:
        await channel.send(
            f"**New commit detected!**\n"
            f"SHA: `{result['sha']}`\n"
            f"Committer: **{result['committer']}**\n"
            f"Message: {result['message']}\n"
            f"Time (WIB): {result['time_wib']}"
        )
    # else:
    #     await channel.send("no commit")

@bot.command(name="events")
async def ghevents(ctx):
    events = await github.check_new_events(config.GITHUB_USER)

    if not events:
        await ctx.send("No new events since last check.")
        return

    for ev in events:
        await ctx.send(ev["text"])

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print(config.CHANNEL_ID)
    print(config.GITHUB_OWNER)
    print(config.GITHUB_REPO)
    check_github.start()

bot.run(config.DISCORD_TOKEN)