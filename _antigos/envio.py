import logging
import os
import re
from pathlib import Path

import httpx
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

env_path = Path(__file__).resolve().parents[1] / "evolution-go" / ".env"
load_dotenv(dotenv_path=env_path)

EVOLUTION_SETUP = {
    "apikey": os.getenv("EVOLUTION_INSTANCE_TOKEN"),
    "base_url": os.getenv("EVOLUTION_BASE_URL", "http://localhost:4000"),
}

if not EVOLUTION_SETUP["apikey"]:
    raise RuntimeError(
        f"EVOLUTION_INSTANCE_TOKEN não definido, confira o .env em {env_path}"
    )


def separar_numero(phone: str) -> str:
    """Remove o sufixo @... e mantém só os dígitos."""
    if "@" in phone:
        phone = phone.split("@")[0]
    return re.sub(r"\D", "", phone)


async def enviar_mensagem(destino: str, mensagem: str) -> bool:
    numero = separar_numero(destino)
    if not numero or not mensagem.strip():
        logger.warning("Envio cancelado: número ou texto vazio")
        return False

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{EVOLUTION_SETUP['base_url']}/send/text",
                json={"number": numero, "text": mensagem},
                headers={"apikey": EVOLUTION_SETUP["apikey"]},
            )
    except httpx.HTTPError:
        logger.exception("Falha de rede ao enviar para %s", numero)
        return False

    logger.info("Evolution respondeu %s: %s", response.status_code, response.text)

    if not response.is_success:
        return False

    logger.info("Mensagem enviada para %s", numero)
    return True