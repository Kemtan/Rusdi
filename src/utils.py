from discord.ext import commands
import time
from discord.utils import utcnow

def setup(bot):
    #!test
    @bot.command()
    async def test(ctx):
        await ctx.send("Bot running.")

    #!ping
    @bot.command()
    async def ping(ctx):
        before = utcnow()
        msg = await ctx.send("pong...")
        after = utcnow()
        ms = int((after - before).total_seconds() * 1000)
        await msg.edit(content=f"pong ({ms} ms)")