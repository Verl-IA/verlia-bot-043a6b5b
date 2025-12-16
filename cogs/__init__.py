import discord
from discord.ext import commands
import os

from discord.ext import commands

class MyCog(commands.Cog):
    """Cog base de exemplo."""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="hello")
    async def hello_command(self, ctx):
        """Responde com um olá."""
        await ctx.send(f"Olá, {ctx.author.display_name}!")


async def setup(bot):
    await bot.add_cog(MyCog(bot))


bot.run(os.environ.get('BOT_TOKEN'))