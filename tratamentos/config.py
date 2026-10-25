"""Configuração central: carrega o .env uma única vez e expõe as variáveis.

Os outros módulos fazem `from . import config` e leem daqui.
Nada neste arquivo importa outro módulo do projeto.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = BASE_DIR / "evolution-go" / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# --- Evolution Go ---
EVOLUTION_URL = os.getenv("EVOLUTION_BASE_URL", "http://localhost:4000").rstrip("/")
EVOLUTION_INSTANCE_TOKEN = os.getenv("EVOLUTION_INSTANCE_TOKEN")  # enviar mensagens
GLOBAL_API_KEY = os.getenv("GLOBAL_API_KEY")  # atender ligações

# --- Gemini ---
GEMINI_KEY = os.getenv("GEMINI_KEY")
GEMINI_MODEL = os.getenv("MODELO", "gemini-3.1-flash-lite")
MODELOS_FALLBACK = [
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    "gemini-1.5-pro",
    "gemini-1.0-pro",
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
]
MAX_ENTRADA = int(os.getenv("MAX_ENTRADA", 1000))  # caracteres da mensagem do usuário
MAX_SAIDA = int(os.getenv("MAX_SAIDA", 500))  # tokens da resposta
SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    "Você é um assistente no WhatsApp. Responda de forma curta e direta.",
)

# --- Allowlist ---
# Números (só dígitos) separados por vírgula. Vazio = aceita todo mundo.
# Exemplo no .env: PERMITIDOS=5511999999999,5511888888888
PERMITIDOS = {
    "".join(ch for ch in item if ch.isdigit())
    for item in os.getenv("PERMITIDOS", "").split(",")
    if item.strip()
}

# --- Deduplicação ---
DEDUP_TTL_SEGUNDOS = int(os.getenv("DEDUP_TTL_SEGUNDOS", 600))


def validar() -> None:
    """Falha cedo, com mensagem clara, se faltar alguma chave obrigatória.

    Chamada na inicialização do servidor (main.py), e não no import,
    para os módulos continuarem importáveis em testes.
    """
    obrigatorias = {
        "EVOLUTION_INSTANCE_TOKEN": EVOLUTION_INSTANCE_TOKEN,
        "GLOBAL_API_KEY": GLOBAL_API_KEY,
        "GEMINI_KEY": GEMINI_KEY,
    }
    faltando = [nome for nome, valor in obrigatorias.items() if not valor]
    if faltando:
        raise RuntimeError(
            f"Variáveis ausentes: {', '.join(faltando)}. Confira o .env em {ENV_PATH}"
        )
