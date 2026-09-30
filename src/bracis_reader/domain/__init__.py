"""Modelos de domínio compartilhados por todas as camadas."""

from bracis_reader.domain.models import (
    CitationCandidate,
    ClassifiedCitation,
    TextDocument,
)
from bracis_reader.domain.ports import (
    CitationClassifierPort,
    CitationExtractor,
    DocumentSource,
    ResultWriter,
)

__all__ = [
    "CitationCandidate",
    "CitationClassifierPort",
    "CitationExtractor",
    "ClassifiedCitation",
    "DocumentSource",
    "ResultWriter",
    "TextDocument",
]
