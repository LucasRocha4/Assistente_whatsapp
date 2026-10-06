from fastapi import FastAPI, Request, Response
from db_config.db_path import get_connection
import uvicorn

app = FastAPI()

@app.post("/evolution-webhook")
async def evolution_webhook(request: Request):
    payload = await request.json()

    event_type = payload.get("event")

    print(f"Tipo de evento: {event_type}\nConteúdo do payload: {payload}")
    return {"status": "success"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8100)