import os

"""Configurações globais do bot"""

# Prefix para comandos de texto (se usado)
PREFIX = "!"

# Cores para embeds
EMBED_COLOR = 0x5865F2  # DiscordBlurple
SUCCESS_COLOR = 0x57F287  # DiscordGreen
ERROR_COLOR = 0xED4245    # DiscordRed
WARNING_COLOR = 0xFEE75C  # DiscordYellow
INFO_COLOR = 0x3b82f6 # Azul claro

# ID do bot (se necessário para comunicação interna ou DB)
BOT_ID = os.environ.get('BOT_ID', '043a6b5b-a2f1-4812-bd92-dfe68e69f56a')

# Níveis de punição automática (número de warns -> ação)
# Ex: 3 warns -> mute de 10 minutos, 5 warns -> ban
PUNISHMENT_LEVELS = {
    3: {"action": "mute", "duration": 600}, # 10 minutos
    5: {"action": "mute", "duration": 3600}, # 1 hora
    7: {"action": "ban", "duration": None} # Banimento permanente
}