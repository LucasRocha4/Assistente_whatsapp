import logging
import uvicorn
from fastapi import FastAPI, Request, BackgroundTasks
from tratamentos.ligacoes import tratar_chamada
from tratamentos.mensagens import TratarMensagem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

HANDLER = {
    "Message": TratarMensagem.tratar,
    "CallOffer": tratar_chamada,
}


@app.post("/evolution-webhook")
async def evolution_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        payload = await request.json()
    except Exception:
        logger.warning("Payload não é JSON válido")
        return {"status": "ignored"}

    event_type = payload.get("event")
    handler = HANDLER.get(event_type)

    if handler is None:
        logger.info("Evento ignorado: %s", event_type)
        return {"status": "ignored"}

    background_tasks.add_task(handler, payload)
    return {"status": "success"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8100)