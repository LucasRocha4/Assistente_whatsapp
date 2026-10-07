from fastapi import Request
from db_config.db_path import get_connection
import sqlite3
import logging 

logger = logging.getLogger(__name__)

class tratamento_contatos:
    def __init__(self):
        pass

    async def salvar_contato(self, request: Request):
        # tratativa do contato
        data = await request.json()
        if not data.get("Chat"):
            return {"sucesso": False, "mensagem": "Campo 'Chat' é obrigatório"}
        
        contato = str(data.get("Chat"))[:str(data.get("Chat")).find("@")]

        # busca no db
        try:
            conexao      = get_connection()
            cursor       = conexao.cursor()
            cursor.execute("SELECT * FROM contatos WHERE contato = ?", (contato,))
            resultado    = cursor.fetchone()

            if resultado:
                return {"sucesso": False, "mensagem": "contato já existe"}
            
            cursor.execute("INSERT INTO contatos (contato) VALUES (?)", (contato,))
            conexao.commit()
            return {"sucesso": True, "mensagem": "contato salvo"}
        
        except sqlite3.Error as e:
            logger.exception(f"Erro ao salvar contato: {e}")
            return {"sucesso": False, "mensagem": f"Erro ao salvar contato."}

        finally:
            if conexao:
                conexao.close()
            else:
                logger.warning("Conexão não estava aberta ao tentar fechar.")
        
        # retornar True se salvo com sucesso, False caso contrário


    def buscar_contato(self, contato_id):
        # Lógica para buscar um contato pelo ID
        # Retornar os dados do contato ou None se não encontrado
        pass