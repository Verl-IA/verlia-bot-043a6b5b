import discord
from config import EMBED_COLOR, SUCCESS_COLOR, ERROR_COLOR, WARNING_COLOR, INFO_COLOR

"""Funções para criar Embeds padronizados."""

def _create_embed(title: str, description: str = None, color: int = EMBED_COLOR, icon: str = None) -> discord.Embed:
    """Função interna para criar um embed base."""
    if icon:
        title = f"{icon} {title}"
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    return embed

def success(title: str, description: str = None) -> discord.Embed:
    """Cria um embed de sucesso (verde)."""
    return _create_embed(title, description, color=SUCCESS_COLOR, icon="✅")

def error(title: str, description: str = None) -> discord.Embed:
    """Cria um embed de erro (vermelho)."""
    return _create_embed(title, description, color=ERROR_COLOR, icon="❌")

def warning(title: str, description: str = None) -> discord.Embed:
    """Cria um embed de aviso (amarelo)."""
    return _create_embed(title, description, color=WARNING_COLOR, icon="⚠️")

def info(title: str, description: str = None) -> discord.Embed:
    """Cria um embed de informação (azul claro)."""
    return _create_embed(title, description, color=INFO_COLOR, icon="ℹ️")

def default_embed(title: str, description: str = None) -> discord.Embed:
    """Cria um embed com a cor padrão do bot."""
    return _create_embed(title, description, color=EMBED_COLOR)