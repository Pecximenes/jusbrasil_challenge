"""Citações descritas por tribunal, ano e relator, sem número."""

import re

from bracis_reader.classification.canonical_base import CanonicalBase
from bracis_reader.classification.legal_text import court_mentioned
from bracis_reader.classification.normalization import to_digits
from bracis_reader.classification.resolvers.base import Resolution

_YEAR = re.compile(r"\b(?:19|2[0O])[0-9OoIlSs]{2}\b")
_TITLE = (
    r"(?:exm[oa]\.?\s+(?:(?:sr|sra)\.?\s+)?)?"
    r"(?:ministr[oa]|min\.|des\.|desembargador[a]?)"
)
_RAPPORTEUR = re.compile(
    r"(?:relatoria\s+d\w{0,2}|relatad[oa]\s+pel[oa]|\brel(?:ator|atora)?\.?"
    rf"|\b(?:d[oa]|pel[oa])(?=\s+{_TITLE}))"
    rf"(?:\s+{_TITLE}){{0,2}}"
    r"\s+(?P<nome>(?-i:[A-ZÀ-Ý][\wÀ-ÿ'’]+(?:\s+(?:(?:d[aeo]s?|D[AEOaeo]S?|e)\s+)?"
    r"[A-ZÀ-Ý][\wÀ-ÿ'’]+)*))",
    re.IGNORECASE,
)


class DescriptionResolver:
    """Só confirma quando a descrição aponta um único feito da base."""

    def __init__(self, base: CanonicalBase) -> None:
        self._base = base

    def resolve(self, trecho: str) -> Resolution:
        year_match = _YEAR.search(trecho)
        ano = int(to_digits(year_match.group(0))) if year_match else None
        rapporteur = _RAPPORTEUR.search(trecho)
        relator = rapporteur.group("nome") if rapporteur else None

        feitos = self._base.count_described(court_mentioned(trecho), ano, relator)
        if len(feitos) == 1:
            return Resolution.real(
                min(feitos[0].ids), "descricao_unica", "descrição única na base"
            )
        if not feitos:
            return Resolution.incompleta(
                "descricao_sem_correspondencia", "sem correspondência"
            )
        return Resolution.incompleta(
            "descricao_varios", f"{len(feitos)} feitos possíveis"
        )
