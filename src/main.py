from discord.ext import commands, tasks
import discord
import github
import config
import utils
import jomok
import wavelink
import reddit

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

# --- Reddit background loop ---
@tasks.loop(seconds=60)
async def reddit_loop():
    channel = getattr(bot, "reddit_channel", None)
    if channel is None:
        print("[reddit_loop] reddit_channel is None")
        return

    for username in config.REDDIT_USERNAMES:
        new_posts = reddit.check_new_posts(
            config.REDDIT_SUBREDDIT,
            username,
            limit=1,
        )

        if new_posts:  
            print(f"[reddit_loop] {username}: {len(new_posts)} new posts")

        for p in new_posts:
            msg = (
                f"New post by **u/{p['author']}** in r/{config.REDDIT_SUBREDDIT}\n"
                f"{p['url']}"
            )
            await channel.send(msg)

@reddit_loop.before_loop
async def before_reddit_loop():
    await bot.wait_until_ready()

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

    # fetch reddit channel
    try:
        bot.reddit_channel = await bot.fetch_channel(config.REDDIT_CHANNEL_ID)
    except Exception as e:
        print("[reddit_loop] cannot fetch channel:", e)
        bot.reddit_channel = None

    # start background task
    if not reddit_loop.is_running():
        reddit_loop.start()

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