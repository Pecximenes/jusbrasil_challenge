"""Tipo compartilhado pelos catálogos de padrões."""

import re
from dataclasses import dataclass
from typing import Literal

CitationType = Literal["lei", "jurisprudencia"]


@dataclass(frozen=True)
class CitationPattern:
    """Expressão regular usada para localizar uma família de citações."""

    name: str
    expression: re.Pattern[str]
    tipo: CitationType
