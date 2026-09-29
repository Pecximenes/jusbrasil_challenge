"""Localização do corpo útil de um documento jurídico."""

import re


class DocumentBodyExtractor:
    """Localiza onde o corpo começa, sem modificar o texto original."""

    _HEADER_END = re.compile(r"\r?\n[ \t]*\r?\n[ \t]*\r?\n")
    _BLANK_LINE = re.compile(r"\r?\n[ \t]*\r?\n")

    def __init__(self, header_limit: int = 1500) -> None:
        self._header_limit = header_limit

    def find_body_start(self, text: str) -> int:
        """Retorna o índice inicial do corpo."""
        header_end = self._HEADER_END.search(text)
        if header_end is not None:
            return header_end.end()

        blank_line = self._BLANK_LINE.search(text, 0, self._header_limit)
        if blank_line is not None:
            return blank_line.end()

        return 0
