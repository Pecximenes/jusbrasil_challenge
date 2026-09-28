"""Catálogo de expressões regulares para citações jurídicas."""

from bracis_reader.extraction.patterns.base import CitationPattern, CitationType
from bracis_reader.extraction.patterns.registry import CitationPatternRegistry

__all__ = ["CitationPattern", "CitationPatternRegistry", "CitationType"]
