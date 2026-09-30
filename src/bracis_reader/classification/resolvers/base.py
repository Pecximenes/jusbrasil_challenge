"""Contrato comum dos resolvedores de citação."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Resolution:
    """Decisão de um resolvedor e a regra que a justificou."""

    classificacao: str
    id_canonico: int | None
    regra: str
    motivo: str

    @classmethod
    def real(cls, id_canonico: int, regra: str, motivo: str) -> "Resolution":
        return cls("real", id_canonico, regra, motivo)

    @classmethod
    def inventada(cls, regra: str, motivo: str) -> "Resolution":
        return cls("inventada", None, regra, motivo)

    @classmethod
    def incompleta(cls, regra: str, motivo: str) -> "Resolution":
        return cls("incompleta", None, regra, motivo)


class CitationResolver(Protocol):
    """Decide a classe de um trecho de um tipo específico de citação."""

    def resolve(self, trecho: str) -> Resolution: ...
