import time
import platform
import asyncio
import inspect

import stoat
from stoat.ext import commands

from bot import style


class General(commands.Gear):
    """General-purpose commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._start_time = time.monotonic()

    @commands.command()
    async def help(self, ctx: commands.Context, *, command_name: str = None) -> None:
        """show commands"""
        if command_name:
            cmd = self.bot.get_command(command_name)
            if cmd:
                doc = cmd.help or "no description"
                
                # build usage string
                usage_parts = [f"{ctx.prefix}{cmd.name}"]
                if hasattr(cmd, 'params') and cmd.params:
                    for param_name, param in cmd.params.items():
                        if param_name in ('self', 'ctx'):
                            continue
                        if param.kind == inspect.Parameter.VAR_POSITIONAL:
                            continue
                        if param.kind == inspect.Parameter.KEYWORD_ONLY:
                            if param.default is inspect.Parameter.empty:
                                usage_parts.append(f"<{param_name}>")
                            else:
                                usage_parts.append(f"[{param_name}]")
                        else:
                            if param.default is inspect.Parameter.empty:
                                usage_parts.append(f"<{param_name}>")
                            else:
                                usage_parts.append(f"[{param_name}]")
                
                usage = " ".join(usage_parts)
                embed = stoat.SendableEmbed(
                    description=f"`{usage}`\n{doc}",
                    color=style.COLOR_HELP
                )
                await ctx.send(embeds=[embed])
            else:
                await ctx.send(f"command `{command_name}` not found")
            return

        description_lines = []
        
        for gear_name, gear in self.bot.gears.items():
            gear_commands = gear.get_commands()
            if gear_commands:
                description_lines.append(f"**{gear_name.lower()}**")
                for cmd in gear_commands:
                    doc = cmd.help or "no description"
                    description_lines.append(f"`{ctx.prefix}{cmd.name}` — {doc}")
                description_lines.append("")
        
        description_lines.append(f"`{ctx.prefix}help <command>` for info")
        
        embed = stoat.SendableEmbed(
            description="\n".join(description_lines),
            color=style.COLOR_HELP
        )
        await ctx.send(embeds=[embed])

    @commands.command()
    async def ping(self, ctx: commands.Context) -> None:
        """check latency"""
        start_time = time.perf_counter_ns()
        
        ws_start = time.perf_counter()
        try:
            await ctx.shard.ping()
            ws_latency = (time.perf_counter() - ws_start) * 1000
        except Exception:
            ws_latency = None
        
        internet_start = time.perf_counter()
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get('https://1.1.1.1', timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    internet_latency = (time.perf_counter() - internet_start) * 1000
        except Exception:
            internet_latency = None
        
        response_time_ns = time.perf_counter_ns() - start_time
        response_time_us = response_time_ns / 1000
        
        description_lines = [
            f"`{response_time_us:.2f}μs` response",
        ]
        
        if ws_latency is not None:
            description_lines.append(f"`{ws_latency:.2f}ms` ws")
        else:
            description_lines.append(f"{style.no_emoji()} ws failed")
        
        if internet_latency is not None:
            description_lines.append(f"`{internet_latency:.2f}ms` net")
        else:
            description_lines.append(f"{style.no_emoji()} net failed")
        
        embed = stoat.SendableEmbed(
            description="\n".join(description_lines),
            color=style.COLOR_SUCCESS
        )
        
        await ctx.send(embeds=[embed])

    @commands.command()
    async def uptime(self, ctx: commands.Context) -> None:
        """how long i've been up"""
        elapsed = int(time.monotonic() - self._start_time)
        hours, remainder = divmod(elapsed, 3600)
        minutes, seconds = divmod(remainder, 60)
        parts: list[str] = []
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")
        await ctx.send(' '.join(parts))

    @commands.command()
    async def about(self, ctx: commands.Context) -> None:
        """about the bot"""
        lines = [
            "bronx — stoat.chat bot",
            f"python {platform.python_version()} · stoat.py",
            f"prefix: `{ctx.prefix}`",
        ]
        await ctx.send("\n".join(lines))

    @commands.command()
    async def echo(self, ctx: commands.Context, *, text: str) -> None:
        """repeat your message"""
        await ctx.send(text)

    @commands.command()
    async def say(self, ctx: commands.Context, *, text: str) -> None:
        """say something"""
        await ctx.send(text)

    @commands.command()
    async def embedtest(self, ctx: commands.Context) -> None:
        """test embed"""
        embed = stoat.SendableEmbed(
            description="embed test\n\nworks nice",
            color=style.COLOR_FUN,
            icon_url="https://cdn.stoatusercontent.com/emojis/01JBRDQ3S3CC7V6VTHJPC71B68/robot.png",
            url="https://stoat.chat"
        )
        await ctx.send(embeds=[embed])
