import stoat
from stoat.ext import commands

from bot import style


class Info(commands.Gear):
    """Information / lookup commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command()
    async def userinfo(self, ctx: commands.Context, *, member: stoat.Member = None) -> None:
        """user info"""
        target = member or ctx.author
        
        description_lines = [f"`{target.id}`"]
        
        if hasattr(target, "joined_at") and target.joined_at:
            description_lines.append(f"joined {target.joined_at}")
        if hasattr(target, "roles") and target.roles:
            role_names = ", ".join(str(r) for r in target.roles)
            description_lines.append(f"roles: {role_names}")
        
        embed = stoat.SendableEmbed(
            description=f"**{target.name}**\n\n{chr(10).join(description_lines)}",
            color=style.COLOR_USER
        )
        
        if hasattr(target, "avatar") and target.avatar:
            embed.icon_url = target.avatar.url() if hasattr(target.avatar, 'url') else None
        
        await ctx.send(embeds=[embed])

    @commands.command()
    async def serverinfo(self, ctx: commands.Context) -> None:
        """server info"""
        server = ctx.server
        if server is None:
            await ctx.send("only works in servers")
            return

        description_lines = [f"`{server.id}`"]
        
        if hasattr(server, "owner") and server.owner:
            description_lines.append(f"owner: {server.owner}")
        if hasattr(server, "member_count") and server.member_count:
            description_lines.append(f"{server.member_count} members")
        if hasattr(server, "description") and server.description:
            description_lines.append(f"{server.description}")
        
        embed = stoat.SendableEmbed(
            description=f"**{server.name}**\n\n{chr(10).join(description_lines)}",
            color=style.COLOR_SERVER
        )
        
        if hasattr(server, "icon") and server.icon:
            embed.icon_url = server.icon.url() if hasattr(server.icon, 'url') else None
        
        await ctx.send(embeds=[embed])

    @commands.command()
    async def avatar(self, ctx: commands.Context, *, member: stoat.Member = None) -> None:
        """get avatar url"""
        target = member or ctx.author
        if hasattr(target, "avatar") and target.avatar:
            url = target.avatar.url() if hasattr(target.avatar, 'url') else str(target.avatar)
            await ctx.send(url)
        else:
            await ctx.send(f"{style.no_emoji()} no avatar set")
