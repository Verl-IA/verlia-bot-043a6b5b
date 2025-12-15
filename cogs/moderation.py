import asyncio
import discord
import logging
from config import SUCCESS_COLOR, ERROR_COLOR, WARNING_COLOR, PUNISHMENT_LEVELS
from datetime import datetime, timedelta
from discord import app_commands
from discord.ext import commands
from utils.database import db
from utils.embeds import success, error, warning, info

"""Comandos de Moderação do Bot"""

log = logging.getLogger('bot')

class Moderation(commands.Cog):
    """Classe Moderation."""
    def __init__(self, bot):
        self.bot = bot
    
    async def _send_mod_log(self, guild: discord.Guild, embed: discord.Embed):
        """Envia um embed para o canal de logs de moderação da guilda."""
        settings = await db.get_one("guild_settings", {"guild_id": str(guild.id)})
        if settings and settings.get("mod_logs_channel_id"):
            channel_id = int(settings["mod_logs_channel_id"])
            channel = guild.get_channel(channel_id)
            if channel and isinstance(channel, discord.TextChannel):
                try:
                    await channel.send(embed=embed)
                except discord.Forbidden:
                    log.warning(f"Não tenho permissão para enviar logs no canal {channel.name} ({channel.id}) da guilda {guild.name} ({guild.id}).")
            else:
                log.warning(f"Canal de logs {channel_id} não é um canal de texto ou não existe na guilda {guild.name} ({guild.id}).")
    
    @app_commands.command(name="ban", description="Bane um usuário do servidor.")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.bot_has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, user: discord.Member, reason: str = "Sem motivo especificado."):
        if user.id == interaction.user.id:
            return await interaction.response.send_message(embed=error("Erro", "Você não pode banir a si mesmo!"), ephemeral=True)
        if user.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message(embed=error("Erro", "Você não pode banir um membro com cargo igual ou superior ao seu."), ephemeral=True)
        if user.top_role >= interaction.guild.me.top_role:
           return await interaction.response.send_message(embed=error("Erro", "Não consigo banir este membro, o cargo dele é igual ou superior ao meu."), ephemeral=True)
        
        try:
            await user.ban(reason=reason)
            await db.save("bans", {
                "user_id": str(user.id),
                "guild_id": str(interaction.guild.id),
                "reason": reason,
                "moderator_id": str(interaction.user.id)
            })
            
            ban_embed = success("Usuário Banido", f"**Usuário:** {user.mention} (`{user.id}`)\n**Motivo:** {reason}\n**Moderador:** {interaction.user.mention}")
            ban_embed.set_thumbnail(url=user.display_avatar.url)
            await interaction.response.send_message(embed=ban_embed)
            
            await self._send_mod_log(interaction.guild, ban_embed)
        except discord.Forbidden:
            await interaction.response.send_message(embed=error("Erro de Permissão", "Não tenho permissão para banir este usuário."), ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(embed=error("Erro", f"Ocorreu um erro ao banir o usuário: `{e}`"), ephemeral=True)

    @app_commands.command(name="unban", description="Desbane um usuário do servidor.")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.bot_has_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, user_id: str, reason: str = "Sem motivo especificado."):
        try:
            user = await self.bot.fetch_user(int(user_id))
        except ValueError:
            return await interaction.response.send_message(embed=error("ID Inválido", "Por favor, forneça um ID de usuário válido."), ephemeral=True)
        except discord.NotFound:
            return await interaction.response.send_message(embed=error("Usuário Não Encontrado", "Não encontrei um usuário com este ID."), ephemeral=True)
        
        try:
            await interaction.guild.unban(user, reason=reason)
            await db.delete("bans", {"user_id": str(user.id), "guild_id": str(interaction.guild.id)})
            
            unban_embed = success("Usuário Desbanido", f"**Usuário:** {user.mention} (`{user.id}`)\n**Motivo:** {reason}\n**Moderador:** {interaction.user.mention}")
            unban_embed.set_thumbnail(url=user.display_avatar.url)
            await interaction.response.send_message(embed=unban_embed)
            
            await self._send_mod_log(interaction.guild, unban_embed)
        except discord.NotFound:
            await interaction.response.send_message(embed=error("Erro", "Este usuário não está banido do servidor."), ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message(embed=error("Erro de Permissão", "Não tenho permissão para desbanir este usuário."), ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(embed=error("Erro", f"Ocorreu um erro ao desbanir o usuário: `{e}`"), ephemeral=True)

    @app_commands.command(name="kick", description="Expulsa um usuário do servidor.")
    @app_commands.checks.has_permissions(kick_members=True)
    @app_commands.bot_has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, user: discord.Member, reason: str = "Sem motivo especificado."):
        if user.id == interaction.user.id:
            return await interaction.response.send_message(embed=error("Erro", "Você não pode se expulsar!"), ephemeral=True)
        if user.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message(embed=error("Erro", "Você não pode expulsar um membro com cargo igual ou superior ao seu."), ephemeral=True)
        if user.top_role >= interaction.guild.me.top_role:
           return await interaction.response.send_message(embed=error("Erro", "Não consigo expulsar este membro, o cargo dele é igual ou superior ao meu."), ephemeral=True)
        
        try:
            await user.kick(reason=reason)
            
            kick_embed = warning("Usuário Expulso", f"**Usuário:** {user.mention} (`{user.id}`)\n**Motivo:** {reason}\n**Moderador:** {interaction.user.mention}")
            kick_embed.set_thumbnail(url=user.display_avatar.url)
            await interaction.response.send_message(embed=kick_embed)
            
            await self._send_mod_log(interaction.guild, kick_embed)
        except discord.Forbidden:
            await interaction.response.send_message(embed=error("Erro de Permissão", "Não tenho permissão para expulsar este usuário."), ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(embed=error("Erro", f"Ocorreu um erro ao expulsar o usuário: `{e}`"), ephemeral=True)

    @app_commands.command(name="mute", description="Coloca um usuário em tempo de espera (timeout).")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.bot_has_permissions(moderate_members=True)
    async def mute_cmd(self, interaction: discord.Interaction, user: discord.Member, duration_minutes: int, reason: str = "Sem motivo especificado."):
        if user.id == interaction.user.id:
            return await interaction.response.send_message(embed=error("Erro", "Você não pode mutar a si mesmo!"), ephemeral=True)
        if user.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message(embed=error("Erro", "Você não pode mutar um membro com cargo igual ou superior ao seu."), ephemeral=True)
        if user.top_role >= interaction.guild.me.top_role:
           return await interaction.response.send_message(embed=error("Erro", "Não consigo mutar este membro, o cargo dele é igual ou superior ao meu."), ephemeral=True)
        if duration_minutes <= 0:
            return await interaction.response.send_message(embed=error("Duração Inválida", "A duração do mute deve ser um número positivo de minutos."), ephemeral=True)

        duration = timedelta(minutes=duration_minutes)
        ends_at = datetime.utcnow() + duration
        
        try:
            await user.timeout(ends_at, reason=reason)
            await db.save("mutes", {
                "user_id": str(user.id),
                "guild_id": str(interaction.guild.id),
                "moderator_id": str(interaction.user.id),
                "reason": reason,
                "ends_at": ends_at.timestamp() # Armazena o timestamp para fácil comparação
            })
            
            mute_embed = warning("Usuário Mutado", f"**Usuário:** {user.mention} (`{user.id}`)\n**Duração:** {duration_minutes} minutos\n**Motivo:** {reason}\n**Moderador:** {interaction.user.mention}")
            mute_embed.set_thumbnail(url=user.display_avatar.url)
            await interaction.response.send_message(embed=mute_embed)
            
            await self._send_mod_log(interaction.guild, mute_embed)
        except discord.Forbidden:
            await interaction.response.send_message(embed=error("Erro de Permissão", "Não tenho permissão para mutar este usuário."), ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(embed=error("Erro", f"Ocorreu um erro ao mutar o usuário: `{e}`"), ephemeral=True)

    @app_commands.command(name="unmute", description="Remove o tempo de espera (timeout) de um usuário.")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.bot_has_permissions(moderate_members=True)
    async def unmute_cmd(self, interaction: discord.Interaction, user: discord.Member, reason: str = "Sem motivo especificado."):
        if not user.timed_out_until:
            return await interaction.response.send_message(embed=info("Info", "Este usuário não está em tempo de espera."), ephemeral=True)
        
        try:
            await user.timeout(None, reason=reason) # Removendo o timeout
            await db.delete("mutes", {"user_id": str(user.id), "guild_id": str(interaction.guild.id)})
            
            unmute_embed = success("Usuário Desmutado", f"**Usuário:** {user.mention} (`{user.id}`)\n**Motivo:** {reason}\n**Moderador:** {interaction.user.mention}")
            unmute_embed.set_thumbnail(url=user.display_avatar.url)
            await interaction.response.send_message(embed=unmute_embed)
            
            await self._send_mod_log(interaction.guild, unmute_embed)
        except discord.Forbidden:
            await interaction.response.send_message(embed=error("Erro de Permissão", "Não tenho permissão para desmutar este usuário."), ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(embed=error("Erro", f"Ocorreu um erro ao desmutar o usuário: `{e}`"), ephemeral=True)

    @app_commands.command(name="warn", description="Adiciona uma advertência a um usuário.")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.bot_has_permissions(moderate_members=True)
    async def warn_cmd(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        if user.id == interaction.user.id:
            return await interaction.response.send_message(embed=error("Erro", "Você não pode se advertir!"), ephemeral=True)
        
        # Obter warns existentes
        all_warns = await db.get("warns", {"user_id": str(user.id), "guild_id": str(interaction.guild.id)})
        current_warn_count = len(all_warns) + 1
        
        # Salvar a nova advertência
        await db.save("warns", {
            "user_id": str(user.id),
            "guild_id": str(interaction.guild.id),
            "reason": reason,
            "moderator_id": str(interaction.user.id),
            "count": current_warn_count,
            "punishment_level": None # Será preenchido se uma punição automática for aplicada
        })
        
        warn_embed = warning(f"Advertência #{current_warn_count}", 
                             f"**Usuário:** {user.mention} (`{user.id}`)\n**Motivo:** {reason}\n**Moderador:** {interaction.user.mention}")
        warn_embed.set_thumbnail(url=user.display_avatar.url)
        await interaction.response.send_message(embed=warn_embed)
        await self._send_mod_log(interaction.guild, warn_embed)

        # Verificar níveis de punição automática
        for warn_threshold, punishment_info in PUNISHMENT_LEVELS.items():
            if current_warn_count == warn_threshold:
                action = punishment_info["action"]
                duration = punishment_info.get("duration") # duration em segundos
                
                punishment_reason = f"Punição automática: {warn_threshold} advertências."
                punishment_embed = None
                
                if action == "mute":
                    if user.top_role >= interaction.guild.me.top_role:
                        await interaction.followup.send(embed=error("Punição Automática Falhou", f"Não foi possível mutar {user.mention} (cargo igual ou superior ao meu)."), ephemeral=True)
                        punishment_embed = error("Punição Automática Falhou", f"Não foi possível mutar {user.mention}. Cargo do bot inferior.")
                        break
                    
                    ends_at = datetime.utcnow() + timedelta(seconds=duration)
                    try:
                        await user.timeout(ends_at, reason=punishment_reason)
                        await db.save("mutes", {
                            "user_id": str(user.id),
                            "guild_id": str(interaction.guild.id),
                            "moderator_id": str(self.bot.user.id), # Bot como moderador
                            "reason": punishment_reason,
                            "ends_at": ends_at.timestamp()
                        })
                        await db.update("warns", {"user_id": str(user.id), "guild_id": str(interaction.guild.id), "count": current_warn_count}, {"punishment_level": "MUTE"})
                        
                        punishment_embed = warning("Punição Automática Aplicada: Mute", 
                                                   f"**Usuário:** {user.mention} (`{user.id}`)\n**Motivo:** {punishment_reason}\n**Duração:** {duration // 60} minutos.")
                        punishment_embed.set_thumbnail(url=user.display_avatar.url)
                        await interaction.followup.send(embed=punishment_embed)
                    except discord.Forbidden:
                        await interaction.followup.send(embed=error("Punição Automática Falhou", f"Não tenho permissão para mutar {user.mention} automaticamente."), ephemeral=True)
                        punishment_embed = error("Punição Automática Falhou", f"Não tenho permissão para mutar {user.mention}.")
                    except Exception as e:
                        await interaction.followup.send(embed=error("Punição Automática Falhou", f"Erro ao mutar {user.mention} automaticamente: `{e}`"), ephemeral=True)
                        punishment_embed = error("Punição Automática Falhou", f"Erro ao mutar {user.mention}: `{e}`")
                        
                elif action == "ban":
                    if user.top_role >= interaction.guild.me.top_role:
                        await interaction.followup.send(embed=error("Punição Automática Falhou", f"Não foi possível banir {user.mention} (cargo igual ou superior ao meu)."), ephemeral=True)
                        punishment_embed = error("Punição Automática Falhou", f"Não foi possível banir {user.mention}. Cargo do bot inferior.")
                        break
                    
                    try:
                        await user.ban(reason=punishment_reason)
                        await db.save("bans", {
                            "user_id": str(user.id),
                            "guild_id": str(interaction.guild.id),
                            "reason": punishment_reason,
                            "moderator_id": str(self.bot.user.id) # Bot como moderador
                        })
                        await db.update("warns", {"user_id": str(user.id), "guild_id": str(interaction.guild.id), "count": current_warn_count}, {"punishment_level": "BAN"})
                        
                        punishment_embed = error("Punição Automática Aplicada: Banimento", 
                                                  f"**Usuário:** {user.mention} (`{user.id}`)\n**Motivo:** {punishment_reason}")
                        punishment_embed.set_thumbnail(url=user.display_avatar.url)
                        await interaction.followup.send(embed=punishment_embed)
                    except discord.Forbidden:
                        await interaction.followup.send(embed=error("Punição Automática Falhou", f"Não tenho permissão para banir {user.mention} automaticamente."), ephemeral=True)
                        punishment_embed = error("Punição Automática Falhou", f"Não tenho permissão para banir {user.mention}.")
                    except Exception as e:
                        await interaction.followup.send(embed=error("Punição Automática Falhou", f"Erro ao banir {user.mention} automaticamente: `{e}`"), ephemeral=True)
                        punishment_embed = error("Punição Automática Falhou", f"Erro ao banir {user.mention}: `{e}`")
                        
                if punishment_embed:
                    await self._send_mod_log(interaction.guild, punishment_embed)
                
                break # Apenas uma punição por vez por atingir o limite

    @app_commands.command(name="warns", description="Exibe as advertências de um usuário.")
    async def warns_list(self, interaction: discord.Interaction, user: discord.Member):
        warns = await db.get("warns", {"user_id": str(user.id), "guild_id": str(interaction.guild.id)})
        
        if not warns:
            return await interaction.response.send_message(embed=info("Sem Advertências", f"{user.mention} não possui advertências neste servidor."), ephemeral=True)
        
        warns_embed = warning(f"Advertências de {user.display_name}", f"Total de advertências: `{len(warns)}`")
        warns_embed.set_thumbnail(url=user.display_avatar.url)
        
        # Ordenar as advertências pela contagem
        warns_sorted = sorted(warns, key=lambda x: x.get('count', 0))

        for warn_data in warns_sorted:
            moderator = interaction.guild.get_member(int(warn_data["moderator_id"])) or "Desconhecido"
            punishment = warn_data.get("punishment_level", "Nenhuma")
            warns_embed.add_field(
                name=f"Advertência #{warn_data.get('count', '?')}",
                value=(f"**Motivo:** {warn_data['reason']}\n"
                       f"**Moderador:** {moderator.mention if isinstance(moderator, discord.Member) else moderator}\n"
                       f"**Data:** <t:{int(datetime.fromisoformat(warn_data['created_at'].replace('Z', '+00:00')).timestamp())}:F>\n"
                       f"**Punição Auto.:** {punishment}"),
                inline=False
            )
        
        await interaction.response.send_message(embed=warns_embed)

    @app_commands.command(name="clear_warns", description="Limpa todas as advertências de um usuário.")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.bot_has_permissions(moderate_members=True)
    async def clear_warns(self, interaction: discord.Interaction, user: discord.Member):
        warns_count = await db.count("warns", {"user_id": str(user.id), "guild_id": str(interaction.guild.id)})
        
        if warns_count == 0:
            return await interaction.response.send_message(embed=info("Info", f"{user.mention} não possui advertências para serem limpas."), ephemeral=True)
        
        await db.delete("warns", {"user_id": str(user.id), "guild_id": str(interaction.guild.id)})
        
        clear_embed = success("Advertências Limpas", f"Todas as `{warns_count}` advertências de {user.mention} foram removidas por {interaction.user.mention}.")
        clear_embed.set_thumbnail(url=user.display_avatar.url)
        await interaction.response.send_message(embed=clear_embed)
        await self._send_mod_log(interaction.guild, clear_embed)

    @app_commands.command(name="clear", description="Limpa um número específico de mensagens no canal.")
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.bot_has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: int):
        if amount <= 0:
            return await interaction.response.send_message(embed=error("Quantidade Inválida", "A quantidade de mensagens a limpar deve ser um número positivo."), ephemeral=True)
        if amount > 100:
            return await interaction.response.send_message(embed=error("Limite Excedido", "Você pode limpar no máximo 100 mensagens por vez."), ephemeral=True)
        
        try:
            # +1 para incluir a própria mensagem de comando após a resposta
            await interaction.response.send_message("Limpeza de mensagens em andamento...", ephemeral=True)
            deleted = await interaction.channel.purge(limit=amount, check=lambda m: not m.pinned) # Não apaga mensagens fixadas
            
            clear_embed = info("Mensagens Limpas", f"🗑️ `{len(deleted)}` mensagens foram apagadas por {interaction.user.mention} no canal {interaction.channel.mention}.")
            await self._send_mod_log(interaction.guild, clear_embed)
            
            await interaction.edit_original_response(content="", embed=success("Limpeza Completa", f"🗑️ `{len(deleted)}` mensagens apagadas neste canal."))
            
            # Deleta a mensagem de confirmação após um tempo
            #await asyncio.sleep(5)
            #await confirmation_message.delete()
            
        except discord.Forbidden:
            await interaction.edit_original_response(content="", embed=error("Erro de Permissão", "Não tenho permissão para gerenciar mensagens neste canal."))
        except Exception as e:
            await interaction.edit_original_response(content="", embed=error("Erro", f"Ocorreu um erro ao limpar as mensagens: `{e}`"))

async def setup(bot):
    await bot.add_cog(Moderation(bot))