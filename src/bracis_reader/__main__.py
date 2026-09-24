"""Executa o pipeline pela linha de comando: ``python -m bracis_reader``.

Opções:

    --exato       avalia por correspondência exata em vez de IoU >= 0,5
    --robustez    roda também o teste de robustez a ruído
    --txt DIR     pasta com os documentos (padrão: data/txt)
    --gold CSV    caminho do goldenset (padrão: data/goldenset.csv)
"""

import argparse
from pathlib import Path

from bracis_reader.evaluation.evaluator import CitationEvaluator
from bracis_reader.evaluation.goldenset import GoldensetLoader
from bracis_reader.evaluation.robustness import NoiseRobustnessEvaluator
from bracis_reader.ingestion.directory_loader import TextDirectoryLoader
from bracis_reader.pipeline import CitationExtractionApplication

DEFAULT_TXT_DIRECTORY = Path("data/txt")
DEFAULT_GOLDENSET_PATH = Path("data/goldenset.csv")


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="bracis_reader",
        description="Extrai citações jurídicas e avalia contra o goldenset.",
    )
    parser.add_argument("--txt", type=Path, default=DEFAULT_TXT_DIRECTORY)
    parser.add_argument("--gold", type=Path, default=DEFAULT_GOLDENSET_PATH)
    parser.add_argument(
        "--exato",
        action="store_true",
        help="exige início, fim e trecho idênticos (padrão: IoU >= 0,5)",
    )
    parser.add_argument(
        "--robustez",
        action="store_true",
        help="mede o recall em variantes ruidosas das citações do gabarito",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Executa o pipeline com os caminhos informados."""
    args = _parse_args(argv)
    evaluator = CitationEvaluator(iou_threshold=None if args.exato else 0.5)
    CitationExtractionApplication(evaluator=evaluator).run(
        txt_directory=args.txt,
        goldenset_path=args.gold,
    )

    if args.robustez:
        documents = TextDirectoryLoader(args.txt).load()
        expected = GoldensetLoader().load(args.gold)
        result = NoiseRobustnessEvaluator().evaluate(documents, expected)
        print(
            f"\nRobustez a ruído: {result.detected}/{result.variants} "
            f"variantes encontradas ({result.recall:.4f})"
        )


if __name__ == "__main__":
    main()
