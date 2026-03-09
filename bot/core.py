import os
import logging

import stoat
from stoat.ext import commands
from stoat import errors as stoat_errors

from bot import style
from bot import database
from bot.gears.general import General
from bot.gears.moderation import Moderation
from bot.gears.fun import Fun
from bot.gears.info import Info
from bot.gears.economy import Economy
from bot.gears.prefix import Prefix

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("bronx")


def _mention_prefix(ctx: commands.Context) -> list[str]:
    """Return the bot-mention prefix strings."""
    me = ctx.bot.me
    if me is None:
        return []
    return [f"<@{me.id}> ", f"<@{me.id}>"]


async def _get_prefix(ctx: commands.Context) -> list[str]:
    """Dynamic prefix resolver.

    Priority:
    1. If the user has personal prefixes, *only* those (+ mention) work for them.
    2. Otherwise, use the server's custom prefixes (+ mention) if any.
    3. Fall back to the default prefix (+ mention).

    Bot mention always works.
    """
    default = os.environ.get("COMMAND_PREFIX", "!")
    mention = _mention_prefix(ctx)
    user_id = str(ctx.author.id)

    # --- user-level prefixes (exclusive) ---
    user_prefixes = await database.get_user_prefixes(user_id)
    if user_prefixes:
        return mention + user_prefixes

    # --- server-level prefixes ---
    if ctx.server is not None:
        server_id = str(ctx.server.id)
        server_prefixes = await database.get_server_prefixes(server_id)
        if server_prefixes:
            return mention + server_prefixes

    # --- default (never empty) ---
    return mention + [default]


class Bronx(commands.Bot):
    """The main bot class for Bronx."""

    def __init__(self) -> None:
        token = os.environ.get("BOT_TOKEN", "")

        if not token:
            raise RuntimeError(
                "BOT_TOKEN environment variable is not set. "
                "Copy .env.example to .env and fill in your bot token."
            )

        super().__init__(command_prefix=_get_prefix, token=token)

    async def on_ready(self, _event, /) -> None:
        log.info("logged in as %s (id: %s)", self.me, self.me.id)
        log.info("default prefix: %s", os.environ.get("COMMAND_PREFIX", "!"))

        if not self.gears:
            await database.ensure_tables()
            await self.add_gear(General(self))
            await self.add_gear(Moderation(self))
            await self.add_gear(Fun(self))
            await self.add_gear(Info(self))
            await self.add_gear(Economy(self))
            await self.add_gear(Prefix(self))
            log.info("all gears loaded")

    async def on_command_error(self, event: commands.CommandErrorEvent, /) -> None:
        """Global error handler for commands."""
        ctx = event.context
        error = event.error

        if isinstance(error, commands.CommandNotFound):
            return

        # Handle CommandInvokeError which wraps other exceptions
        if isinstance(error, commands.CommandInvokeError):
            error = error.original

        # Check if it's a Forbidden error (permissions issue)
        if isinstance(error, stoat_errors.Forbidden):
            log.warning("Missing permissions in channel %s: %s", ctx.channel.id if ctx.channel else "unknown", error)
            return

        if isinstance(error, commands.MissingRequiredArgument):
            try:
                await ctx.send(f"{style.no_emoji()} missing argument. try `{ctx.prefix}help {ctx.command}`")
            except stoat_errors.Forbidden:
                pass
            return

        if isinstance(error, commands.BadArgument):
            try:
                await ctx.send(f"{style.no_emoji()} bad argument: {error}")
            except stoat_errors.Forbidden:
                pass
            return

        if isinstance(error, commands.CommandOnCooldown):
            try:
                await ctx.send(f"{style.warning_emoji()} cooldown. try again in {error.retry_after:.1f}s")
            except stoat_errors.Forbidden:
                pass
            return

        if isinstance(error, commands.CheckFailure):
            try:
                await ctx.send(f"{style.no_emoji()} no permission")
            except stoat_errors.Forbidden:
                pass
            return

        log.exception("Unhandled error in command %s", ctx.command, exc_info=error)
        try:
            await ctx.send(f"{style.no_emoji()} unexpected error occurred")
        except stoat_errors.Forbidden:
            pass
