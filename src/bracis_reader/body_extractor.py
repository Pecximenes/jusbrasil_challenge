"""Localização do corpo útil de um documento jurídico."""

import re


class DocumentBodyExtractor:
    """Localiza o corpo após duas linhas vazias consecutivas."""

    _HEADER_END = re.compile(
        r"\r?\n[ \t]*\r?\n[ \t]*\r?\n",
    )

    def find_body_start(self, text: str) -> int:
        """Retorna o índice inicial sem modificar o texto original."""
        header_end = self._HEADER_END.search(text)

        if header_end is None:
            return 0

        return header_end.end()
