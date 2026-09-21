from pathlib import Path

from bracis_reader import DocumentLevelSplitter, TextDirectoryLoader


def main() -> None:
    """Carrega o diretório e separa seus documentos entre N1 e N2."""
    directory = Path("data/txt")

    loader = TextDirectoryLoader(directory)
    documents = loader.load()

    splitter = DocumentLevelSplitter()
    documents_n1, documents_n2 = splitter.split(documents)

    print(f"Total de documentos: {len(documents)}")
    print(f"Documentos N1: {len(documents_n1)}")
    print(f"Documentos N2: {len(documents_n2)}")

    # print(documents_n1[0])


if __name__ == "__main__":
    main()
