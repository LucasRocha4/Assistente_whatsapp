import os
import logging
from pathlib import Path

import httpx
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

env_path = Path(__file__).resolve().parents[1] / "evolution-go" / ".env"
load_dotenv(dotenv_path=env_path)

EVOLUTION_URL = "http://localhost:4000"
API_KEY = os.getenv("GLOBAL_API_KEY")

if not API_KEY:
    logger.warning("GLOBAL_API_KEY vazia: confira o caminho do .env (%s)", env_path)

# evita atender duas vezes a mesma ligação se o webhook repetir
chamadas_tratadas = set()


def achar(obj, *chaves):
    """Procura a primeira chave encontrada em qualquer nível do JSON."""
    if isinstance(obj, dict):
        for chave in chaves:
            if chave in obj and obj[chave] is not None:
                return obj[chave]
        for v in obj.values():
            r = achar(v, *chaves)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = achar(v, *chaves)
            if r is not None:
                return r
    return None


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
    creator = montar_creator(call_creator)
    body = {"callId": call_id, "callCreator": creator}
    url = f"{EVOLUTION_URL.rstrip('/')}/call/answer"

    logger.info("Atendendo ligação %s | url=%s | body=%s", call_id, url, body)

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            url,
            json=body,
            headers={"apikey": API_KEY or ""},
        )

    logger.info("Resposta do Evolution: %s - %s", response.status_code, response.text)
    return response.status_code == 200


async def tratar_chamada(payload: dict):
    call_id = achar(payload, "callId", "call_id", "CallID")
    call_creator = achar(payload, "callCreator", "call_creator", "CallCreator")

    if not call_id or not call_creator:
        logger.warning("CallOffer sem callId/callCreator, confira o payload")
        return

    if call_id in chamadas_tratadas:
        logger.info("Chamada %s já tratada, ignorando repetição", call_id)
        return
    chamadas_tratadas.add(call_id)

    try:
        ok = await atende_ligacao(call_id, call_creator)
        logger.info("Atendimento da chamada %s: %s", call_id, "OK" if ok else "FALHOU")
    except Exception:
        logger.exception("Erro ao atender chamada %s", call_id)