import os
import logging
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

env_path = Path(__file__).resolve().parents[1] / "evolution-go" / ".env"
load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("GEMINI_KEY")
MODELO = os.getenv("MODELO", "gemini-3.1-flash-lite")
MAX_ENTRADA = int(os.getenv("MAX_ENTRADA", 1000))  # caracteres da mensagem
MAX_SAIDA = int(os.getenv("MAX_SAIDA", 500))       # tokens da resposta
SYSTEM = "Você é um assistente no WhatsApp. Responda de forma curta e direta."

if not API_KEY:
    raise RuntimeError(f"GEMINI_KEY não encontrada. Confira o .env em {env_path}")

client = genai.Client(api_key=API_KEY)


async def responder(texto: str) -> str | None:
    try:
        resp = await client.aio.models.generate_content(
            model=MODELO,
            contents=texto[:MAX_ENTRADA],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM,
                max_output_tokens=MAX_SAIDA,
            ),
        )
    except Exception:
        logger.exception("Erro ao chamar o Gemini")
        return None

    if not resp.text:
        logger.warning("Gemini devolveu resposta vazia")
        return None
    return resp.text