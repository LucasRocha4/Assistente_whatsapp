import logging
import sys
from mcp.server.fastmcp import FastMCP
from db_config.db_path import get_connection
from tratamentos.contatos import TratamentoContatos

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

try:
    get_connection().close()
except Exception:
    logger.exception("Erro ao conectar ao banco de dados")
    sys.exit(1)

server = FastMCP("contatos")
tratamento_contatos = TratamentoContatos()


@server.tool()
def salvar_contato(chat: str) -> dict:
    return tratamento_contatos.salvar_contato(chat)


@server.tool()
def buscar_contato(numero: str) -> dict:
    return tratamento_contatos.buscar_contato(numero)


@server.tool()
def isspam(numero: str) -> dict:
    return {"result": tratamento_contatos.verificar_spam(numero)}


if __name__ == "__main__":
    server.run()