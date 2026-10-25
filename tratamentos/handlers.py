"""Regras do bot: o que fazer com cada evento recebido do Evolution.

Ordem de dependência: este módulo importa os outros (config, evolution,
contatos, llm...). Nenhum deles importa este.
"""
import asyncio
import logging
import re
from datetime import datetime, timezone

from . import config, evolution, llm
from .contatos import TratamentoContatos
from .dedup import Dedup
from .historico import HistoricoConversas
from .numeros import conversa_individual, normalizar_numero

logger = logging.getLogger(__name__)

# Só processa mensagens enviadas depois que o servidor ligou
DATA_INICIO = datetime.now(timezone.utc)

# Números permitidos (vazio = todos). Vem do .env.
PERMITIDOS: set[str] = set(config.PERMITIDOS)

mensagens_vistas = Dedup(config.DEDUP_TTL_SEGUNDOS)
chamadas_vistas = Dedup(config.DEDUP_TTL_SEGUNDOS)

contatos = TratamentoContatos()
historico = HistoricoConversas()


# ---------------------------------------------------------------- utilidades

def achar(obj, *chaves):
    """Procura a primeira chave encontrada em qualquer nível do JSON."""
    if isinstance(obj, dict):
        for chave in chaves:
            if chave in obj and obj[chave] is not None:
                return obj[chave]
        for v in obj.values():
            r = achar(v, *chaves)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = achar(v, *chaves)
            if r is not None:
                return r
    return None


def extrair_texto(message: dict | None) -> str | None:
    """Pega o texto da mensagem, seja simples ou resposta/link."""
    if not message:
        return None
    return (
        message.get("conversation")
        or (message.get("extendedTextMessage") or {}).get("text")
    )


def texto_util(texto: str | None) -> bool:
    return bool(texto) and len(texto.strip()) >= 2


def ler_timestamp(valor) -> datetime | None:
    """Converte o Timestamp do Evolution em datetime com fuso. None se não der.

    Aceita frações com mais de 6 dígitos (o Evolution manda 9) e 'Z' no fim,
    o que funciona mesmo em versões do Python anteriores à 3.11.
    """
    if not valor or not isinstance(valor, str):
        return None
    texto = valor.strip()
    if texto.endswith("Z"):
        texto = texto[:-1] + "+00:00"
    texto = re.sub(r"(\.\d{6})\d+", r"\1", texto)
    try:
        momento = datetime.fromisoformat(texto)
    except ValueError:
        return None
    if momento.tzinfo is None:
        momento = momento.replace(tzinfo=timezone.utc)
    return momento


# ------------------------------------------------------------------ mensagens

async def tratar_mensagem(payload: dict) -> None:
    data = payload.get("data") or {}
    info = data.get("Info") or {}
    chat = info.get("Chat") or ""
    msg_id = info.get("ID")
    sender = info.get("Sender") or info.get("SenderAlt") or chat
    conversa_id = str(chat)
    remetente_id = str(sender)
    logger.info(
        "Mensagem recebida | id=%s chat=%s sender=%s senderAlt=%s fromMe=%r",
        msg_id,
        chat,
        info.get("Sender"),
        info.get("SenderAlt"),
        info.get("IsFromMe"),
    )

    # 1) descartes baratos
    if info.get("IsFromMe"):
        logger.info("Ignorada: enviada por mim")
        return
    if info.get("IsGroup") or chat.endswith("@g.us"):
        logger.info("Ignorada: grupo %s", chat)
        return
    if chat.startswith("status@broadcast") or chat.endswith("@newsletter"):
        logger.info("Ignorada: status/canal %s", chat)
        return

    # 2) só conversa individual (@s.whatsapp.net)
    if not conversa_individual(chat):
        logger.info("Ignorada: chat fora do formato esperado: %s", chat)
        return

    # 3) só mensagens posteriores ao início do servidor
    momento = ler_timestamp(info.get("Timestamp"))
    if momento is None:
        logger.warning("Ignorada: Timestamp ausente ou ilegível (%r)", info.get("Timestamp"))
        return
    if momento < DATA_INICIO:
        logger.info("Ignorada: mensagem anterior ao início do servidor (%s)", momento)
        return

    # 4) deduplicação (webhooks podem repetir)
    if not msg_id:
        logger.warning("Ignorada: mensagem sem ID")
        return
    if mensagens_vistas.ja_visto(f"msg:{msg_id}"):
        logger.info("Ignorada: mensagem %s já tratada", msg_id)
        return

    # 5) allowlist
    numero = normalizar_numero(chat)
    if PERMITIDOS and numero not in PERMITIDOS:
        logger.info("Ignorada: %s fora da allowlist", numero)
        return

    # 6) texto útil
    texto = extrair_texto(data.get("Message"))
    if not texto_util(texto):
        logger.info("Ignorada: sem texto útil")
        return

    historico_anterior = await asyncio.to_thread(historico.listar, conversa_id)
    await asyncio.to_thread(
        historico.salvar,
        conversa_id=conversa_id,
        mensagem_id=str(msg_id),
        remetente_id=remetente_id,
        direcao="recebida",
        mensagem=texto,
        data_hora=momento.isoformat(),
    )

    # 7) spam (consulta ao banco numa thread, para não travar o servidor)
    if await asyncio.to_thread(contatos.verificar_spam, numero):
        logger.info("Ignorada: %s marcado como spam", numero)
        return

    # 8) registra o contato (criado=True só no primeiro contato)
    salvo = await asyncio.to_thread(contatos.salvar_contato, numero)
    if salvo.get("criado"):
        logger.info("Primeiro contato de %s", numero)

    # 9) LLM e envio
    logger.info("Processando mensagem de %s: %s", numero, texto)
    resposta = await llm.responder(texto, historico_anterior)
    if not resposta:
        logger.warning("Sem resposta da LLM para %s; nada enviado", numero)
        return

    enviada = await evolution.enviar_mensagem(chat, resposta)
    if enviada:
        await asyncio.to_thread(
            historico.salvar,
            conversa_id=conversa_id,
            mensagem_id=f"rock:{msg_id}",
            remetente_id="rock",
            direcao="enviada",
            mensagem=resposta,
            data_hora=datetime.now(timezone.utc).isoformat(),
        )


# ------------------------------------------------------------------- chamadas

async def tratar_chamada(payload: dict) -> None:
    call_id = achar(payload, "callId", "call_id", "CallID")
    call_creator = achar(payload, "callCreator", "call_creator", "CallCreator")

    if not call_id or not call_creator:
        logger.warning("CallOffer sem callId/callCreator, confira o payload")
        return

    if chamadas_vistas.ja_visto(f"call:{call_id}"):
        logger.info("Chamada %s já tratada, ignorando repetição", call_id)
        return

    ok = await evolution.atende_ligacao(call_id, call_creator)
    logger.info("Atendimento da chamada %s: %s", call_id, "OK" if ok else "FALHOU")
