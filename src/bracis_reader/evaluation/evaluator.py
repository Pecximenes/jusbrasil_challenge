"""Avaliação das citações extraídas por correspondência exata."""

from dataclasses import dataclass

from bracis_reader.domain.models import CitationCandidate, TextDocument
from bracis_reader.evaluation.goldenset import CitationKey, GoldensetByDocument


@dataclass(frozen=True)
class DocumentEvaluation:
    """Contagens de avaliação de um único documento."""

    documento_id: str
    expected: int
    predicted: int
    true_positives: int
    false_positives: int
    false_negatives: int


@dataclass(frozen=True)
class EvaluationSummary:
    """Métricas agregadas de todos os documentos."""

    expected: int
    predicted: int
    true_positives: int
    false_positives: int
    false_negatives: int

    @property
    def precision(self) -> float:
        return self._safe_divide(self.true_positives, self.predicted)

    @property
    def recall(self) -> float:
        return self._safe_divide(self.true_positives, self.expected)

    @property
    def f1_score(self) -> float:
        denominator = self.precision + self.recall
        if denominator == 0:
            return 0.0
        return 2 * self.precision * self.recall / denominator

    @staticmethod
    def _safe_divide(numerator: int, denominator: int) -> float:
        return numerator / denominator if denominator else 0.0


class CitationEvaluator:
    """Compara spans previstos e esperados sem aproximação textual."""

    def evaluate(
        self,
        documents: list[TextDocument],
        predictions: dict[str, list[CitationCandidate]],
        expected_by_document: GoldensetByDocument,
    ) -> tuple[list[DocumentEvaluation], EvaluationSummary]:
        """Calcula TP, FP e FN para cada documento e para o conjunto."""
        evaluations = [
            self._evaluate_document(
                document=document,
                predictions=predictions.get(document.documento_id, []),
                expected=expected_by_document.get(document.documento_id, set()),
            )
            for document in documents
        ]
        return evaluations, self._summarize(evaluations)

    @staticmethod
    def _evaluate_document(
        document: TextDocument,
        predictions: list[CitationCandidate],
        expected: set[CitationKey],
    ) -> DocumentEvaluation:
        predicted = {
            (citation.inicio, citation.fim, citation.trecho) for citation in predictions
        }
        true_positives = predicted & expected

        return DocumentEvaluation(
            documento_id=document.documento_id,
            expected=len(expected),
            predicted=len(predicted),
            true_positives=len(true_positives),
            false_positives=len(predicted - expected),
            false_negatives=len(expected - predicted),
        )

    @staticmethod
    def _summarize(
        evaluations: list[DocumentEvaluation],
    ) -> EvaluationSummary:
        return EvaluationSummary(
            expected=sum(item.expected for item in evaluations),
            predicted=sum(item.predicted for item in evaluations),
            true_positives=sum(item.true_positives for item in evaluations),
            false_positives=sum(item.false_positives for item in evaluations),
            false_negatives=sum(item.false_negatives for item in evaluations),
        )
