import discord
from discord.ext import commands
import wavelink


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queues = {}

    async def _get_player(self, ctx: commands.Context) -> wavelink.Player:
        """Get or create a Wavelink player for this guild."""
        if ctx.voice_client and isinstance(ctx.voice_client, wavelink.Player):
            return ctx.voice_client

        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError("You have to be in a voice channel.")

        channel: discord.VoiceChannel = ctx.author.voice.channel
        player: wavelink.Player = await channel.connect(cls=wavelink.Player)
        return player

    @commands.command(name="join")
    async def join(self, ctx: commands.Context):
        """Join your voice channel."""
        player = await self._get_player(ctx)
        await ctx.send(f"Joined {player.channel.mention}")

    @commands.command(name="play")
    async def play(self, ctx: commands.Context, *, query: str):
        """Play a song from a query or URL."""
        player = await self._get_player(ctx)

        # search tracks (default: YouTube)
        tracks: wavelink.Search = await wavelink.Playable.search(query)
        if not tracks:
            return await ctx.send("No results found.")

        track = tracks[0]

        # init queue for this guild
        queue = self.queues.setdefault(ctx.guild.id, [])

        if not player.playing:
            await player.play(track)
            await ctx.send(f"▶️ Now playing: **{track.title}**")
        else:
            queue.append(track)
            await ctx.send(f"➕ Added to queue: **{track.title}**")

    @commands.command(name="pause")
    async def pause(self, ctx: commands.Context):
        player: wavelink.Player = ctx.voice_client  # type: ignore
        if not player:
            return await ctx.send("Not connected.")

        await player.pause(True)
        await ctx.send("⏸ Paused.")

    @commands.command(name="resume")
    async def resume(self, ctx: commands.Context):
        player: wavelink.Player = ctx.voice_client  # type: ignore
        if not player:
            return await ctx.send("Not connected.")

        await player.pause(False)
        await ctx.send("▶️ Resumed.")

    @commands.command(name="stop")
    async def stop(self, ctx: commands.Context):
        """Stop playback and clear the player."""
        player: wavelink.Player = ctx.voice_client  # type: ignore
        if not player:
            return await ctx.send("Not connected.")

        await player.stop()
        await ctx.send("⏹️ Stopped playback.")

    @commands.command(name="skip")
    async def skip(self, ctx):
        player: wavelink.Player = ctx.voice_client

        if not player or not isinstance(player, wavelink.Player):
            return await ctx.send("Not connected.")

        if not player.playing:
            return await ctx.send("Nothing is playing.")

        await player.stop()  # triggers next song from queue
        await ctx.send("⏭️ Skipped.")

    @commands.command(name="leave")
    async def leave(self, ctx: commands.Context):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("👋 Left the voice channel.")
        else:
            await ctx.send("I'm not in a voice channel.")

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload):
        guild_id = payload.player.guild.id

        queue = self.queues.get(guild_id)
        if queue and len(queue) > 0:
            next_track = queue.pop(0)
            await payload.player.play(next_track)
            channel = payload.player.channel
            text = channel.guild.text_channels[0]
            await text.send(f"▶️ Now playing: **{next_track.title}**")

    @commands.command(name="queue")
    async def show_queue(self, ctx):
        queue = self.queues.get(ctx.guild.id, [])
        if not queue:
            return await ctx.send("Queue is empty.")

        msg = "\n".join(f"{i+1}. {t.title}" for i, t in enumerate(queue))
        await ctx.send(f"📜 **Queue:**\n{msg}")

async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
