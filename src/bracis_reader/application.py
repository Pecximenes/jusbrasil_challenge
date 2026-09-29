"""Caso de uso completo: ler, extrair, classificar, avaliar e gravar."""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from bracis_reader.domain.ports import DocumentSource, ResultsByDocument, ResultWriter
from bracis_reader.evaluation.classification import ClassificationSummary
from bracis_reader.evaluation.evaluator import EvaluationSummary
from bracis_reader.evaluation.service import GoldensetEvaluationService
from bracis_reader.extraction.detector import CitationDetector
from bracis_reader.ingestion.directory_loader import TextDirectoryLoader
from bracis_reader.pipeline import CitationPipeline
from bracis_reader.reporting.console import ConsoleReportPrinter
from bracis_reader.reporting.submission import SubmissionWriter

SourceFactory = Callable[[Path], DocumentSource]
WriterFactory = Callable[[Path], ResultWriter]


class SubmissionReporter(Protocol):
    def print_submission(self, results: ResultsByDocument, path: Path) -> None: ...


@dataclass(frozen=True)
class PipelineResult:
    """O que a execução produziu. Métricas só existem quando há gabarito."""

    extraction: EvaluationSummary | None
    classification: ClassificationSummary | None
    results: ResultsByDocument
    submission_path: Path | None


class CitationExtractionApplication:
    """Coordena as etapas sem conhecer as regras de nenhuma delas."""

    def __init__(
        self,
        pipeline: CitationPipeline | None = None,
        evaluation: GoldensetEvaluationService | None = None,
        reporter: SubmissionReporter | None = None,
        source_factory: SourceFactory = TextDirectoryLoader,
        writer_factory: WriterFactory = SubmissionWriter,
    ) -> None:
        console = ConsoleReportPrinter()
        self._pipeline = pipeline or CitationPipeline(CitationDetector())
        self._evaluation = evaluation or GoldensetEvaluationService(console)
        self._reporter = reporter or console
        self._source_factory = source_factory
        self._writer_factory = writer_factory

    def run(
        self,
        txt_directory: str | Path,
        goldenset_path: str | Path | None = None,
        output_directory: str | Path | None = None,
    ) -> PipelineResult:
        documents = self._source_factory(Path(txt_directory)).load()
        output = self._pipeline.process(documents)

        extraction = classification = None
        if goldenset_path is not None:
            outcome = self._evaluation.evaluate(
                documents, output.predictions, output.results, goldenset_path
            )
            extraction, classification = outcome.extraction, outcome.classification

        submission_path = None
        if output_directory is not None and output.results:
            writer = self._writer_factory(Path(output_directory))
            submission_path = writer.write(output.results)
            self._reporter.print_submission(output.results, submission_path)

        return PipelineResult(
            extraction=extraction,
            classification=classification,
            results=output.results,
            submission_path=submission_path,
        )
