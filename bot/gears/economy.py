"""Economy commands for Bronx."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import stoat
from stoat.ext import commands

from bot import style
from bot.database import get_pool

DAILY_AMOUNT = 500
DAILY_COOLDOWN = timedelta(hours=24)
CURRENCY = "coins"


async def _get_user(user_id: str) -> dict | None:
    """Fetch a user row from the economy table."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT user_id, balance, last_daily FROM economy WHERE user_id = %s",
                (user_id,),
            )
            row = await cur.fetchone()
            if row is None:
                return None
            return {"user_id": row[0], "balance": row[1], "last_daily": row[2]}


async def _ensure_user(user_id: str) -> dict:
    """Get or create a user row."""
    user = await _get_user(user_id)
    if user is not None:
        return user
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT IGNORE INTO economy (user_id, balance) VALUES (%s, 0)",
                (user_id,),
            )
    return {"user_id": user_id, "balance": 0, "last_daily": None}


async def _set_balance(user_id: str, amount: int) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE economy SET balance = %s WHERE user_id = %s",
                (amount, user_id),
            )


async def _update_daily(user_id: str, new_balance: int, now: datetime) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE economy SET balance = %s, last_daily = %s WHERE user_id = %s",
                (new_balance, now, user_id),
            )


class Economy(commands.Gear):
    """Economy commands — earn and manage coins."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ── daily ────────────────────────────────────────────────────────────

    @commands.command()
    async def daily(self, ctx: commands.Context) -> None:
        """claim your daily coins (every 24h)"""
        user_id = str(ctx.author.id)
        user = await _ensure_user(user_id)

        now = datetime.now(timezone.utc)

        if user["last_daily"] is not None:
            last = user["last_daily"]
            # ensure tz-aware comparison
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            next_claim = last + DAILY_COOLDOWN
            if now < next_claim:
                remaining = next_claim - now
                hours, rem = divmod(int(remaining.total_seconds()), 3600)
                minutes, seconds = divmod(rem, 60)
                parts: list[str] = []
                if hours:
                    parts.append(f"{hours}h")
                if minutes:
                    parts.append(f"{minutes}m")
                parts.append(f"{seconds}s")

                embed = stoat.SendableEmbed(
                    description=(
                        f"{style.warning_emoji()} you already claimed your daily\n\n"
                        f"**try again in:** {' '.join(parts)}"
                    ),
                    color=style.COLOR_WARNING,
                )
                await ctx.send(embeds=[embed])
                return

        new_balance = user["balance"] + DAILY_AMOUNT
        await _update_daily(user_id, new_balance, now)

        embed = stoat.SendableEmbed(
            description=(
                f"{style.yes_emoji()} you claimed **{DAILY_AMOUNT} {CURRENCY}**!\n\n"
                f"**balance:** {new_balance:,} {CURRENCY}"
            ),
            color=style.COLOR_SUCCESS,
        )
        await ctx.send(embeds=[embed])

    # ── balance ──────────────────────────────────────────────────────────

    @commands.command(name="balance")
    async def balance(self, ctx: commands.Context) -> None:
        """check your coin balance"""
        user_id = str(ctx.author.id)
        user = await _ensure_user(user_id)

        embed = stoat.SendableEmbed(
            description=(
                f"**balance:** {user['balance']:,} {CURRENCY}"
            ),
            color=style.COLOR_USER,
        )
        await ctx.send(embeds=[embed])

    @commands.command(name="bal")
    async def bal(self, ctx: commands.Context) -> None:
        """check your coin balance (shortcut)"""
        await self.balance(ctx)

    # ── pay ───────────────────────────────────────────────────────────────

    @commands.command()
    async def pay(self, ctx: commands.Context, target: str, amount: int) -> None:
        """send coins to another user — .pay @user amount"""
        if amount <= 0:
            await ctx.send(f"{style.no_emoji()} amount must be positive")
            return

        # resolve mention to ID
        target_id = target.strip("<@!>")

        if target_id == str(ctx.author.id):
            await ctx.send(f"{style.no_emoji()} you can't pay yourself")
            return

        sender = await _ensure_user(str(ctx.author.id))
        if sender["balance"] < amount:
            embed = stoat.SendableEmbed(
                description=(
                    f"{style.no_emoji()} not enough {CURRENCY}\n\n"
                    f"**your balance:** {sender['balance']:,} {CURRENCY}"
                ),
                color=style.COLOR_ERROR,
            )
            await ctx.send(embeds=[embed])
            return

        receiver = await _ensure_user(target_id)

        await _set_balance(str(ctx.author.id), sender["balance"] - amount)
        await _set_balance(target_id, receiver["balance"] + amount)

        embed = stoat.SendableEmbed(
            description=(
                f"{style.yes_emoji()} sent **{amount:,} {CURRENCY}** to <@{target_id}>\n\n"
                f"**your balance:** {sender['balance'] - amount:,} {CURRENCY}"
            ),
            color=style.COLOR_SUCCESS,
        )
        await ctx.send(embeds=[embed])

    # ── leaderboard ──────────────────────────────────────────────────────

    @commands.command(name="leaderboard")
    async def leaderboard(self, ctx: commands.Context) -> None:
        """top 10 richest users"""
        pool = await get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT user_id, balance FROM economy ORDER BY balance DESC LIMIT 10"
                )
                rows = await cur.fetchall()

        if not rows:
            await ctx.send("no one has any coins yet")
            return

        lines: list[str] = []
        for i, (uid, bal) in enumerate(rows, start=1):
            medal = {1: ":01KK7EC8VP8CMKZW8SB64TCVTC:", 2: "", 3: ""}.get(i, "")
            prefix = f"{medal} " if medal else f"`{i}.` "
            lines.append(f"{prefix}<@{uid}> — **{bal:,}** {CURRENCY}")

        embed = stoat.SendableEmbed(
            description="\n".join(lines),
            color=style.COLOR_INFO,
        )
        await ctx.send(embeds=[embed])

    @commands.command(name="lb")
    async def lb(self, ctx: commands.Context) -> None:
        """top 10 richest users (shortcut)"""
        await self.leaderboard(ctx)
