import discord
from discord.ext import commands

"""Verificações customizadas para comandos."""

"""
Não é recomendado usar `commands.check` com `/` (slash commands) diretamente.
Para comandos de barra, use `@app_commands.checks.has_permissions()`
ou crie seus próprios decoradores customizados com `app_commands.check`.

Exemplo de uso em cog:
@app_commands.command(name="comando", description="Descrição")
@app_commands.checks.has_permissions(administrator=True) # Exemplo de permissão
async def comando(self, interaction: discord.Interaction):
    pass
"""

# Mantido por compatibilidade se houver comandos de texto no futuro, mas priorize app_commands.checks para slash commands
def is_admin():
    """Verifica se o autor do comando tem permissões de administrador."""
    async def predicate(ctx):
        if not ctx.guild:
            raise commands.NoPrivateMessage("Este comando não pode ser usado em mensagens diretas.")
        if not ctx.author.guild_permissions.administrator:
            raise commands.MissingPermissions(["administrator"])
        return True
    return commands.check(predicate)

def is_mod():
    """Verifica se o autor do comando tem permissões de gerenciar mensagens."""
    async def predicate(ctx):
        if not ctx.guild:
            raise commands.NoPrivateMessage("Este comando não pode ser usado em mensagens diretas.")
        if not ctx.author.guild_permissions.manage_messages:
            raise commands.MissingPermissions(["manage_messages"])
        return True
    return commands.check(predicate)