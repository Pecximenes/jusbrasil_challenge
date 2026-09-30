"""Relatórios auxiliares: calibração da confiança e robustez."""

from pathlib import Path

from bracis_reader.classification.canonical_base import CanonicalBase
from bracis_reader.domain.ports import CitationClassifierPort
from bracis_reader.evaluation.calibration import laplace, measure_rules
from bracis_reader.evaluation.goldenset import GoldensetLoader, load_annotations
from bracis_reader.evaluation.robustness import NoiseRobustnessEvaluator
from bracis_reader.evaluation.synthetic import SyntheticCitationEvaluator
from bracis_reader.extraction.detector import CitationDetector
from bracis_reader.ingestion.directory_loader import TextDirectoryLoader


def print_calibration(
    txt: Path, goldenset: Path, classifier: CitationClassifierPort
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


def print_noise_robustness(txt: Path, goldenset: Path) -> None:
    """Quantas variantes ruidosas das citações do gabarito ainda são achadas."""
    documents = TextDirectoryLoader(txt).load()
    expected = GoldensetLoader().load(goldenset)
    result = NoiseRobustnessEvaluator().evaluate(documents, expected)
    print(
        f"\nRobustez da extração a ruído: {result.detected}/{result.variants} "
        f"variantes encontradas ({result.recall:.4f})"
    )


def print_synthetic(base: CanonicalBase, classifier: CitationClassifierPort) -> None:
    """Acerto em citações montadas a partir dos registros da base."""
    print("\nClassificação de citações sintéticas geradas da base:")
    synthetic = SyntheticCitationEvaluator(base, classifier).evaluate()
    for group, (hits, total) in synthetic.groups.items():
        print(f"  {group:<26}{hits:>5}/{total}")
