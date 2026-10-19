import asyncio
from tratamentos.envio import enviar_mensagem

import logging
logging.basicConfig(level=logging.INFO)

async def main():
    ok = await enviar_mensagem("5511943943535@s.whatsapp.net", "teste do bot")
    logging.info("enviado: %s", ok)

asyncio.run(main())