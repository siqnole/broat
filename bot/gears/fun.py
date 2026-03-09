import random

from stoat.ext import commands

from bot import style


class Fun(commands.Gear):
    """Fun & entertainment commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command()
    async def coinflip(self, ctx: commands.Context, choice: str = "heads") -> None:
        """flip a coin"""
        result = random.choice(["heads", "tails"])
        if result == choice.lower():
            await ctx.send(f"{style.yes_emoji()} {result}")
        else:
            await ctx.send(f"{style.no_emoji()} {result}")

    @commands.command()
    async def roll(self, ctx: commands.Context, sides: int = 6) -> None:
        """roll a die"""
        if sides < 2:
            await ctx.send("needs at least 2 sides")
            return
        result = random.randint(1, sides)
        await ctx.send(f"rolled {result} (d{sides})")

    @commands.command(name="8ball")
    async def eightball(self, ctx: commands.Context, *, question: str) -> None:
        """ask the magic 8-ball"""
        responses = [
            "it is certain",
            "it is decidedly so",
            "without a doubt",
            "yes definitely",
            "you may rely on it",
            "as i see it, yes",
            "most likely",
            "outlook good",
            "yes",
            "signs point to yes",
            "reply hazy try again",
            "ask again later",
            "better not tell you now",
            "cannot predict now",
            "concentrate and ask again",
            "don't count on it",
            "my reply is no",
            "my sources say no",
            "outlook not so good",
            "very doubtful",
            "no lol"
        ]
        await ctx.send(random.choice(responses))

    @commands.command()
    async def choose(self, ctx: commands.Context, *, choices: str) -> None:
        """pick one option from comma-separated list"""
        options = [o.strip() for o in choices.split(",") if o.strip()]
        if len(options) < 2:
            await ctx.send("need at least 2 options")
            return
        await ctx.send(random.choice(options))

    @commands.command()
    async def reverse(self, ctx: commands.Context, *, text: str) -> None:
        """reverse text"""
        await ctx.send(text[::-1])

    @commands.command()
    async def shout(self, ctx: commands.Context, *, text: str) -> None:
        """shout your text"""
        await ctx.send(text.upper())
