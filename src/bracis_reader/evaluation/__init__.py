"""Avaliação das citações extraídas contra o goldenset."""

from bracis_reader.evaluation.evaluator import (
    CitationEvaluator,
    DocumentEvaluation,
    EvaluationSummary,
)
from bracis_reader.evaluation.goldenset import (
    CitationKey,
    GoldensetByDocument,
    GoldensetLoader,
)

__all__ = [
    "CitationEvaluator",
    "CitationKey",
    "DocumentEvaluation",
    "EvaluationSummary",
    "GoldensetByDocument",
    "GoldensetLoader",
]
