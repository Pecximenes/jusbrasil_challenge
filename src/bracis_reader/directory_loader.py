"""Carregamento dos arquivos TXT de um diretório."""

from pathlib import Path

from bracis_reader.models import TextDocument


class TextDirectoryLoader:
    """Carrega todos os arquivos TXT existentes em um diretório."""

    def __init__(self, directory: str | Path) -> None:
        self._directory = Path(directory)

    def load(self) -> list[TextDocument]:
        """Lê os arquivos TXT e devolve os documentos em ordem alfabética."""
        if not self._directory.is_dir():
            raise FileNotFoundError(f"Diretório não encontrado: {self._directory}")

        document_paths = sorted(self._directory.glob("*.txt"))

        return [self._load_document(path) for path in document_paths]

    @staticmethod
    def _load_document(path: Path) -> TextDocument:
        text = path.read_bytes().decode("utf-8")

        return TextDocument(
            documento_id=path.stem,
            texto=text,
        )
