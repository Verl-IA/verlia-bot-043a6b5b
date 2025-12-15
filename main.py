import asyncio
import discord
import logging
import os
from datetime import datetime
from discord.ext import commands, tasks

"""Moderador - Criado com Verl.ia Ultimate"""

# Configuração de logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(name)s | %(message)s')
log = logging.getLogger('bot')

# Configuração de intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

class Bot(commands.Bot):
    """Classe Bot."""
    def __init__(self):
        super().__init__(command_prefix='!', intents=intents, help_command=None)
    
    async def setup_hook(self):
        # Carrega as cogs
        initial_extensions = [
            'cogs.moderation',
            'cogs.utility',
            'cogs.events',
            'cogs.settings'
        ]
        for cog in initial_extensions:
            try:
                await self.load_extension(cog)
                log.info(f'✅ Cog {cog} carregada com sucesso.')
            except Exception as e:
                log.error(f'❌ Erro ao carregar cog {cog}: {e}')
        
        # Sincroniza os comandos de barra com o Discord
        await self.tree.sync()
        log.info('Comandos de barra sincronizados com sucesso.')
        
        # Inicia a task de verificação de mutes
        self.check_mutes.start()
    
    async def on_ready(self):
        log.info(f'🤖 {self.user} está online em {len(self.guilds)} servidores.')
        await self.change_presence(activity=discord.Game('!help'))

    @tasks.loop(minutes=1)
    async def check_mutes(self):
        from utils.database import db # Importa aqui para evitar circular dependency
        from config import MOD_LOGS_CHANNEL_ID
        
        now = datetime.utcnow().timestamp()
        
        # Busca por mutes que já deveriam ter terminado
        # Note: A função 'get' do seu 'db' não permite filtros complexos diretamente como '<'. 
        # Terei que pegar todos e filtrar no código. Este é um design de banco de dados simplificado.
        # Em um sistema real, o DB permitiria consultas mais eficientes.
        all_mutes = await db.get("mutes")
        if not all_mutes:
            return

        for mute_record in all_mutes:
            try:
                if mute_record.get('ends_at') and float(mute_record['ends_at']) <= now:
                    guild_id = int(mute_record['guild_id'])
                    user_id = int(mute_record['user_id'])
                    
                    guild = self.get_guild(guild_id)
                    if not guild:
                        log.warning(f"Guild {guild_id} não encontrada para unmute de {user_id}. Removendo mute do DB.")
                        await db.delete("mutes", {"user_id": mute_record['user_id'], "guild_id": mute_record['guild_id']})
                        continue
                    
                    member = guild.get_member(user_id)
                    if not member:
                        log.warning(f"Membro {user_id} não encontrado na guild {guild_id} para unmute. Removendo mute do DB.")
                        await db.delete("mutes", {"user_id": mute_record['user_id'], "guild_id": mute_record['guild_id']})
                        continue

                    # Tenta remover o timeout
                    if member.timed_out_until:
                        try:
                            await member.edit(timed_out_until=None, reason="Tempo de espera automático expirado.")
                            log.info(f"Membro {member.name} ({member.id}) desmutado automaticamente na guild {guild.name} ({guild.id}).")
                            
                            # Log no canal de moderação
                            settings = await db.get_one("guild_settings", {"guild_id": str(guild.id)})
                            if settings and settings.get("mod_logs_channel_id"):
                                logs_channel = guild.get_channel(int(settings["mod_logs_channel_id"]))
                                if logs_channel:
                                    embed = discord.Embed(
                                        title="✅ Usuário desmutado automaticamente",
                                        description=f"**Usuário:** {member.mention} (`{member.id}`)\n"
                                                    f"**Motivo:** Tempo de espera expirado.",
                                        color=discord.Color.green(),
                                        timestamp=datetime.utcnow()
                                    )
                                    embed.set_thumbnail(url=member.display_avatar.url)
                                    await logs_channel.send(embed=embed)

                        except discord.Forbidden:
                            log.error(f"Não tenho permissão para desmutar {member.name} ({member.id}) na guild {guild.name} ({guild.id}).")
                        except Exception as e:
                            log.error(f"Erro ao desmutar {member.name} ({member.id}) na guild {guild.name} ({guild.id}): {e}")

                    # Remove o registro do banco de dados
                    await db.delete("mutes", {"user_id": mute_record['user_id'], "guild_id": mute_record['guild_id']})
            except Exception as e:
                log.error(f"Erro na verificação de mute para {mute_record.get('user_id')}: {e}")

    @check_mutes.before_loop
    async def before_check_mutes(self):
        await self.wait_until_ready()

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send('❌ Você não tem permissão para usar este comando!', ephemeral=True)
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(f'❌ Eu não tenho as permissões necessárias para executar este comando: `{", ".join(error.missing_permissions)}`', ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f'❌ Faltou um argumento necessário: `{error.param.name}`', ephemeral=True)
        elif isinstance(error, commands.CommandNotFound):
            pass # Ignora comandos não encontrados
        else:
            log.error(f"Erro no comando {ctx.command}: {error}")
            await ctx.send(f'❌ Ocorreu um erro inesperado: `{error}`', ephemeral=True)

bot = Bot()

# Carrega o token do bot da variável de ambiente
bot.run(os.environ.get('BOT_TOKEN'))