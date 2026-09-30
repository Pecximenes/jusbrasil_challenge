"""Leitura e extração de citações dos documentos."""

from bracis_reader.application import CitationExtractionApplication
from bracis_reader.domain import CitationCandidate, TextDocument
from bracis_reader.extraction import CitationDetector, DocumentBodyExtractor
from bracis_reader.ingestion import DocumentLevelSplitter, TextDirectoryLoader
from bracis_reader.pipeline import CitationPipeline

__all__ = [
    "CitationCandidate",
    "CitationDetector",
    "CitationExtractionApplication",
    "CitationPipeline",
    "DocumentBodyExtractor",
    "DocumentLevelSplitter",
    "TextDirectoryLoader",
    "TextDocument",
]
