"""Separação dos documentos por nível."""

from collections.abc import Iterable

from bracis_reader.domain.models import TextDocument


class DocumentLevelSplitter:
    """Divide uma coleção de documentos entre os níveis N1 e N2."""

    def split(
        self,
        documents: Iterable[TextDocument],
    ) -> tuple[list[TextDocument], list[TextDocument]]:
        """Retorna duas listas: documentos N1 e documentos N2."""
        documents_n1: list[TextDocument] = []
        documents_n2: list[TextDocument] = []

        for document in documents:
            if "_n1_" in document.documento_id.lower():
                documents_n1.append(document)
            elif "_n2_" in document.documento_id.lower():
                documents_n2.append(document)

        return documents_n1, documents_n2
