"""Contratos entre as etapas do fluxo.

As camadas de orquestração dependem destes protocolos, não das classes
concretas, o que permite trocar qualquer etapa (outro leitor, outro
detector, outro classificador) sem alterar quem as usa.
"""

from collections.abc import Iterable
from pathlib import Path
from typing import Protocol

from bracis_reader.domain.models import (
    CitationCandidate,
    ClassifiedCitation,
    TextDocument,
)

CandidatesByDocument = dict[str, list[CitationCandidate]]
ResultsByDocument = dict[str, list[ClassifiedCitation]]


class DocumentSource(Protocol):
    """Origem dos documentos a analisar."""

    def load(self) -> list[TextDocument]: ...


class CitationExtractor(Protocol):
    """Encontra trechos que parecem citações."""

    def detect(self, document: TextDocument) -> list[CitationCandidate]: ...

    def detect_many(
        self, documents: Iterable[TextDocument]
    ) -> CandidatesByDocument: ...


class CitationClassifierPort(Protocol):
    """Decide se cada citação é real, inventada ou incompleta."""

    def classify_many(
        self, citations: list[CitationCandidate]
    ) -> list[ClassifiedCitation]: ...


class ResultWriter(Protocol):
    """Destino dos resultados classificados."""

    def write(self, results: ResultsByDocument) -> Path: ...
