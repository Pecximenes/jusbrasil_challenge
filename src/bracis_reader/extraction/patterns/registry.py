"""Montagem do conjunto completo de padrões usados pelo detector."""

from bracis_reader.extraction.patterns.base import CitationPattern
from bracis_reader.extraction.patterns.generic import build_generic_patterns
from bracis_reader.extraction.patterns.ocr import build_ocr_patterns
from bracis_reader.extraction.patterns.structured import build_structured_patterns


class CitationPatternRegistry:
    """Constrói o conjunto de padrões utilizados pelo detector.

    A ordem importa: em empates de início e tamanho, o resolvedor de
    sobreposição mantém o primeiro padrão encontrado.
    """

    @classmethod
    def build(cls) -> tuple[CitationPattern, ...]:
        """Cria todos os padrões usados na extração."""
        return (
            build_structured_patterns()
            + build_ocr_patterns()
            + build_generic_patterns()
        )
