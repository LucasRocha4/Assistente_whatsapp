"""Gemini. Por enquanto sem memória: cada mensagem é uma chamada independente."""
import logging

from google import genai
from google.genai import types

from . import config

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    """Cria o cliente na primeira chamada, para um erro de chave não derrubar o import."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=config.GEMINI_KEY)
    return _client


async def responder(texto: str) -> str | None:
    try:
        resp = await _get_client().aio.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=texto[: config.MAX_ENTRADA],
            config=types.GenerateContentConfig(
                system_instruction=config.SYSTEM_PROMPT,
                max_output_tokens=config.MAX_SAIDA,
            ),
        )
    except Exception:
        logger.exception("Erro ao chamar o Gemini")
        return None

    if not resp.text:
        logger.warning("Gemini devolveu resposta vazia")
        return None
    return resp.text
