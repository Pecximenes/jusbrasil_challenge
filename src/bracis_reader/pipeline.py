"""Orquestração do fluxo completo: leitura, extração, classificação e avaliação."""

from dataclasses import dataclass
from pathlib import Path

from bracis_reader.classification.classifier import CitationClassifier
from bracis_reader.domain.models import ClassifiedCitation
from bracis_reader.evaluation.classification import (
    ClassificationEvaluator,
    ClassificationSummary,
)
from bracis_reader.evaluation.evaluator import CitationEvaluator, EvaluationSummary
from bracis_reader.evaluation.goldenset import GoldensetLoader, load_annotations
from bracis_reader.extraction.detector import CitationDetector
from bracis_reader.ingestion.directory_loader import TextDirectoryLoader
from bracis_reader.ingestion.level_splitter import DocumentLevelSplitter
from bracis_reader.reporting.console import ConsoleReportPrinter
from bracis_reader.reporting.submission import SubmissionWriter


@dataclass(frozen=True)
class PipelineResult:
    """O que o pipeline produziu. Métricas só existem quando há gabarito."""

    extraction: EvaluationSummary | None
    classification: ClassificationSummary | None
    results: dict[str, list[ClassifiedCitation]]
    submission_path: Path | None


class CitationExtractionApplication:
    """Coordena os componentes sem concentrar suas regras de negócio."""

    def __init__(
        self,
        detector: CitationDetector | None = None,
        evaluator: CitationEvaluator | None = None,
        reporter: ConsoleReportPrinter | None = None,
        classifier: CitationClassifier | None = None,
    ) -> None:
        self._detector = detector or CitationDetector()
        self._evaluator = evaluator or CitationEvaluator()
        self._reporter = reporter or ConsoleReportPrinter()
        self._classifier = classifier

    def run(
        self,
        txt_directory: str | Path,
        goldenset_path: str | Path | None = None,
        output_directory: str | Path | None = None,
    ) -> PipelineResult:
        """Executa o pipeline.

        Sem ``goldenset_path`` (caso do conjunto oculto), apenas extrai,
        classifica e grava a saída.
        """
        documents = TextDirectoryLoader(txt_directory).load()
        predictions = self._detector.detect_many(documents)

        results: dict[str, list[ClassifiedCitation]] = {}
        if self._classifier is not None:
            results = {
                documento_id: self._classifier.classify_many(citations)
                for documento_id, citations in predictions.items()
            }

        extraction_summary = classification_summary = None
        if goldenset_path is not None:
            documents_n1, documents_n2 = DocumentLevelSplitter().split(documents)
            evaluations, extraction_summary = self._evaluator.evaluate(
                documents=documents,
                predictions=predictions,
                expected_by_document=GoldensetLoader().load(goldenset_path),
            )
            self._reporter.print_report(
                evaluations=evaluations,
                summary=extraction_summary,
                total_documents=len(documents),
                n1_documents=len(documents_n1),
                n2_documents=len(documents_n2),
                criterion=self._evaluator.criterion,
            )
            if results:
                classification_summary = ClassificationEvaluator().evaluate(
                    results, load_annotations(goldenset_path)
                )
                self._reporter.print_classification(classification_summary)

        submission_path = None
        if output_directory is not None and results:
            submission_path = SubmissionWriter(output_directory).write(results)
            total = sum(len(items) for items in results.values())
            print(f"\n{total} citações de {len(results)} documentos gravadas em")
            print(f"{submission_path.parent} (json/ e {submission_path.name})")

        return PipelineResult(
            extraction=extraction_summary,
            classification=classification_summary,
            results=results,
            submission_path=submission_path,
        )
