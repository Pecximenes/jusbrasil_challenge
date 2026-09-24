"""Ponto de entrada da aplicação."""

from pathlib import Path

from bracis_reader.application import CitationExtractionApplication


def main() -> None:
    """Executa o pipeline com os caminhos padrão do projeto."""
    CitationExtractionApplication().run(
        txt_directory=Path("data/txt"),
        goldenset_path=Path("script/goldenset.csv"),
    )


if __name__ == "__main__":
    main()
