"""Gemini com contexto recente da conversa."""
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


async def responder(texto: str, historico: list[dict] | None = None) -> str | None:
    partes = ["Histórico recente da conversa:"]
    for item in historico or []:
        autor = "Rock" if item["direcao"] == "enviada" else item["remetente_id"]
        partes.append(f"[{item['data_hora']}] {autor}: {item['mensagem']}")
    partes.append(f"\nMensagem atual: {texto}")

    modelos = dict.fromkeys([config.GEMINI_MODEL, *config.MODELOS_FALLBACK])
    ultimo_erro = None

    for modelo in modelos:
        try:
            resp = await _get_client().aio.models.generate_content(
                model=modelo,
                contents="\n".join(partes)[: config.MAX_ENTRADA],
                config=types.GenerateContentConfig(
                    system_instruction=config.SYSTEM_PROMPT,
                    max_output_tokens=config.MAX_SAIDA,
                ),
            )
        except Exception as erro:
            ultimo_erro = erro
            logger.warning(
                "Modelo %s falhou; tentando o próximo fallback: %s",
                modelo,
                erro,
            )
            continue

        if resp.text:
            if modelo != config.GEMINI_MODEL:
                logger.info("Resposta gerada pelo modelo fallback %s", modelo)
            return resp.text

        logger.warning("Modelo %s devolveu resposta vazia", modelo)

    logger.error("Todos os modelos Gemini falharam; último erro: %s", ultimo_erro)
    return None
