from discord.ext import commands
import discord
import github
import config
import utils
import jomok
import wavelink

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

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

@bot.event
async def setup_hook():
    nodes = [
        wavelink.Node(
            uri="http://127.0.0.1:2333",   # or your Tailscale IP
            password=config.WAVELINK_PASS
        )
    ]

    await wavelink.Pool.connect(nodes=nodes, client=bot)
    await bot.load_extension("music")

@bot.event
async def on_socket_response(msg):
    await wavelink.Pool.on_socket_response(msg)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandError):
        await ctx.send(f"❌ {error}")
    else:
        raise error

bot.run(config.DISCORD_TOKEN)