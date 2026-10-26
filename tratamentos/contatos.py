import logging
import sqlite3

from db_config.db_path import get_connection

logger = logging.getLogger(__name__)


class TratamentoContatos:
    def salvar_contato(self, chat: str) -> dict:
        """Salva o contato. `chat` pode ser o JID inteiro ou só o número.

        Retorno: 'sucesso' (False se já existia ou deu erro) e 'criado'
        (True só quando foi inserido agora, útil para detectar primeiro contato).
        """
        if not chat:
            return {"sucesso": False, "criado": False, "mensagem": "Campo 'chat' é obrigatório"}

        contato = chat.split("@")[0]
        conexao = None
        try:
            conexao = get_connection()
            cursor = conexao.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO contatos (numero, nome) VALUES (?, ?)",
                (contato, contato),
            )
            conexao.commit()
            if cursor.rowcount == 0:
                return {"sucesso": False, "criado": False, "mensagem": "contato já existe"}
            return {"sucesso": True, "criado": True, "mensagem": "contato salvo"}
        except sqlite3.Error:
            logger.exception("Erro ao salvar contato")
            return {"sucesso": False, "criado": False, "mensagem": "Erro ao salvar contato"}
        finally:
            if conexao:
                conexao.close()

    def buscar_contato(self, numero: str) -> dict:
        conexao = None
        try:
            conexao = get_connection()
            conexao.row_factory = sqlite3.Row
            cursor = conexao.cursor()
            cursor.execute("SELECT * FROM contatos WHERE numero = ?", (numero,))
            row = cursor.fetchone()
            if row is None:
                return {"sucesso": False, "mensagem": "Contato não encontrado"}
            return {"sucesso": True, "contato": dict(row)}
        except sqlite3.Error:
            logger.exception("Erro ao buscar contato")
            return {"sucesso": False, "mensagem": "Erro ao buscar contato"}
        finally:
            if conexao:
                conexao.close()

    def verificar_spam(self, numero: str) -> bool:
        conexao = None
        try:
            conexao = get_connection()
            cursor = conexao.cursor()
            cursor.execute(
                "SELECT 1 FROM contatos WHERE numero = ? AND isspam = 1 LIMIT 1",
                (numero,),
            )
            return cursor.fetchone() is not None
        except sqlite3.Error:
            logger.exception("Erro ao verificar spam")
            return False
        finally:
            if conexao:
                conexao.close()
