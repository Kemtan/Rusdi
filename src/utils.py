from discord.ext import commands

def setup(bot):
    #!test
    @bot.command()
    async def test(ctx):
        await ctx.send("Bot running.")

    #!ping
    @bot.command()
    async def ping(ctx):
        latency = round(bot.latency * 1000)
        await ctx.send(f"pong ({latency} ms)")