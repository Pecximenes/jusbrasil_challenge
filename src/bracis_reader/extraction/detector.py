"""Serviço de extração de citações em documentos jurídicos."""

from collections.abc import Iterable

from bracis_reader.domain.models import CitationCandidate, TextDocument
from bracis_reader.extraction.body_extractor import DocumentBodyExtractor
from bracis_reader.extraction.overlap_resolver import CitationOverlapResolver
from bracis_reader.extraction.patterns import (
    CitationPattern,
    CitationPatternRegistry,
)


class CitationDetector:
    """Aplica padrões no corpo e preserva os índices do texto original."""

    def __init__(
        self,
        body_extractor: DocumentBodyExtractor | None = None,
        patterns: tuple[CitationPattern, ...] | None = None,
        overlap_resolver: CitationOverlapResolver | None = None,
    ) -> None:
        self._body_extractor = body_extractor or DocumentBodyExtractor()
        self._patterns = patterns or CitationPatternRegistry.build()
        self._overlap_resolver = overlap_resolver or CitationOverlapResolver()

    def detect(self, document: TextDocument) -> list[CitationCandidate]:
        """Extrai citações do corpo de um documento."""
        body_start = self._body_extractor.find_body_start(document.texto)
        body = document.texto[body_start:]
        candidates = self._find_candidates(
            original_text=document.texto,
            searchable_text=body,
            offset=body_start,
        )
        return self._overlap_resolver.resolve(candidates)

    def detect_many(
        self,
        documents: Iterable[TextDocument],
    ) -> dict[str, list[CitationCandidate]]:
        """Extrai citações de vários documentos, agrupadas por ID."""
        return {document.documento_id: self.detect(document) for document in documents}

    def _find_candidates(
        self,
        original_text: str,
        searchable_text: str,
        offset: int,
    ) -> list[CitationCandidate]:
        candidates: list[CitationCandidate] = []

        for pattern in self._patterns:
            for match in pattern.expression.finditer(searchable_text):
                start = offset + match.start()
                end = offset + match.end()
                candidates.append(
                    CitationCandidate(
                        inicio=start,
                        fim=end,
                        trecho=original_text[start:end],
                    )
                )

        return candidates
