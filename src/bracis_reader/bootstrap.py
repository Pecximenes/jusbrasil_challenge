"""Raiz de composição: o único lugar que escolhe as implementações."""

from dataclasses import dataclass

from bracis_reader.application import CitationExtractionApplication
from bracis_reader.classification.canonical_base import CanonicalBase
from bracis_reader.classification.classifier import CitationClassifier
from bracis_reader.classification.confidence import (
    CalibratedConfidence,
    ConfidencePolicy,
    FixedConfidence,
)
from bracis_reader.evaluation.evaluator import CitationEvaluator
from bracis_reader.evaluation.service import GoldensetEvaluationService
from bracis_reader.extraction.detector import CitationDetector
from bracis_reader.pipeline import CitationPipeline
from bracis_reader.reporting.console import ConsoleReportPrinter
from bracis_reader.settings import Settings


@dataclass(frozen=True)
class Components:
    """Objetos montados para uma execução."""

    application: CitationExtractionApplication
    base: CanonicalBase | None
    classifier: CitationClassifier | None


def confidence_policy(settings: Settings) -> ConfidencePolicy:
    return FixedConfidence(1.0) if settings.max_confidence else CalibratedConfidence()


def build(settings: Settings) -> Components:
    base = CanonicalBase(settings.base) if settings.base.is_file() else None
    classifier = (
        CitationClassifier.from_base(base, confidence_policy(settings))
        if base is not None
        else None
    )
    reporter = ConsoleReportPrinter()
    evaluation = GoldensetEvaluationService(
        reporter,
        extraction_evaluator=CitationEvaluator(
            iou_threshold=None if settings.exact_match else 0.5
        ),
    )
    pipeline = CitationPipeline(
        CitationDetector(include_generic=settings.include_generic), classifier
    )
    application = CitationExtractionApplication(
        pipeline=pipeline, evaluation=evaluation, reporter=reporter
    )
    return Components(application=application, base=base, classifier=classifier)
