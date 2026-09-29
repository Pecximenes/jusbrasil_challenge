"""Índices de súmulas e artigos de lei presentes na base canônica."""

import re
from collections.abc import Iterator

from bracis_reader.classification.canonical_base import CanonicalBase, Record
from bracis_reader.classification.catalog import DISPOSITIVOS, LAW_PATTERNS, SUMULAS
from bracis_reader.classification.legal_text import plain

SumulaKey = tuple[str, int, bool]
ArticleKey = tuple[str, int]

_SUMULA_TITLE = re.compile(
    r"s[uú]mula\s+(?P<vinculante>vinculante\s+)?n[º°o]?\.?\s*(?P<numero>\d+)"
    r"\s+d[oa]\s+(?P<tribunal>STF|STJ|TST|TSE|STM)\b",
    re.IGNORECASE,
)
_ARTICLE_TITLE = re.compile(
    r"artigo\s+(?P<artigo>\d+)\s*[º°o]?\s+d[aoe]s?\s+(?P<lei>.+)$", re.IGNORECASE
)


def law_of(*texts: str) -> str | None:
    """Primeiro diploma legal reconhecido em algum dos textos normalizados."""
    return next(
        (
            law
            for law, pattern in LAW_PATTERNS
            if any(re.search(pattern, text) for text in texts)
        ),
        None,
    )


class CanonicalCatalog:
    """Localiza súmulas e artigos pelo título do registro.

    Quando a base não traz títulos, recorre ao início do texto de cada
    enunciado conhecido em ``catalog.py``.
    """

    def __init__(self, base: CanonicalBase) -> None:
        self._base = base
        self.sumulas: dict[SumulaKey, int] = self._index_sumulas()
        self.dispositivos: dict[ArticleKey, int] = self._index_dispositivos()

    def _titles(self, natureza: str) -> Iterator[tuple[Record, str]]:
        for record in self._base.records:
            if record.natureza == natureza:
                yield record, record.texto.split("\n", 1)[0]

    def _record_containing(self, natureza: str, fragment: str) -> int | None:
        wanted = plain(fragment)
        for record in self._base.records:
            if record.natureza == natureza and wanted in plain(record.texto):
                return record.id
        return None

    def _index_sumulas(self) -> dict[SumulaKey, int]:
        index: dict[SumulaKey, int] = {}
        for record, title in self._titles("sumula"):
            match = _SUMULA_TITLE.match(title)
            if match:
                key = (
                    match.group("tribunal").upper(),
                    int(match.group("numero")),
                    bool(match.group("vinculante")),
                )
                index[key] = record.id
        for entry in SUMULAS:
            key = (entry.tribunal, entry.numero, entry.vinculante)
            if key not in index:
                record_id = self._record_containing("sumula", entry.inicio_do_texto)
                if record_id is not None:
                    index[key] = record_id
        return index

    def _index_dispositivos(self) -> dict[ArticleKey, int]:
        index: dict[ArticleKey, int] = {}
        for record, title in self._titles("dispositivo"):
            match = _ARTICLE_TITLE.match(title)
            law = law_of(plain(match.group("lei"))) if match else None
            if law:
                index[(law, int(match.group("artigo")))] = record.id
        for entry in DISPOSITIVOS:
            key = (entry.lei, entry.artigo)
            if key not in index:
                record_id = self._record_containing(
                    "dispositivo", entry.inicio_do_texto
                )
                if record_id is not None:
                    index[key] = record_id
        return index
