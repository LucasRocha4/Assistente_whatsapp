import logging
import re

logger = logging.getLogger(__name__)

PERMITIDOS: set[str] = set()

class TratarMensagem:

    # dentro da classe
    @staticmethod
    async def tratar(payload: dict):
        data = payload.get("data", {})
        info = data.get("Info", {})

        chat = info.get("Chat", "")
        texto = TratarMensagem.extrair_texto(data.get("Message", {}))

        # 1) o que eu mesmo enviei (evita loop)
        if info.get("IsFromMe"):
            logger.info("Ignorada: enviada por mim")
            return

        # 2) grupos
        if info.get("IsGroup"):
            logger.info("Ignorada: grupo %s", chat)
            return

        # 3) status e canais
        if chat.startswith("status@broadcast") or chat.endswith("@newsletter"):
            logger.info("Ignorada: status/canal")
            return

        # 4) conversas não permitidas
        if PERMITIDOS and chat not in PERMITIDOS:
            logger.info("Ignorada: %s fora da allowlist", chat)
            return

        # 5) sem texto útil
        if not await TratarMensagem.filtrar_mensagem(texto):
            logger.info("Ignorada: sem texto útil")
            return

        logger.info("Processando mensagem de %s: %s", chat, texto)
        # aqui entra a resposta, no próximo passo

    @staticmethod
    def extrair_texto(message: dict) -> str | None:
        """Pega o texto da mensagem, seja simples ou resposta/link."""
        if not message:
            return None
        return (
            message.get("conversation")
            or message.get("extendedTextMessage", {}).get("text")
        )

    @staticmethod
    def separar_numero(phone: str) -> str:
        """Remove caracteres não numéricos de um número de telefone."""
        if "@" in phone:
            phone = phone.split("@")[0]
        return re.sub(r"\D", "", phone)

    @staticmethod
    async def filtrar_mensagem(message: str) -> bool:
        """Retorna True se a mensagem passar no filtro."""
        if not message or len(message) < 2:
            return False

        logger.info("Mensagem passou no filtro: %s", message)
        return True
