"""Montagem do conjunto completo de padrões usados pelo detector."""

from bracis_reader.extraction.patterns.base import CitationPattern
from bracis_reader.extraction.patterns.incomplete import build_incomplete_patterns
from bracis_reader.extraction.patterns.jurisprudence import (
    build_jurisprudence_patterns,
)
from bracis_reader.extraction.patterns.legislation import build_legislation_patterns

GENERIC_PATTERN_NAMES = frozenset({"jurisprudencia_generica", "legislacao_generica"})


class CitationPatternRegistry:
    """Constrói o conjunto de padrões utilizados pelo detector."""

    @classmethod
    def build(cls, include_generic: bool = False) -> tuple[CitationPattern, ...]:
        """Cria os padrões usados na extração."""
        patterns = (
            build_jurisprudence_patterns()
            + build_legislation_patterns()
            + build_incomplete_patterns()
        )
        if include_generic:
            return patterns
        return tuple(p for p in patterns if p.name not in GENERIC_PATTERN_NAMES)
