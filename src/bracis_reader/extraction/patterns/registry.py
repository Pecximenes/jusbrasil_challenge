"""Montagem do conjunto completo de padrões usados pelo detector."""

from bracis_reader.extraction.patterns.base import CitationPattern
from bracis_reader.extraction.patterns.incomplete import build_incomplete_patterns
from bracis_reader.extraction.patterns.jurisprudence import (
    build_jurisprudence_patterns,
)
from bracis_reader.extraction.patterns.legislation import build_legislation_patterns

# Alusões sem identificador nenhum ("jurisprudência pacífica desta Corte",
# "normas de regência"). O gabarito oficial do Kaggle (goldenset_offsets.csv)
# NÃO as anota: só as incompletas descritivas (tribunal, ano, relator) contam.
# Prevê-las vira falso positivo, então ficam desligadas por padrão.
GENERIC_PATTERN_NAMES = frozenset({"jurisprudencia_generica", "legislacao_generica"})


class CitationPatternRegistry:
    """Constrói o conjunto de padrões utilizados pelo detector.

    A ordem importa: em empates de início e tamanho, o resolvedor de
    sobreposição mantém o primeiro padrão encontrado. Os identificados vêm
    antes dos genéricos.
    """

    @classmethod
    def build(cls, include_generic: bool = False) -> tuple[CitationPattern, ...]:
        """Cria os padrões usados na extração.

        ``include_generic=True`` inclui também as alusões genéricas.
        """
        patterns = (
            build_jurisprudence_patterns()
            + build_legislation_patterns()
            + build_incomplete_patterns()
        )
        if include_generic:
            return patterns
        return tuple(p for p in patterns if p.name not in GENERIC_PATTERN_NAMES)
