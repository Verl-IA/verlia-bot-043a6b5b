import discord
import logging
import re
from config import SUCCESS_COLOR, WARNING_COLOR
from datetime import datetime
from discord.ext import commands
from utils.database import db
from utils.embeds import info

"""Eventos do Bot (on_member_join, on_member_remove)"""

log = logging.getLogger('bot')

class Events(commands.Cog):
    """Classe Events."""
    def __init__(self, bot):
        self.bot = bot
    
    async def _log_event(self, guild: discord.Guild, embed: discord.Embed):
        """Envia um embed para o canal de logs de moderação da guilda, se configurado."""
        settings = await db.get_one("guild_settings", {"guild_id": str(guild.id)})
        if settings and settings.get("mod_logs_channel_id"):
            channel_id = int(settings["mod_logs_channel_id"])
            channel = guild.get_channel(channel_id)
            if channel and isinstance(channel, discord.TextChannel):
                try:
                    await channel.send(embed=embed)
                except discord.Forbidden:
                    log.warning(f"Não tenho permissão para enviar logs no canal '{channel.name}' ({channel.id}) da guilda '{guild.name}' ({guild.id}).")
            else:
                log.warning(f"Canal de logs {channel_id} não é um canal de texto ou não existe na guilda '{guild.name}' ({guild.id}).")
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild.system_channel:
            join_embed = info("👋 Novo Membro!", f"Bem-vindo {member.mention} ao servidor {member.guild.name}!\nEsperamos que se divirta conosco.")
            join_embed.set_thumbnail(url=member.display_avatar.url)
            join_embed.set_footer(text=f"ID: {member.id} | Membros: {member.guild.member_count}")
            try:
                await member.guild.system_channel.send(embed=join_embed)
            except discord.Forbidden:
                log.warning(f"Não consigo enviar mensagem de boas-vindas no canal de sistema de {member.guild.name}.")
        
        # Log de entrada no canal de moderação
        mod_log_embed = discord.Embed(
            title="➡️ Membro Entrou",
            description=f"**Usuário:** {member.mention} (`{member.id}`)\n"
                        f"**Criado em:** <t:{int(member.created_at.timestamp())}:F>",
            color=SUCCESS_COLOR,
            timestamp=datetime.utcnow()
        )
        mod_log_embed.set_thumbnail(url=member.display_avatar.url)
        await self._log_event(member.guild, mod_log_embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if member.guild.system_channel:
            leave_embed = info("👋 Membro Saiu", f"{member.mention} deixou o servidor {member.guild.name}.")
            leave_embed.set_thumbnail(url=member.display_avatar.url)
            leave_embed.set_footer(text=f"ID: {member.id} | Membros: {member.guild.member_count}")
            try:
                await member.guild.system_channel.send(embed=leave_embed)
            except discord.Forbidden:
                log.warning(f"Não consigo enviar mensagem de saída no canal de sistema de {member.guild.name}.")
        
        # Log de saída no canal de moderação
        mod_log_embed = discord.Embed(
            title="⬅️ Membro Saiu",
            description=f"**Usuário:** {member.mention} (`{member.id}`)",
            color=WARNING_COLOR,
            timestamp=datetime.utcnow()
        )
        mod_log_embed.set_thumbnail(url=member.display_avatar.url)
        await self._log_event(member.guild, mod_log_embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        # Ignora mensagens de bots e DMs
        if before.author.bot or not before.guild:
            return
        
        # Ignora se o conteúdo não mudou ou se não é um canal de texto
        if before.content == after.content or not isinstance(before.channel, discord.TextChannel):
            return

        embed = discord.Embed(
            title="✏️ Mensagem Editada",
            description=(f"**Autor:** {before.author.mention} (`{before.author.id}`)\n"
                         f"**Canal:** {before.channel.mention}\n"
                         f"[Ir para a mensagem]({after.jump_url})"),
            color=WARNING_COLOR,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Antes", value=discord.utils.escape_markdown(before.content[:1020]), inline=False)
        embed.add_field(name="Depois", value=discord.utils.escape_markdown(after.content[:1020]), inline=False)
        embed.set_footer(text=f"ID da Mensagem: {after.id}")
        embed.set_thumbnail(url=before.author.display_avatar.url)
        await self._log_event(before.guild, embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        # Ignora mensagens de bots e DMs
        if message.author.bot or not message.guild:
            return
        
        # Ignora se não é um canal de texto
        if not isinstance(message.channel, discord.TextChannel):
            return

        embed = discord.Embed(
            title="🗑️ Mensagem Deletada",
            description=(f"**Autor:** {message.author.mention} (`{message.author.id}`)\n"
                         f"**Canal:** {message.channel.mention}"),
            color=ERROR_COLOR,
            timestamp=datetime.utcnow()
        )
        if message.content:
            embed.add_field(name="Conteúdo", value=discord.utils.escape_markdown(message.content[:1020]), inline=False)
        if message.attachments:
            attachments_str = "\n".join([f"[{attachment.filename}]({attachment.url})" for attachment in message.attachments])
            embed.add_field(name="Anexos", value=attachments_str[:1020], inline=False)

        embed.set_footer(text=f"ID da Mensagem: {message.id}")
        embed.set_thumbnail(url=message.author.display_avatar.url)
        await self._log_event(message.guild, embed)

async def setup(bot):
    await bot.add_cog(Events(bot))