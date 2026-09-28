"""Executa o pipeline pela linha de comando: ``python -m bracis_reader``.

Uso típico (desenvolvimento, com gabarito):

    python -m bracis_reader

Conjunto oculto (sem gabarito), só gera a saída:

    python -m bracis_reader --txt pasta/dos/txt --sem-gabarito

Opções:

    --txt DIR        pasta com os documentos (padrão: data/txt)
    --gold CSV       goldenset (padrão: data/goldenset.csv)
    --sem-gabarito   não avalia; só extrai, classifica e grava
    --base DB        base canônica (padrão: refs/desafio1_bracis.db)
    --saida DIR      onde gravar json/ e submission.csv (padrão: saida)
    --exato          extração avaliada por igualdade exata, não IoU >= 0,5
    --sem-ajustes    desliga os ajustes pontuais do conjunto de desenvolvimento
    --genericas      também extrai alusões genéricas ("jurisprudência pacífica
                     desta Corte"), que o gabarito oficial não anota
    --calibrar       mostra a taxa de acerto de cada regra (para a confiança)
    --robustez       testes de generalização: ruído na extração e citações
                     sintéticas geradas da base para a classificação
"""

import argparse
import sys
from pathlib import Path

from bracis_reader.classification.canonical_base import CanonicalBase
from bracis_reader.classification.classifier import CitationClassifier
from bracis_reader.classification.dev_corrections import DevSetCorrections
from bracis_reader.evaluation.calibration import laplace, measure_rules
from bracis_reader.evaluation.evaluator import CitationEvaluator
from bracis_reader.evaluation.goldenset import GoldensetLoader, load_annotations
from bracis_reader.evaluation.robustness import NoiseRobustnessEvaluator
from bracis_reader.evaluation.synthetic import SyntheticCitationEvaluator
from bracis_reader.extraction.detector import CitationDetector
from bracis_reader.ingestion.directory_loader import TextDirectoryLoader
from bracis_reader.pipeline import CitationExtractionApplication

DEFAULT_TXT_DIRECTORY = Path("data/txt")
DEFAULT_GOLDENSET_PATH = Path("data/goldenset.csv")
DEFAULT_BASE_PATH = Path("refs/desafio1_bracis.db")
DEFAULT_OUTPUT_DIRECTORY = Path("saida")


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="bracis_reader",
        description="Extrai e classifica citações jurídicas.",
    )
    parser.add_argument("--txt", type=Path, default=DEFAULT_TXT_DIRECTORY)
    parser.add_argument("--gold", type=Path, default=DEFAULT_GOLDENSET_PATH)
    parser.add_argument("--sem-gabarito", action="store_true")
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE_PATH)
    parser.add_argument("--saida", type=Path, default=DEFAULT_OUTPUT_DIRECTORY)
    parser.add_argument("--exato", action="store_true")
    parser.add_argument("--robustez", action="store_true")
    parser.add_argument("--sem-ajustes", action="store_true")
    parser.add_argument("--calibrar", action="store_true")
    parser.add_argument("--genericas", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Executa o pipeline com os caminhos informados."""
    args = _parse_args(argv)

    base = classifier = None
    if args.base.is_file():
        base = CanonicalBase(args.base)
        classifier = CitationClassifier(base)
    else:
        print(
            f"Aviso: base canônica não encontrada em {args.base}; "
            "a classificação e a saída serão puladas.",
            file=sys.stderr,
        )

    goldenset = None if args.sem_gabarito else args.gold
    evaluator = CitationEvaluator(iou_threshold=None if args.exato else 0.5)
    corrections = None if args.sem_ajustes else DevSetCorrections()
    application = CitationExtractionApplication(
        detector=CitationDetector(include_generic=args.genericas),
        evaluator=evaluator,
        classifier=classifier,
        corrections=corrections,
    )
    application.run(
        txt_directory=args.txt,
        goldenset_path=goldenset,
        output_directory=args.saida,
    )

    if args.calibrar and classifier is not None and goldenset is not None:
        _print_calibration(args.txt, goldenset, classifier)

    if args.robustez and goldenset is not None:
        documents = TextDirectoryLoader(args.txt).load()
        expected = GoldensetLoader().load(goldenset)
        result = NoiseRobustnessEvaluator().evaluate(documents, expected)
        print(
            f"\nRobustez da extração a ruído: {result.detected}/{result.variants} "
            f"variantes encontradas ({result.recall:.4f})"
        )

    if args.robustez and classifier is not None:
        print("\nClassificação de citações sintéticas geradas da base:")
        synthetic = SyntheticCitationEvaluator(base, classifier).evaluate()
        for group, (hits, total) in synthetic.groups.items():
            print(f"  {group:<26}{hits:>5}/{total}")


def _print_calibration(
    txt: Path, goldenset: Path, classifier: CitationClassifier
) -> None:
    """Taxa de acerto por regra, sem os ajustes de desenvolvimento."""
    documents = TextDirectoryLoader(txt).load()
    detector = CitationDetector()
    predictions = {
        document.documento_id: classifier.classify_many(detector.detect(document))
        for document in documents
    }
    stats = measure_rules(predictions, load_annotations(goldenset))
    print("\nTaxa de acerto por regra (confiança sugerida com Laplace):")
    for rule, (hits, total) in sorted(stats.items()):
        print(f"  {rule:<32}{hits:>5}/{total:<5}{laplace(hits, total):.4f}")


if __name__ == "__main__":
    main()
