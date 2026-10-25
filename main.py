import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import BackgroundTasks, FastAPI, Request

from tratamentos import config
from tratamentos.handlers import tratar_chamada, tratar_mensagem
from tratamentos.historico import HistoricoConversas

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# evento do Evolution -> função que trata (todas recebem o payload inteiro)
HANDLER = {
    "Message": tratar_mensagem,
    "CallOffer": tratar_chamada,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    config.validar()  # falha cedo se faltar alguma chave no .env
    await asyncio.to_thread(HistoricoConversas().inicializar)
    yield


app = FastAPI(lifespan=lifespan)


async def executar(handler, payload: dict) -> None:
    """Roda o handler em segundo plano registrando qualquer erro com traceback."""
    try:
        await handler(payload)
    except Exception:
        logger.exception("Erro no handler %s", getattr(handler, "__name__", handler))


@app.post("/evolution-webhook")
async def evolution_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        payload = await request.json()
    except Exception:
        logger.warning("Payload não é JSON válido")
        return {"status": "ignored"}

    if not isinstance(payload, dict):
        logger.warning("Payload não é um objeto JSON")
        return {"status": "ignored"}

    event_type = payload.get("event")
    handler = HANDLER.get(event_type)

    if handler is None:
        logger.info("Evento ignorado: %s", event_type)
        return {"status": "ignored"}

    logger.info("Evento: %s", event_type)
    background_tasks.add_task(executar, handler, payload)
    return {"status": "success"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8100)
