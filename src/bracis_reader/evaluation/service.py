"""Compara a saída do fluxo com o goldenset e publica as métricas."""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from bracis_reader.domain.models import TextDocument
from bracis_reader.domain.ports import CandidatesByDocument, ResultsByDocument
from bracis_reader.evaluation.classification import (
    ClassificationEvaluator,
    ClassificationSummary,
)
from bracis_reader.evaluation.evaluator import (
    CitationEvaluator,
    DocumentEvaluation,
    EvaluationSummary,
)
from bracis_reader.evaluation.goldenset import GoldensetLoader, load_annotations
from bracis_reader.evaluation.official import OfficialScore, official_score
from bracis_reader.ingestion.level_splitter import DocumentLevelSplitter


class EvaluationReporter(Protocol):
    """Quem apresenta as métricas calculadas."""

    def print_report(
        self,
        evaluations: list[DocumentEvaluation],
        summary: EvaluationSummary,
        total_documents: int,
        n1_documents: int,
        n2_documents: int,
        criterion: str | None = None,
    ) -> None: ...

    def print_classification(self, summary: ClassificationSummary) -> None: ...

    def print_official(self, score: OfficialScore) -> None: ...


@dataclass(frozen=True)
class EvaluationOutcome:
    extraction: EvaluationSummary
    classification: ClassificationSummary | None


class GoldensetEvaluationService:
    """Mede extração, classificação e a nota oficial contra um gabarito."""

    def __init__(
        self,
        reporter: EvaluationReporter,
        extraction_evaluator: CitationEvaluator | None = None,
        classification_evaluator: ClassificationEvaluator | None = None,
        splitter: DocumentLevelSplitter | None = None,
    ) -> None:
        self._reporter = reporter
        self._extraction = extraction_evaluator or CitationEvaluator()
        self._classification = classification_evaluator or ClassificationEvaluator()
        self._splitter = splitter or DocumentLevelSplitter()

    def evaluate(
        self,
        documents: list[TextDocument],
        predictions: CandidatesByDocument,
        results: ResultsByDocument,
        goldenset_path: str | Path,
    ) -> EvaluationOutcome:
        extraction = self._evaluate_extraction(documents, predictions, goldenset_path)
        classification = None
        if results:
            annotations = load_annotations(goldenset_path)
            classification = self._classification.evaluate(results, annotations)
            self._reporter.print_classification(classification)
            self._reporter.print_official(official_score(results, annotations))
        return EvaluationOutcome(extraction, classification)

    def _evaluate_extraction(
        self,
        documents: list[TextDocument],
        predictions: CandidatesByDocument,
        goldenset_path: str | Path,
    ) -> EvaluationSummary:
        documents_n1, documents_n2 = self._splitter.split(documents)
        evaluations, summary = self._extraction.evaluate(
            documents=documents,
            predictions=predictions,
            expected_by_document=GoldensetLoader().load(goldenset_path),
        )
        self._reporter.print_report(
            evaluations=evaluations,
            summary=summary,
            total_documents=len(documents),
            n1_documents=len(documents_n1),
            n2_documents=len(documents_n2),
            criterion=self._extraction.criterion,
        )
        return summary
