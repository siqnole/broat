import os
import logging

import stoat
from stoat.ext import commands
from stoat import errors as stoat_errors

from bot import style
from bot.gears.general import General
from bot.gears.moderation import Moderation
from bot.gears.fun import Fun
from bot.gears.info import Info
from bot.gears.economy import Economy
from bot import database

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("bronx")


class Bronx(commands.Bot):
    """The main bot class for Bronx."""

    def __init__(self) -> None:
        token = os.environ.get("BOT_TOKEN", "")
        prefix = os.environ.get("COMMAND_PREFIX", "!")

        if not token:
            raise RuntimeError(
                "BOT_TOKEN environment variable is not set. "
                "Copy .env.example to .env and fill in your bot token."
            )

        super().__init__(command_prefix=prefix, token=token)

    async def on_ready(self, _event, /) -> None:
        log.info("logged in as %s (id: %s)", self.me, self.me.id)
        log.info("prefix: %s", self.command_prefix)

        if not self.gears:
            await database.ensure_tables()
            await self.add_gear(General(self))
            await self.add_gear(Moderation(self))
            await self.add_gear(Fun(self))
            await self.add_gear(Info(self))
            await self.add_gear(Economy(self))
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
