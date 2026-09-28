"""Extração de citações jurídicas a partir do texto dos documentos."""

from bracis_reader.extraction.body_extractor import DocumentBodyExtractor
from bracis_reader.extraction.detector import CitationDetector
from bracis_reader.extraction.overlap_resolver import CitationOverlapResolver

__all__ = ["CitationDetector", "CitationOverlapResolver", "DocumentBodyExtractor"]
