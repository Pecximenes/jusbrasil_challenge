"""Montagem do conjunto completo de padrões usados pelo detector."""

from bracis_reader.extraction.patterns.base import CitationPattern
from bracis_reader.extraction.patterns.incomplete import build_incomplete_patterns
from bracis_reader.extraction.patterns.jurisprudence import (
    build_jurisprudence_patterns,
)
from bracis_reader.extraction.patterns.legislation import build_legislation_patterns


class CitationPatternRegistry:
    """Constrói o conjunto de padrões utilizados pelo detector.

    A ordem importa: em empates de início e tamanho, o resolvedor de
    sobreposição mantém o primeiro padrão encontrado. Os identificados vêm
    antes dos genéricos.
    """

    @classmethod
    def build(cls) -> tuple[CitationPattern, ...]:
        """Cria todos os padrões usados na extração."""
        return (
            build_jurisprudence_patterns()
            + build_legislation_patterns()
            + build_incomplete_patterns()
        )
