"""Citações de súmulas."""

import re

from bracis_reader.classification.canonical_catalog import SumulaKey
from bracis_reader.classification.legal_text import NUMBER, court_mentioned, plain
from bracis_reader.classification.normalization import to_digits
from bracis_reader.classification.resolvers.base import Resolution

_SUMULA_NUMBER = re.compile(
    rf"(?:mula|rnula|m\.|rn\.|enunciado|verbete|\bSV\b)\D{{0,20}}?\b({NUMBER})",
    re.I,
)


class SumulaResolver:
    """Confirma a súmula pelo número, tribunal e caráter vinculante."""

    def __init__(self, sumulas: dict[SumulaKey, int]) -> None:
        self._sumulas = sumulas

    def resolve(self, trecho: str) -> Resolution:
        match = _SUMULA_NUMBER.search(trecho)
        if not match:
            return Resolution.incompleta("sumula_sem_numero", "sem número")
        numero = int(to_digits(match.group(1)) or 0)
        vinculante = bool(re.search(r"vinculante|\bsv\b", plain(trecho)))
        court = court_mentioned(trecho) or ("STF" if vinculante else None)

        found = [
            record_id
            for (tribunal, number, binding), record_id in self._sumulas.items()
            if number == numero
            and binding == vinculante
            and (court is None or tribunal == court)
        ]
        if len(found) == 1:
            return Resolution.real(found[0], "sumula_real", "súmula do catálogo")
        if not found:
            return Resolution.inventada("sumula_inventada", "fora da base")
        return Resolution.incompleta("sumula_ambigua", "sem tribunal definido")
