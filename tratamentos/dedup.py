"""Deduplicação com expiração: lembra "vi isso há pouco", não "vi alguma vez"."""
import time


class Dedup:
    def __init__(self, ttl_segundos: float = 600):
        self.ttl = ttl_segundos
        # dict mantém a ordem de inserção, então as mais antigas ficam na frente
        self._vistos: dict[str, float] = {}

    def ja_visto(self, chave: str) -> bool:
        """Retorna True se a chave já foi vista dentro do prazo; senão registra e retorna False.

        Verificar e registrar acontecem sem nenhum `await` no meio, então duas
        entregas do mesmo webhook no asyncio não passam juntas.
        """
        agora = time.monotonic()

        for k in list(self._vistos):
            if agora - self._vistos[k] > self.ttl:
                del self._vistos[k]
            else:
                break

        if chave in self._vistos:
            return True

        self._vistos[chave] = agora
        return False

    def __len__(self) -> int:
        return len(self._vistos)
