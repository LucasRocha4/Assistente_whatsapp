import logging
import json

import uvicorn
from fastapi import FastAPI, Request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


@app.post("/evolution-webhook")
async def evolution_webhook(request: Request):
    try:
        payload = await request.json()
    except Exception:
        logger.warning("Payload não é JSON válido")
        return {"status": "ignored"}

    event_type = payload.get("event")
    logger.info("Evento: %s", event_type)
    logger.info("Payload:\n%s", json.dumps(payload, indent=2, ensure_ascii=False))

    return {"status": "success"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8100)