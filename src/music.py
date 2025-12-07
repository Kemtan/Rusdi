import discord
from discord.ext import commands
import wavelink
import random


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queues: dict[int, list[wavelink.Playable]] = {}
        self.text_channels: dict[int, discord.abc.MessageableChannel] = {}

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
        # remember text channel for this guild
        self.text_channels[ctx.guild.id] = ctx.channel
        await ctx.send(f"Joined {player.channel.mention}")

    @commands.command(name="play")
    async def play(self, ctx: commands.Context, *, query: str):
        """Play a song from a query or URL."""
        player = await self._get_player(ctx)

        # remember where to talk for this guild
        self.text_channels[ctx.guild.id] = ctx.channel

        # search tracks (default: YouTube)
        tracks: wavelink.Search = await wavelink.Playable.search(query)
        if not tracks:
            return await ctx.send("No results found.")

        track = tracks[0]

        # init queue for this guild
        queue = self.queues.setdefault(ctx.guild.id, [])

        if not player.playing:
            await player.play(track)
            await ctx.send(f"▶ Now playing: **{track.title}**")
        else:
            queue.append(track)
            await ctx.send(f"+ Added to queue: **{track.title}**")

    @commands.command(name="pause")
    async def pause(self, ctx: commands.Context):
        """Pause the current song."""
        player: wavelink.Player = ctx.voice_client  # type: ignore
        if not player:
            return await ctx.send("Not connected.")

        await player.pause(True)
        await ctx.send("⏸ Paused.")

    @commands.command(name="resume")
    async def resume(self, ctx: commands.Context):
        """Resume playback."""
        player: wavelink.Player = ctx.voice_client  # type: ignore
        if not player:
            return await ctx.send("Not connected.")

        await player.pause(False)
        await ctx.send("▶ Resumed.")

    @commands.command(name="stop")
    async def stop(self, ctx: commands.Context):
        """Stop playback and clear the player."""
        player: wavelink.Player = ctx.voice_client  # type: ignore
        if not player:
            return await ctx.send("Not connected.")

        await player.stop()
        await ctx.send("⏹ Stopped playback.")

    @commands.command(name="skip")
    async def skip(self, ctx: commands.Context):
        """Skip the current song."""
        player: wavelink.Player = ctx.voice_client

        if not player or not isinstance(player, wavelink.Player):
            return await ctx.send("Not connected.")

        if not player.playing:
            return await ctx.send("Nothing is playing.")

        await player.stop()  # triggers next song from queue
        await ctx.send("⏭ Skipped.")

    @commands.command(name="leave")
    async def leave(self, ctx: commands.Context):
        """"Leave the voice channel."""
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("👋 Left the voice channel.")
        else:
            await ctx.send("I'm not in a voice channel.")

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload):
        """Auto-play next track from queue when current ends."""
        guild = payload.player.guild
        guild_id = guild.id

        queue = self.queues.get(guild_id)
        if queue and len(queue) > 0:
            next_track = queue.pop(0)
            await payload.player.play(next_track)

            # use the last text channel used for this guild, fallback to first text channel
            text = self.text_channels.get(guild_id)
            if text is None:
                text_channels = guild.text_channels
                if not text_channels:
                    return  # nowhere to send
                text = text_channels[0]

            await text.send(f"▶ Now playing: **{next_track.title}**")

    @commands.command(name="queue")
    async def show_queue(self, ctx: commands.Context):
        """Show the current queue."""
        queue = self.queues.get(ctx.guild.id, [])
        if not queue:
            return await ctx.send("Queue is empty.")

        msg = "\n".join(f"{i+1}. {t.title}" for i, t in enumerate(queue))
        await ctx.send(f"📜 **Queue:**\n{msg}")

    @commands.command(name="nowplaying", aliases=["np"])
    async def nowplaying(self, ctx: commands.Context):
        """Show the currently playing song."""
        player: wavelink.Player = ctx.voice_client

        if not player or not isinstance(player, wavelink.Player):
            return await ctx.send("Not connected.")

        if not player.current:
            return await ctx.send("Nothing is playing.")

        track = player.current
        await ctx.send(f"🎵 **Now playing:** {track.title}")

    @commands.command(name="shuffle")
    async def shuffle_queue(self, ctx: commands.Context):
        """Shuffle the queue."""
        queue = self.queues.get(ctx.guild.id, [])

        if not queue:
            return await ctx.send("Queue is empty.")

        random.shuffle(queue)
        await ctx.send("🔀 Queue shuffled.")

    @commands.command(name="remove")
    async def remove_track(self, ctx: commands.Context, index: int):
        """Remove a song from the queue."""
        queue = self.queues.get(ctx.guild.id, [])

        if not queue:
            return await ctx.send("Queue is empty.")

        index -= 1  # 1-based -> 0-based

        if index < 0 or index >= len(queue):
            return await ctx.send("Invalid index.")

        removed = queue.pop(index)
        await ctx.send(f"🗑️ Removed: **{removed.title}**")

async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
