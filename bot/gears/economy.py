"""Economy commands for Bronx."""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

import stoat
from stoat.ext import commands

from bot import style
from bot.database import get_pool

# ── constants ────────────────────────────────────────────────────────────

CURRENCY = "coins"

DAILY_AMOUNT = 500
DAILY_COOLDOWN = timedelta(hours=24)

WORK_MIN, WORK_MAX = 100, 350
WORK_COOLDOWN = timedelta(hours=1)

BEG_MIN, BEG_MAX = 10, 150
BEG_FAIL_CHANCE = 0.35
BEG_COOLDOWN = timedelta(minutes=30)

CRIME_MIN, CRIME_MAX = 300, 800
CRIME_FINE_MIN, CRIME_FINE_MAX = 200, 600
CRIME_FAIL_CHANCE = 0.45
CRIME_COOLDOWN = timedelta(hours=2)

FISH_MIN, FISH_MAX = 50, 250
FISH_COOLDOWN = timedelta(minutes=45)

SEARCH_MIN, SEARCH_MAX = 20, 200
SEARCH_COOLDOWN = timedelta(minutes=30)

WORK_RESPONSES = [
    "you worked as a barista and earned",
    "you delivered packages and earned",
    "you mowed lawns and earned",
    "you drove an uber and earned",
    "you tutored a student and earned",
    "you walked some dogs and earned",
    "you coded a website and earned",
    "you streamed on twitch and earned",
    "you sold lemonade and earned",
    "you fixed a computer and earned",
]

BEG_SUCCESS = [
    "a stranger felt generous and gave you",
    "someone threw coins at you —",
    "a kind soul donated",
    "you found a wallet and returned it, the owner gave you",
    "an old lady tipped you",
]

BEG_FAIL = [
    "everyone ignored you",
    "someone told you to get a job",
    "a pigeon stole your sign",
    "nobody had any change",
    "you tripped and embarrassed yourself",
]

CRIME_SUCCESS = [
    "you robbed a gas station and got",
    "you hacked a vending machine for",
    "you ran a successful scam and earned",
    "you counterfeited money and made",
    "you pulled off a heist and scored",
]

CRIME_FAIL = [
    "you got caught and were fined",
    "the police nabbed you — you paid",
    "your plan failed and you lost",
    "a security camera caught you, fine of",
    "you tripped the alarm and paid",
]

FISH_CATCHES = [
    ("a tiny sardine", 50, 80),
    ("a bass", 80, 130),
    ("a catfish", 100, 160),
    ("a salmon", 120, 200),
    ("a golden trout", 180, 250),
    ("an old boot (with coins inside)", 20, 50),
    ("a treasure chest", 200, 250),
]

SEARCH_PLACES = [
    "under the couch cushions",
    "in your old jacket",
    "behind the vending machine",
    "in a parking lot",
    "inside a library book",
    "in a dumpster",
    "behind a diner",
    "in a coat pocket at goodwill",
    "under a park bench",
    "in a storm drain",
]

# ── medal emojis ─────────────────────────────────────────────────────────

MEDAL_1ST = f":{style.EMOJI_1ST}:"
MEDAL_2ND = f":{style.EMOJI_2ND}:"
MEDAL_3RD = f":{style.EMOJI_3RD}:"


# ── helpers ──────────────────────────────────────────────────────────────

