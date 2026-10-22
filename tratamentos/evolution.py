"""Único módulo que conhece a API do Evolution Go (enviar mensagem e atender ligação)."""
import logging

import httpx

from . import config
from .numeros import normalizar_numero

logger = logging.getLogger(__name__)

TIMEOUT = 10.0


async def _post(caminho: str, corpo: dict, apikey: str | None) -> bool:
    """POST no Evolution. Retorna True só em 2xx. Nunca levanta erro de rede."""
    url = f"{config.EVOLUTION_URL}{caminho}"
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                url,
                json=corpo,
                headers={"apikey": apikey or ""},
            )
    except httpx.HTTPError:
        logger.exception("Falha de rede em %s", caminho)
        return False

    logger.info("Evolution respondeu %s em %s: %s", response.status_code, caminho, response.text)
    return response.is_success


async def enviar_mensagem(destino: str, mensagem: str) -> bool:
    """Envia texto. `destino` pode ser o Chat inteiro (…@s.whatsapp.net)."""
    numero = normalizar_numero(destino)
    if not numero or not mensagem or not mensagem.strip():
        logger.warning("Envio cancelado: número ou texto vazio")
        return False

    ok = await _post(
        "/send/text",
        {"number": numero, "text": mensagem},
        config.EVOLUTION_INSTANCE_TOKEN,
    )
    if ok:
        logger.info("Mensagem enviada para %s", numero)
    return ok


def montar_creator(valor) -> dict:
    """Aceita dict (repassa) ou string tipo '1405...@lid' (converte em objeto)."""
    if isinstance(valor, dict):
        return valor
    user, _, server = str(valor).partition("@")
    return {
        "user": user,
        "server": server,
        "device": 0,
        "integrator": 0,
        "rawAgent": 0,
    }


async def atende_ligacao(call_id: str, call_creator) -> bool:
    body = {"callId": call_id, "callCreator": montar_creator(call_creator)}
    logger.info("Atendendo ligação %s | body=%s", call_id, body)
    return await _post("/call/answer", body, config.GLOBAL_API_KEY)
