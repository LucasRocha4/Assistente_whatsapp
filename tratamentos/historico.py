"""Persistência do histórico de mensagens por conversa."""
import logging
import sqlite3

from db_config.db_path import get_connection

logger = logging.getLogger(__name__)

CRIAR_TABELA = """
CREATE TABLE IF NOT EXISTS historico_conversas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversa_id TEXT NOT NULL,
    mensagem_id TEXT NOT NULL UNIQUE,
    remetente_id TEXT NOT NULL,
    direcao TEXT NOT NULL CHECK (direcao IN ('recebida', 'enviada')),
    mensagem TEXT NOT NULL,
    data_hora TEXT NOT NULL,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

CRIAR_INDICE_CONVERSA = """
CREATE INDEX IF NOT EXISTS idx_historico_conversas_conversa_data
ON historico_conversas (conversa_id, data_hora, id)
"""


class HistoricoConversas:
    def inicializar(self) -> None:
        conexao = None
        try:
            conexao = get_connection()
            conexao.execute(CRIAR_TABELA)
            conexao.execute(CRIAR_INDICE_CONVERSA)
            conexao.commit()
        except sqlite3.Error:
            logger.exception("Erro ao inicializar histórico de conversas")
            raise
        finally:
            if conexao:
                conexao.close()

    def salvar(
        self,
        *,
        conversa_id: str,
        mensagem_id: str,
        remetente_id: str,
        direcao: str,
        mensagem: str,
        data_hora: str,
    ) -> bool:
        if not all((conversa_id, mensagem_id, remetente_id, mensagem, data_hora)):
            logger.warning("Mensagem sem dados obrigatórios não foi salva no histórico")
            return False
        if direcao not in {"recebida", "enviada"}:
            logger.warning("Direção inválida para mensagem: %s", direcao)
            return False

        conexao = None
        try:
            conexao = get_connection()
            conexao.execute(CRIAR_TABELA)
            conexao.execute(CRIAR_INDICE_CONVERSA)
            cursor = conexao.execute(
                """
                INSERT OR IGNORE INTO historico_conversas
                    (conversa_id, mensagem_id, remetente_id, direcao, mensagem, data_hora)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (conversa_id, mensagem_id, remetente_id, direcao, mensagem, data_hora),
            )
            conexao.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            logger.exception("Erro ao salvar mensagem no histórico")
            return False
        finally:
            if conexao:
                conexao.close()

    def listar(self, conversa_id: str, limite: int = 20) -> list[dict]:
        if not conversa_id:
            return []
        limite = max(1, min(limite, 100))
        conexao = None
        try:
            conexao = get_connection()
            conexao.execute(CRIAR_TABELA)
            conexao.execute(CRIAR_INDICE_CONVERSA)
            conexao.row_factory = sqlite3.Row
            rows = conexao.execute(
                """
                SELECT conversa_id, mensagem_id, remetente_id, direcao, mensagem, data_hora
                FROM historico_conversas
                WHERE conversa_id = ?
                ORDER BY data_hora DESC, id DESC
                LIMIT ?
                """,
                (conversa_id, limite),
            ).fetchall()
            return [dict(row) for row in reversed(rows)]
        except sqlite3.Error:
            logger.exception("Erro ao consultar histórico da conversa %s", conversa_id)
            return []
        finally:
            if conexao:
                conexao.close()