async def _get_user(user_id: str) -> dict | None:
    """Fetch a user row from the economy table."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT user_id, balance, last_daily, last_work, last_beg, "
                "last_crime, last_fish, last_search FROM economy WHERE user_id = %s",
                (user_id,),
            )
            row = await cur.fetchone()
            if row is None:
                return None
            return {
                "user_id": row[0], "balance": row[1],
                "last_daily": row[2], "last_work": row[3],
                "last_beg": row[4], "last_crime": row[5],
                "last_fish": row[6], "last_search": row[7],
            }


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
    return {
        "user_id": user_id, "balance": 0,
        "last_daily": None, "last_work": None, "last_beg": None,
        "last_crime": None, "last_fish": None, "last_search": None,
    }


async def _set_balance(user_id: str, amount: int) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE economy SET balance = %s WHERE user_id = %s",
                (amount, user_id),
            )


async def _update_cooldown(user_id: str, column: str, new_balance: int, now: datetime) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                f"UPDATE economy SET balance = %s, {column} = %s WHERE user_id = %s",
                (new_balance, now, user_id),
            )


def _format_remaining(remaining: timedelta) -> str:
    """Format a timedelta as a human-readable string."""
    hours, rem = divmod(int(remaining.total_seconds()), 3600)
    minutes, seconds = divmod(rem, 60)
    parts: list[str] = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    return " ".join(parts)


def _check_cooldown(user: dict, column: str, cooldown: timedelta, now: datetime) -> str | None:
    """Return formatted remaining time if still on cooldown, else None."""
    last = user.get(column)
    if last is None:
        return None
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    next_claim = last + cooldown
    if now < next_claim:
        return _format_remaining(next_claim - now)
    return None


# ── gear ─────────────────────────────────────────────────────────────────

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

        remaining = _check_cooldown(user, "last_daily", DAILY_COOLDOWN, now)
        if remaining:
            embed = stoat.SendableEmbed(
                description=(
                    f"{style.warning_emoji()} you already claimed your daily\n\n"
                    f"**try again in:** {remaining}"
                ),
                color=style.COLOR_WARNING,
            )
            await ctx.send(embeds=[embed])
            return

        new_balance = user["balance"] + DAILY_AMOUNT
        await _update_cooldown(user_id, "last_daily", new_balance, now)

        embed = stoat.SendableEmbed(
            description=(
                f"{style.yes_emoji()} you claimed **{DAILY_AMOUNT} {CURRENCY}**!\n\n"
                f"**balance:** {new_balance:,} {CURRENCY}"
            ),
            color=style.COLOR_SUCCESS,
        )
        await ctx.send(embeds=[embed])

    # ── work ─────────────────────────────────────────────────────────────

    @commands.command()
    async def work(self, ctx: commands.Context) -> None:
        """work a shift for coins (every 1h)"""
        user_id = str(ctx.author.id)
        user = await _ensure_user(user_id)
        now = datetime.now(timezone.utc)

        remaining = _check_cooldown(user, "last_work", WORK_COOLDOWN, now)
        if remaining:
            embed = stoat.SendableEmbed(
                description=(
                    f"{style.warning_emoji()} you're still tired from work\n\n"
                    f"**try again in:** {remaining}"
                ),
                color=style.COLOR_WARNING,
            )
            await ctx.send(embeds=[embed])
            return

        earned = random.randint(WORK_MIN, WORK_MAX)
        new_balance = user["balance"] + earned
        await _update_cooldown(user_id, "last_work", new_balance, now)

        job = random.choice(WORK_RESPONSES)
        embed = stoat.SendableEmbed(
            description=(
                f"{style.yes_emoji()} {job} **{earned} {CURRENCY}**\n\n"
                f"**balance:** {new_balance:,} {CURRENCY}"
            ),
            color=style.COLOR_SUCCESS,
        )
        await ctx.send(embeds=[embed])

    # ── beg ──────────────────────────────────────────────────────────────

    @commands.command()
    async def beg(self, ctx: commands.Context) -> None:
        """beg for coins — might fail (every 30m)"""
        user_id = str(ctx.author.id)
        user = await _ensure_user(user_id)
        now = datetime.now(timezone.utc)

        remaining = _check_cooldown(user, "last_beg", BEG_COOLDOWN, now)
        if remaining:
            embed = stoat.SendableEmbed(
                description=(
                    f"{style.warning_emoji()} you begged too recently\n\n"
                    f"**try again in:** {remaining}"
                ),
                color=style.COLOR_WARNING,
            )
            await ctx.send(embeds=[embed])
            return

        if random.random() < BEG_FAIL_CHANCE:
            await _update_cooldown(user_id, "last_beg", user["balance"], now)
            msg = random.choice(BEG_FAIL)
            embed = stoat.SendableEmbed(
                description=f"{style.no_emoji()} {msg}",
                color=style.COLOR_ERROR,
            )
            await ctx.send(embeds=[embed])
            return

        earned = random.randint(BEG_MIN, BEG_MAX)
        new_balance = user["balance"] + earned
        await _update_cooldown(user_id, "last_beg", new_balance, now)

        msg = random.choice(BEG_SUCCESS)
        embed = stoat.SendableEmbed(
            description=(
                f"{style.yes_emoji()} {msg} **{earned} {CURRENCY}**\n\n"
                f"**balance:** {new_balance:,} {CURRENCY}"
            ),
            color=style.COLOR_SUCCESS,
        )
        await ctx.send(embeds=[embed])

    # ── crime ────────────────────────────────────────────────────────────

    @commands.command()
    async def crime(self, ctx: commands.Context) -> None:
        """commit a crime — high risk, high reward (every 2h)"""
        user_id = str(ctx.author.id)
        user = await _ensure_user(user_id)
        now = datetime.now(timezone.utc)

        remaining = _check_cooldown(user, "last_crime", CRIME_COOLDOWN, now)
        if remaining:
            embed = stoat.SendableEmbed(
                description=(
                    f"{style.warning_emoji()} you're laying low for now\n\n"
                    f"**try again in:** {remaining}"
                ),
                color=style.COLOR_WARNING,
            )
            await ctx.send(embeds=[embed])
            return

        if random.random() < CRIME_FAIL_CHANCE:
            fine = random.randint(CRIME_FINE_MIN, CRIME_FINE_MAX)
            new_balance = max(0, user["balance"] - fine)
            await _update_cooldown(user_id, "last_crime", new_balance, now)

            msg = random.choice(CRIME_FAIL)
            embed = stoat.SendableEmbed(
                description=(
                    f"{style.no_emoji()} {msg} **{fine} {CURRENCY}**\n\n"
                    f"**balance:** {new_balance:,} {CURRENCY}"
                ),
                color=style.COLOR_ERROR,
            )
            await ctx.send(embeds=[embed])
            return

        earned = random.randint(CRIME_MIN, CRIME_MAX)
        new_balance = user["balance"] + earned
        await _update_cooldown(user_id, "last_crime", new_balance, now)

        msg = random.choice(CRIME_SUCCESS)
        embed = stoat.SendableEmbed(
            description=(
                f"{style.yes_emoji()} {msg} **{earned} {CURRENCY}**\n\n"
                f"**balance:** {new_balance:,} {CURRENCY}"
            ),
            color=style.COLOR_SUCCESS,
        )
        await ctx.send(embeds=[embed])

    # ── fish ─────────────────────────────────────────────────────────────

    @commands.command()
    async def fish(self, ctx: commands.Context) -> None:
        """go fishing for coins (every 45m)"""
        user_id = str(ctx.author.id)
        user = await _ensure_user(user_id)
        now = datetime.now(timezone.utc)

        remaining = _check_cooldown(user, "last_fish", FISH_COOLDOWN, now)
        if remaining:
            embed = stoat.SendableEmbed(
                description=(
                    f"{style.warning_emoji()} the fish aren't biting yet\n\n"
                    f"**try again in:** {remaining}"
                ),
                color=style.COLOR_WARNING,
            )
            await ctx.send(embeds=[embed])
            return

        catch_name, low, high = random.choice(FISH_CATCHES)
        earned = random.randint(low, high)
        new_balance = user["balance"] + earned
        await _update_cooldown(user_id, "last_fish", new_balance, now)

        embed = stoat.SendableEmbed(
            description=(
                f"{style.yes_emoji()} you caught **{catch_name}** worth **{earned} {CURRENCY}**\n\n"
                f"**balance:** {new_balance:,} {CURRENCY}"
            ),
            color=style.COLOR_SUCCESS,
        )
        await ctx.send(embeds=[embed])

    # ── search ───────────────────────────────────────────────────────────

    @commands.command()
    async def search(self, ctx: commands.Context) -> None:
        """search for coins in random places (every 30m)"""
        user_id = str(ctx.author.id)
        user = await _ensure_user(user_id)
        now = datetime.now(timezone.utc)

        remaining = _check_cooldown(user, "last_search", SEARCH_COOLDOWN, now)
        if remaining:
            embed = stoat.SendableEmbed(
                description=(
                    f"{style.warning_emoji()} you've searched everywhere recently\n\n"
                    f"**try again in:** {remaining}"
                ),
                color=style.COLOR_WARNING,
            )
            await ctx.send(embeds=[embed])
            return

        place = random.choice(SEARCH_PLACES)
        earned = random.randint(SEARCH_MIN, SEARCH_MAX)
        new_balance = user["balance"] + earned
        await _update_cooldown(user_id, "last_search", new_balance, now)

        embed = stoat.SendableEmbed(
            description=(
                f"{style.yes_emoji()} you searched **{place}** and found **{earned} {CURRENCY}**\n\n"
                f"**balance:** {new_balance:,} {CURRENCY}"
            ),
            color=style.COLOR_SUCCESS,
        )
        await ctx.send(embeds=[embed])

    # ── balance ──────────────────────────────────────────────────────────

    @commands.command(name="balance", aliases=['bal'])
    async def balance(self, ctx: commands.Context) -> None:
        """check your coin balance"""
        user_id = str(ctx.author.id)
        user = await _ensure_user(user_id)

        embed = stoat.SendableEmbed(
            description=f"**balance:** {user['balance']:,} {CURRENCY}",
            color=style.COLOR_USER,
        )
        await ctx.send(embeds=[embed])

    # ── pay ───────────────────────────────────────────────────────────────

    @commands.command(name="pay", aliases=['give', 'send'])
    async def pay(self, ctx: commands.Context, target: str, amount: int) -> None:
        """send coins to another user — .pay @user amount"""
        if amount <= 0:
            await ctx.send(f"{style.no_emoji()} amount must be positive")
            return

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

    @commands.command(name="leaderboard", aliases=['lb'])
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
            if i == 1:
                prefix = f"{MEDAL_1ST} "
            elif i == 2:
                prefix = f"{MEDAL_2ND} "
            elif i == 3:
                prefix = f"{MEDAL_3RD} "
            else:
                prefix = f"`{i}.` "
            lines.append(f"{prefix}<@{uid}> — **{bal:,}** {CURRENCY}")

        embed = stoat.SendableEmbed(
            description="\n".join(lines),
            color=style.COLOR_INFO,
        )
        await ctx.send(embeds=[embed])
