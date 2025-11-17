from discord.ext import commands

def setup(bot):
    @bot.command()
    async def test(ctx):
        await ctx.send("Bot running.")