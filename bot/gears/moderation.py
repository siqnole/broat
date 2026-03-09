import stoat
from stoat.ext import commands

from bot import style


class Moderation(commands.Gear):
    """Moderation commands for server management."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command()
    async def kick(self, ctx: commands.Context, member: stoat.Member, *, reason: str = None) -> None:
        """kick a member"""
        try:
            await member.kick()
            msg = f"{style.yes_emoji()} kicked {member.name}"
            if reason:
                msg += f" — {reason}"
            await ctx.send(msg)
        except Exception as exc:
            await ctx.send(f"{style.no_emoji()} failed: {exc}")

    @commands.command()
    async def ban(self, ctx: commands.Context, member: stoat.Member, *, reason: str = None) -> None:
        """ban a member"""
        try:
            await member.ban(reason=reason)
            msg = f"{style.yes_emoji()} banned {member.name}"
            if reason:
                msg += f" — {reason}"
            await ctx.send(msg)
        except Exception as exc:
            await ctx.send(f"{style.no_emoji()} failed: {exc}")

    @commands.command()
    async def purge(self, ctx: commands.Context, count: int = 10) -> None:
        """delete last n messages (max 100)"""
        count = min(max(count, 1), 100)
        try:
            messages = await ctx.channel.history(limit=count)
            ids = [m.id for m in messages]
            if ids:
                await ctx.channel.delete_messages(ids)
                await ctx.send(f"{style.yes_emoji()} deleted {len(ids)} messages")
        except Exception as exc:
            await ctx.send(f"{style.no_emoji()} failed: {exc}")
