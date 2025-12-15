import discord
import logging
from config import SUCCESS_COLOR, ERROR_COLOR
from discord import app_commands
from discord.ext import commands
from utils.database import db
from utils.embeds import success, error, info

"""Configuração do Bot"""

log = logging.getLogger('bot')

class Settings(commands.Cog):
    """Classe Settings."""
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup_logs", description="Define o canal para logs de moderação e eventos.")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_logs(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)
        
        # Verifica se o bot tem permissão de enviar mensagens no canal
        if not channel.permissions_for(interaction.guild.me).send_messages:
            return await interaction.response.send_message(embed=error("Erro de Permissão", f"Eu não tenho permissão para enviar mensagens no canal {channel.mention}."), ephemeral=True)

        try:
            # Tenta encontrar a configuração existente
            existing_settings = await db.get_one("guild_settings", {"guild_id": guild_id})
            
            if existing_settings:
                # Atualiza a configuração existente
                await db.update("guild_settings", {"guild_id": guild_id}, {"mod_logs_channel_id": str(channel.id)})
                response_embed = success("Configuração Atualizada", f"O canal de logs de moderação foi atualizado para {channel.mention}.")
            else:
                # Cria uma nova configuração
                await db.save("guild_settings", {"guild_id": guild_id, "mod_logs_channel_id": str(channel.id)})
                response_embed = success("Configuração Salva", f"O canal de logs de moderação foi definido para {channel.mention}.")
            
            await interaction.response.send_message(embed=response_embed, ephemeral=True)
            
            # Envia uma mensagem de teste no canal configurado
            test_embed = info("Logs Configurados!", f"Este canal ({channel.mention}) foi definido como o canal de logs de moderação por {interaction.user.mention}.")
            await channel.send(embed=test_embed)

        except Exception as e:
            log.error(f"Erro ao configurar canal de logs para a guilda {guild_id}: {e}")
            await interaction.response.send_message(embed=error("Erro", f"Ocorreu um erro ao configurar o canal de logs: `{e}`"), ephemeral=True)

    @app_commands.command(name="show_settings", description="Exibe as configurações atuais do bot para este servidor.")
    @app_commands.checks.has_permissions(administrator=True)
    async def show_settings(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        settings = await db.get_one("guild_settings", {"guild_id": guild_id})

        embed = info("Configurações do Servidor", "Configurações atuais do bot para esta guilda.")

        if settings:
            mod_logs_channel_id = settings.get("mod_logs_channel_id")
            if mod_logs_channel_id:
                mod_logs_channel = interaction.guild.get_channel(int(mod_logs_channel_id))
                embed.add_field(name="Canal de Logs de Moderação", value=mod_logs_channel.mention if mod_logs_channel else f"ID: `{mod_logs_channel_id}` (Não encontrado)", inline=False)
            else:
                embed.add_field(name="Canal de Logs de Moderação", value="Não configurado", inline=False)
        else:
            embed.add_field(name="Nenhuma Configuração", value="Nenhuma configuração específica encontrada para este servidor.", inline=False)
            
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Settings(bot))