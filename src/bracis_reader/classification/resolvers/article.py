"""Citações de dispositivos legais."""

import re

from bracis_reader.classification.canonical_catalog import ArticleKey, law_of
from bracis_reader.classification.legal_text import NUMBER, plain
from bracis_reader.classification.normalization import to_digits
from bracis_reader.classification.resolvers.base import Resolution

_ARTICLE_NUMBER = re.compile(rf"art(?:igo)?s?\.?\s*({NUMBER})", re.I)


class ArticleResolver:
    """Confirma o artigo pelo número e pelo diploma legal citado."""

    def __init__(self, dispositivos: dict[ArticleKey, int]) -> None:
        self._dispositivos = dispositivos

    def resolve(self, trecho: str) -> Resolution:
        match = _ARTICLE_NUMBER.search(trecho)
        if not match:
            return Resolution.incompleta("artigo_sem_numero", "sem número")
        artigo = int(to_digits(match.group(1)) or 0)
        law_text = plain(trecho[match.end() :])
        lei = law_of(law_text, law_text.replace("rn", "m"))
        if lei is None:
            return Resolution.inventada("artigo_lei_fora", "diploma fora da base")
        record_id = self._dispositivos.get((lei, artigo))
        if record_id is None:
            return Resolution.inventada(
                "artigo_inexistente", f"art. {artigo} do {lei} fora"
            )
        return Resolution.real(record_id, "artigo_real", f"art. {artigo} do {lei}")
