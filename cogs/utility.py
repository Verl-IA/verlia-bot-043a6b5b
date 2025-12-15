import datetime
import discord
from config import EMBED_COLOR, INFO_COLOR
from discord import app_commands
from discord.ext import commands
from utils.embeds import info

"""Comandos de Utilidade do Bot"""

class Utility(commands.Cog):
    """Classe Utility."""
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="help", description="Exibe a lista de comandos do bot.")
    async def help_cmd(self, interaction: discord.Interaction):
        help_embed = info("Central de Ajuda", "Aqui estão todos os comandos que você pode usar:")
        
        help_embed.add_field(name="🛡️ Comandos de Moderação", 
                              value="`/ban` - Bane um usuário\n"
                                    "`/unban` - Desbane um usuário\n"
                                    "`/kick` - Expulsa um usuário\n"
                                    "`/mute` - Coloca um usuário em tempo de espera\n"
                                    "`/unmute` - Remove o tempo de espera de um usuário\n"
                                    "`/warn` - Adverte um usuário\n"
                                    "`/warns` - Exibe advertências de um usuário\n"
                                    "`/clear_warns` - Limpa advertências de um usuário\n"
                                    "`/clear` - Limpa mensagens no canal", 
                              inline=False)
        
        help_embed.add_field(name="🛠️ Comandos de Utilidade",
                              value="`/help` - Exibe esta mensagem de ajuda\n"
                                    "`/ping` - Mostra a latência do bot\n"
                                    "`/serverinfo` - Exibe informações do servidor\n"
                                    "`/userinfo` - Exibe informações de um usuário\n"
                                    "`/avatar` - Mostra o avatar de um usuário",
                              inline=False)

        help_embed.add_field(name="⚙️ Comandos de Configuração",
                              value="`/setup_logs` - Configura o canal de logs de moderação",
                              inline=False)
        
        help_embed.set_footer(text=f"Prefix: {self.bot.command_prefix}")
        await interaction.response.send_message(embed=help_embed, ephemeral=True)

    @app_commands.command(name="ping", description="Mostra a latência do bot.")
    async def ping_cmd(self, interaction: discord.Interaction):
        # A latência é geralmente calculada a partir do websocket
        latency_ms = round(self.bot.latency * 1000)
        await interaction.response.send_message(embed=info("Latência do Bot", f"🏓 Pong! `{latency_ms}ms`"), ephemeral=True)

    @app_commands.command(name="serverinfo", description="Exibe informações sobre o servidor atual.")
    async def serverinfo_cmd(self, interaction: discord.Interaction):
        guild = interaction.guild
        if not guild:
            return await interaction.response.send_message(embed=info("Info", "Este comando só pode ser usado em um servidor."), ephemeral=True)

        embed = discord.Embed(title=f"Informações do Servidor: {guild.name}", color=EMBED_COLOR)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        if guild.banner:
            embed.set_image(url=guild.banner.url)

        embed.add_field(name="ID do Servidor", value=guild.id, inline=True)
        embed.add_field(name="Dono", value=guild.owner.mention if guild.owner else "N/A", inline=True)
        embed.add_field(name="Criado em", value=discord.utils.format_dt(guild.created_at, "F"), inline=True)
        embed.add_field(name="Membros", value=f"Total: {guild.member_count}\nBots: {len([m for m in guild.members if m.bot])}", inline=True)
        embed.add_field(name="Canais", value=f"Texto: {len(guild.text_channels)}\nVoz: {len(guild.voice_channels)}\nCategorias: {len(guild.categories)}", inline=True)
        embed.add_field(name="Cargos", value=len(guild.roles), inline=True)
        embed.add_field(name="Boosts", value=f"Nível {guild.premium_tier} com {guild.premium_subscription_count} boosts", inline=True)
        embed.add_field(name="Região", value=str(guild.preferred_locale).upper(), inline=True)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="userinfo", description="Exibe informações de um usuário.")
    async def userinfo_cmd(self, interaction: discord.Interaction, user: discord.Member = None):
        target_user = user or interaction.user
        
        if not target_user:
            return await interaction.response.send_message(embed=error("Erro", "Não foi possível encontrar o usuário."), ephemeral=True)

        embed = discord.Embed(title=f"Informações de {target_user.display_name}", color=target_user.color if target_user.color != discord.Color.default() else EMBED_COLOR)
        if target_user.avatar:
            embed.set_thumbnail(url=target_user.avatar.url)
        elif target_user.display_avatar:
             embed.set_thumbnail(url=target_user.display_avatar.url)

        embed.add_field(name="ID", value=target_user.id, inline=True)
        embed.add_field(name="Nome de Usuário", value=target_user.name, inline=True)
        embed.add_field(name="Apelido", value=target_user.nick or "Nenhum", inline=True)
        embed.add_field(name="Conta Criada", value=discord.utils.format_dt(target_user.created_at, "F"), inline=False)
        
        if isinstance(target_user, discord.Member):
            embed.add_field(name="Entrou no Servidor", value=discord.utils.format_dt(target_user.joined_at, "F"), inline=False)
            roles = [role.mention for role in target_user.roles if role.name != "@everyone"]
            if roles:
                embed.add_field(name=f"Cargos ({len(roles)})", value=" ".join(roles) if len(roles) < 10 else f"{len(roles)} cargos", inline=False)
            
            if target_user.timed_out_until:
                embed.add_field(name="Em Tempo de Espera Até", value=discord.utils.format_dt(target_user.timed_out_until, "F"), inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="avatar", description="Mostra o avatar de um usuário.")
    async def avatar_cmd(self, interaction: discord.Interaction, user: discord.Member = None):
        target_user = user or interaction.user
        
        avatar_url = target_user.avatar.url if target_user.avatar else target_user.default_avatar.url
        
        embed = discord.Embed(title=f"Avatar de {target_user.display_name}", color=EMBED_COLOR)
        embed.set_image(url=avatar_url)
        embed.set_footer(text=f"Solicitado por {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Utility(bot))