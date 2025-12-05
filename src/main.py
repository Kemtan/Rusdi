from discord.ext import commands
import discord
import github
import config
import utils
import jomok

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

utils.setup(bot)

@bot.command(name="events")
async def ghevents(ctx, username: str | None = None):
    if username is None:
        await ctx.send("no user specified. please run `!events [user]`")
        return

    events = await github.check_new_events(username)

    if not events:
        await ctx.send(f"No new events for **{username}**.")
        return

    for ev in events:
        await ctx.send(ev["text"])

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print(config.CHANNEL_ID)
    print(config.GITHUB_OWNER)
    print(config.GITHUB_REPO)

@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return
    
    if bot.user in message.mentions:
        raw = message.content
        clean = raw.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()

        response = jomok.responJomok(raw)
        await message.reply(response)
    await bot.process_commands(message)

bot.run(config.DISCORD_TOKEN)