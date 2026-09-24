"""Avaliação das citações extraídas contra o goldenset.

Dois critérios de acerto estão disponíveis:

- ``iou_threshold=0.5`` (padrão): mesmo critério da avaliação oficial do
  desafio. Previsão e gabarito formam um par quando a sobreposição dos
  intervalos (IoU) é de pelo menos 50%. Cada citação só pode ser usada em um
  par.
- ``iou_threshold=None``: correspondência exata de ``(inicio, fim, trecho)``.
"""

from dataclasses import dataclass

from bracis_reader.domain.models import CitationCandidate, TextDocument
from bracis_reader.evaluation.goldenset import CitationKey, GoldensetByDocument

Span = tuple[int, int]


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


def span_iou(first: Span, second: Span) -> float:
    """Interseção sobre união de dois intervalos ``[inicio, fim)``."""
    intersection = min(first[1], second[1]) - max(first[0], second[0])
    if intersection <= 0:
        return 0.0
    union = max(first[1], second[1]) - min(first[0], second[0])
    return intersection / union


def match_spans(
    predicted: list[Span],
    expected: list[Span],
    iou_threshold: float,
) -> list[tuple[int, int]]:
    """Pareia previsões e gabarito um-para-um, do maior IoU para o menor.

    Retorna os pares ``(indice_previsto, indice_esperado)``.
    """
    candidates = sorted(
        (
            (span_iou(pred, gold), i, j)
            for i, pred in enumerate(predicted)
            for j, gold in enumerate(expected)
        ),
        reverse=True,
    )
    used_predicted: set[int] = set()
    used_expected: set[int] = set()
    pairs: list[tuple[int, int]] = []

    for iou, i, j in candidates:
        if iou < iou_threshold:
            break
        if i in used_predicted or j in used_expected:
            continue
        used_predicted.add(i)
        used_expected.add(j)
        pairs.append((i, j))

    return pairs


class CitationEvaluator:
    """Compara citações previstas e esperadas."""

    def __init__(self, iou_threshold: float | None = 0.5) -> None:
        self._iou_threshold = iou_threshold

    @property
    def criterion(self) -> str:
        """Descrição curta do critério de acerto em uso."""
        if self._iou_threshold is None:
            return "correspondência exata"
        return f"IoU >= {self._iou_threshold:g}"

    def evaluate(
        self,
        documents: list[TextDocument],
        predictions: dict[str, list[CitationCandidate]],
        expected_by_document: GoldensetByDocument,
    ) -> tuple[list[DocumentEvaluation], EvaluationSummary]:
        """Calcula TP, FP e FN para cada documento e para o conjunto."""
        evaluations = [
            self._evaluate_document(
                documento_id=document.documento_id,
                predictions=predictions.get(document.documento_id, []),
                expected=expected_by_document.get(document.documento_id, set()),
            )
            for document in documents
        ]
        return evaluations, summarize(evaluations)

    def _evaluate_document(
        self,
        documento_id: str,
        predictions: list[CitationCandidate],
        expected: set[CitationKey],
    ) -> DocumentEvaluation:
        predicted_keys = {
            (citation.inicio, citation.fim, citation.trecho) for citation in predictions
        }

        if self._iou_threshold is None:
            true_positives = len(predicted_keys & expected)
        else:
            true_positives = len(
                match_spans(
                    predicted=[(start, end) for start, end, _ in predicted_keys],
                    expected=[(start, end) for start, end, _ in expected],
                    iou_threshold=self._iou_threshold,
                )
            )

        return DocumentEvaluation(
            documento_id=documento_id,
            expected=len(expected),
            predicted=len(predicted_keys),
            true_positives=true_positives,
            false_positives=len(predicted_keys) - true_positives,
            false_negatives=len(expected) - true_positives,
        )


def summarize(evaluations: list[DocumentEvaluation]) -> EvaluationSummary:
    """Soma as contagens de uma lista de avaliações por documento."""
    return EvaluationSummary(
        expected=sum(item.expected for item in evaluations),
        predicted=sum(item.predicted for item in evaluations),
        true_positives=sum(item.true_positives for item in evaluations),
        false_positives=sum(item.false_positives for item in evaluations),
        false_negatives=sum(item.false_negatives for item in evaluations),
    )
