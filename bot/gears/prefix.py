"""Prefix management commands for Bronx."""

import os

import stoat
from stoat.ext import commands

from bot import database
from bot import style

MAX_SERVER_PREFIXES = 5
MAX_USER_PREFIXES = 5
MAX_PREFIX_LENGTH = 16


class Prefix(commands.Gear):
    """Manage server and user prefixes."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._default = os.environ.get("COMMAND_PREFIX", "!")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def _is_admin(ctx: commands.Context) -> bool:
        """Return True if the author is the server owner or has manage_server."""
        if ctx.server is None:
            return False
        if hasattr(ctx.server, "owner_id") and str(ctx.server.owner_id) == str(ctx.author.id):
            return True
        if hasattr(ctx.server, "owner") and ctx.server.owner and str(ctx.server.owner.id) == str(ctx.author.id):
            return True
        perms = ctx.server.permissions_for(ctx.author)
        if hasattr(perms, "manage_server") and perms.manage_server:
            return True
        return False

    # ------------------------------------------------------------------
    # prefix  (base command – router)
    # ------------------------------------------------------------------

    @commands.command(name="prefix")
    async def prefix_base(self, ctx: commands.Context, action: str = None, *, value: str = None) -> None:
        """manage server & user prefixes

        **server** (admins/owner):
        `prefix add <prefix>` — add a server prefix
        `prefix remove <prefix>` — remove a server prefix
        `prefix list` — list server prefixes

        **personal**:
        `prefix user add <prefix>` — add a personal prefix
        `prefix user remove <prefix>` — remove a personal prefix
        `prefix user list` — list your personal prefixes
        `prefix user clear` — remove all personal prefixes"""

        if action is None:
            await self._show_prefixes(ctx)
            return

        action_lower = action.lower()

        if action_lower == "list":
            await self._list_server(ctx)
        elif action_lower == "add":
            await self._add_server(ctx, value)
        elif action_lower == "remove":
            await self._remove_server(ctx, value)
        elif action_lower == "user":
            await self._user_router(ctx, value)
        else:
            await ctx.send(
                f"{style.no_emoji()} unknown action `{action}`. "
                f"try `{ctx.prefix}help prefix`"
            )

    # ------------------------------------------------------------------
    # Show current effective prefixes
    # ------------------------------------------------------------------

    async def _show_prefixes(self, ctx: commands.Context) -> None:
        lines = []

        # bot mention
        me = self.bot.me
        if me is not None:
            lines.append(f"**mention:** <@{me.id}>")

        # user prefixes
        user_prefixes = await database.get_user_prefixes(str(ctx.author.id))
        if user_prefixes:
            formatted = ", ".join(f"`{p}`" for p in user_prefixes)
            lines.append(f"**your prefixes:** {formatted} *(exclusive)*")

        # server prefixes
        if ctx.server is not None:
            server_prefixes = await database.get_server_prefixes(str(ctx.server.id))
            if server_prefixes:
                formatted = ", ".join(f"`{p}`" for p in server_prefixes)
                lines.append(f"**server:** {formatted}")

        # default
        lines.append(f"**default:** `{self._default}`")

        embed = stoat.SendableEmbed(
            description="\n".join(lines),
            color=style.COLOR_INFO,
        )
        await ctx.send(embeds=[embed])

    # ------------------------------------------------------------------
    # Server prefix management (admin only)
    # ------------------------------------------------------------------

    async def _list_server(self, ctx: commands.Context) -> None:
        if ctx.server is None:
            await ctx.send(f"{style.no_emoji()} only works in servers")
            return

        prefixes = await database.get_server_prefixes(str(ctx.server.id))
        if not prefixes:
            await ctx.send(f"no custom server prefixes — using default `{self._default}`")
            return

        formatted = "\n".join(f"• `{p}`" for p in prefixes)
        embed = stoat.SendableEmbed(
            description=f"**server prefixes**\n{formatted}",
            color=style.COLOR_SERVER,
        )
        await ctx.send(embeds=[embed])

    async def _add_server(self, ctx: commands.Context, prefix: str = None) -> None:
        if ctx.server is None:
            await ctx.send(f"{style.no_emoji()} only works in servers")
            return

        if not await self._is_admin(ctx):
            await ctx.send(f"{style.no_emoji()} you need **manage server** or be the server owner")
            return

        if not prefix:
            await ctx.send(f"{style.no_emoji()} provide a prefix: `{ctx.prefix}prefix add <prefix>`")
            return

        if len(prefix) > MAX_PREFIX_LENGTH:
            await ctx.send(f"{style.no_emoji()} prefix too long (max {MAX_PREFIX_LENGTH} chars)")
            return

        server_id = str(ctx.server.id)
        existing = await database.get_server_prefixes(server_id)
        if len(existing) >= MAX_SERVER_PREFIXES:
            await ctx.send(f"{style.no_emoji()} max {MAX_SERVER_PREFIXES} server prefixes reached")
            return

        ok = await database.add_server_prefix(server_id, prefix)
        if ok:
            await ctx.send(f"{style.yes_emoji()} added server prefix `{prefix}`")
        else:
            await ctx.send(f"{style.no_emoji()} `{prefix}` is already a server prefix")

    async def _remove_server(self, ctx: commands.Context, prefix: str = None) -> None:
        if ctx.server is None:
            await ctx.send(f"{style.no_emoji()} only works in servers")
            return

        if not await self._is_admin(ctx):
            await ctx.send(f"{style.no_emoji()} you need **manage server** or be the server owner")
            return

        if not prefix:
            await ctx.send(f"{style.no_emoji()} provide a prefix: `{ctx.prefix}prefix remove <prefix>`")
            return

        ok = await database.remove_server_prefix(str(ctx.server.id), prefix)
        if ok:
            await ctx.send(f"{style.yes_emoji()} removed server prefix `{prefix}`")
        else:
            await ctx.send(f"{style.no_emoji()} `{prefix}` is not a server prefix")

    # ------------------------------------------------------------------
    # User prefix management (any user)
    # ------------------------------------------------------------------

    async def _user_router(self, ctx: commands.Context, value: str = None) -> None:
        """Route `prefix user <subaction> [value]`."""
        if not value:
            # no args → show user prefixes
            await self._list_user(ctx)
            return

        parts = value.split(None, 1)
        sub = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else None

        if sub == "list":
            await self._list_user(ctx)
        elif sub == "add":
            await self._add_user(ctx, arg)
        elif sub == "remove":
            await self._remove_user(ctx, arg)
        elif sub == "clear":
            await self._clear_user(ctx)
        else:
            # treat the whole value as a prefix to add (shorthand)
            await self._add_user(ctx, value)

    async def _list_user(self, ctx: commands.Context) -> None:
        user_id = str(ctx.author.id)
        prefixes = await database.get_user_prefixes(user_id)
        if not prefixes:
            await ctx.send(f"no personal prefixes set — using server/default prefix")
            return

        formatted = "\n".join(f"• `{p}`" for p in prefixes)
        embed = stoat.SendableEmbed(
            description=f"**your prefixes**\n{formatted}",
            color=style.COLOR_USER,
        )
        await ctx.send(embeds=[embed])

    async def _add_user(self, ctx: commands.Context, prefix: str = None) -> None:
        if not prefix:
            await ctx.send(f"{style.no_emoji()} provide a prefix: `{ctx.prefix}prefix user add <prefix>`")
            return

        if len(prefix) > MAX_PREFIX_LENGTH:
            await ctx.send(f"{style.no_emoji()} prefix too long (max {MAX_PREFIX_LENGTH} chars)")
            return

        user_id = str(ctx.author.id)
        existing = await database.get_user_prefixes(user_id)
        if len(existing) >= MAX_USER_PREFIXES:
            await ctx.send(f"{style.no_emoji()} max {MAX_USER_PREFIXES} personal prefixes reached")
            return

        ok = await database.add_user_prefix(user_id, prefix)
        if ok:
            await ctx.send(
                f"{style.yes_emoji()} added personal prefix `{prefix}`\n"
                f"the bot will **only** respond to your personal prefixes (+ mention) for your messages"
            )
        else:
            await ctx.send(f"{style.no_emoji()} `{prefix}` is already one of your prefixes")

    async def _remove_user(self, ctx: commands.Context, prefix: str = None) -> None:
        if not prefix:
            await ctx.send(f"{style.no_emoji()} provide a prefix: `{ctx.prefix}prefix user remove <prefix>`")
            return

        ok = await database.remove_user_prefix(str(ctx.author.id), prefix)
        if ok:
            await ctx.send(f"{style.yes_emoji()} removed personal prefix `{prefix}`")
        else:
            await ctx.send(f"{style.no_emoji()} `{prefix}` is not one of your prefixes")

    async def _clear_user(self, ctx: commands.Context) -> None:
        ok = await database.clear_user_prefixes(str(ctx.author.id))
        if ok:
            await ctx.send(f"{style.yes_emoji()} all personal prefixes cleared")
        else:
            await ctx.send(f"{style.no_emoji()} you didn't have any personal prefixes")
