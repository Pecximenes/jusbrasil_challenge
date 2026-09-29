"""Funções de leitura de texto jurídico usadas por mais de um resolvedor."""

import re

from bracis_reader.classification.normalization import strip_accents

COURTS = ("STF", "STJ", "TST", "TSE", "STM")
_COURT_NAMES = {
    "supremo tribunal federal": "STF",
    "superior tribunal de justica": "STJ",
    "tribunal superior do trabalho": "TST",
    "tribunal superior eleitoral": "TSE",
    "superior tribunal militar": "STM",
}

NUMBER = r"(?:[0-9]|[OoIlLSs](?=[.\s]?[0-9º°]))[0-9OoIlLSs.]*"


def plain(text: str) -> str:
    """Minúsculas, sem acentos e com espaços simples."""
    return re.sub(r"\s+", " ", strip_accents(text).lower())


def court_mentioned(text: str) -> str | None:
    """Sigla do tribunal superior citado pela sigla ou pelo nome."""
    for court in COURTS:
        if re.search(rf"\b{court}\b", text):
            return court
    normalized = plain(text)
    for name, court in _COURT_NAMES.items():
        if name in normalized:
            return court
    return None
