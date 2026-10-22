"""Funções puras para lidar com identificadores (JIDs) do WhatsApp."""
import re

SUFIXO_INDIVIDUAL = "@s.whatsapp.net"


def normalizar_numero(jid: str) -> str:
    """Converte um JID em só dígitos.

    '5511999999999@s.whatsapp.net'   -> '5511999999999'
    '5511999999999:7@s.whatsapp.net' -> '5511999999999'  (remove o sufixo de dispositivo)
    """
    if not jid:
        return ""
    usuario = jid.split("@")[0].split(":")[0]
    return re.sub(r"\D", "", usuario)


def conversa_individual(chat: str) -> bool:
    return bool(chat) and chat.endswith(SUFIXO_INDIVIDUAL)
