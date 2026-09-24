"""Permite executar o pipeline com ``python -m bracis_reader``."""

from pathlib import Path

from bracis_reader.pipeline import CitationExtractionApplication

DEFAULT_TXT_DIRECTORY = Path("data/txt")
DEFAULT_GOLDENSET_PATH = Path("data/goldenset.csv")


def main() -> None:
    """Executa o pipeline com os caminhos padrão do projeto."""
    CitationExtractionApplication().run(
        txt_directory=DEFAULT_TXT_DIRECTORY,
        goldenset_path=DEFAULT_GOLDENSET_PATH,
    )


if __name__ == "__main__":
    main()
