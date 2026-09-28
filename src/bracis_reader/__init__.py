"""Leitura e extração de citações dos documentos."""

from bracis_reader.domain import CitationCandidate, TextDocument
from bracis_reader.extraction import CitationDetector, DocumentBodyExtractor
from bracis_reader.ingestion import DocumentLevelSplitter, TextDirectoryLoader
from bracis_reader.pipeline import CitationExtractionApplication

__all__ = [
    "CitationCandidate",
    "CitationDetector",
    "CitationExtractionApplication",
    "DocumentBodyExtractor",
    "DocumentLevelSplitter",
    "TextDirectoryLoader",
    "TextDocument",
]
