"""Tipos e constantes compartilhados pelos catálogos de padrões."""

import re
from dataclasses import dataclass

FLAGS = re.IGNORECASE | re.VERBOSE
SPACE = r"[ \t\r\n]+"


@dataclass(frozen=True)
class CitationPattern:
    """Expressão regular usada para localizar uma família de citações."""

    name: str
    expression: re.Pattern[str]
