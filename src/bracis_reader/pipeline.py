"""Orquestração do fluxo completo de leitura, extração e avaliação."""

from pathlib import Path

from bracis_reader.evaluation.evaluator import CitationEvaluator, EvaluationSummary
from bracis_reader.evaluation.goldenset import GoldensetLoader
from bracis_reader.extraction.detector import CitationDetector
from bracis_reader.ingestion.directory_loader import TextDirectoryLoader
from bracis_reader.ingestion.level_splitter import DocumentLevelSplitter
from bracis_reader.reporting.console import ConsoleReportPrinter


class CitationExtractionApplication:
    """Coordena os componentes sem concentrar suas regras de negócio."""

    def __init__(
        self,
        detector: CitationDetector | None = None,
        evaluator: CitationEvaluator | None = None,
        reporter: ConsoleReportPrinter | None = None,
    ) -> None:
        self._detector = detector or CitationDetector()
        self._evaluator = evaluator or CitationEvaluator()
        self._reporter = reporter or ConsoleReportPrinter()

    def run(
        self,
        txt_directory: str | Path,
        goldenset_path: str | Path,
    ) -> EvaluationSummary:
        """Executa o pipeline e devolve as métricas agregadas."""
        documents = TextDirectoryLoader(txt_directory).load()
        documents_n1, documents_n2 = DocumentLevelSplitter().split(documents)
        predictions = self._detector.detect_many(documents)
        expected = GoldensetLoader().load(goldenset_path)
        evaluations, summary = self._evaluator.evaluate(
            documents=documents,
            predictions=predictions,
            expected_by_document=expected,
        )
        self._reporter.print_report(
            evaluations=evaluations,
            summary=summary,
            total_documents=len(documents),
            n1_documents=len(documents_n1),
            n2_documents=len(documents_n2),
        )
        return summary
