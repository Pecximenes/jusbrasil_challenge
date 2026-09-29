"""Avaliação da classificação (real / inventada / incompleta)."""

from collections import Counter
from dataclasses import dataclass

from bracis_reader.domain.models import ClassifiedCitation
from bracis_reader.evaluation.evaluator import match_spans
from bracis_reader.evaluation.goldenset import GoldCitation

CLASSES = ("real", "inventada", "incompleta")
LEVEL_WEIGHT = {1: 1.0, 2: 2.0}


@dataclass(frozen=True)
class ClassMetrics:
    classe: str
    true_positives: float
    false_positives: float
    false_negatives: float

    @property
    def precision(self) -> float:
        predicted = self.true_positives + self.false_positives
        return self.true_positives / predicted if predicted else 0.0

    @property
    def recall(self) -> float:
        expected = self.true_positives + self.false_negatives
        return self.true_positives / expected if expected else 0.0

    @property
    def f1_score(self) -> float:
        total = self.precision + self.recall
        return 2 * self.precision * self.recall / total if total else 0.0


@dataclass(frozen=True)
class ClassificationSummary:
    per_class: tuple[ClassMetrics, ...]
    tipo_corretos: int
    pares: int

    @property
    def macro_f1(self) -> float:
        return sum(item.f1_score for item in self.per_class) / len(self.per_class)


class ClassificationEvaluator:
    """Compara classe, id e tipo das citações com o gabarito."""

    def __init__(self, iou_threshold: float = 0.5, weighted: bool = True) -> None:
        self._iou_threshold = iou_threshold
        self._weighted = weighted

    def evaluate(
        self,
        predictions: dict[str, list[ClassifiedCitation]],
        annotations: dict[str, list[GoldCitation]],
    ) -> ClassificationSummary:
        tp: Counter[str] = Counter()
        fp: Counter[str] = Counter()
        fn: Counter[str] = Counter()
        tipo_ok = pairs_total = 0

        for documento_id in sorted(set(predictions) | set(annotations)):
            predicted = predictions.get(documento_id, [])
            gold = annotations.get(documento_id, [])
            level = gold[0].nivel if gold else (2 if "_n2_" in documento_id else 1)
            weight = LEVEL_WEIGHT.get(level, 1.0) if self._weighted else 1.0

            pairs = match_spans(
                [(p.citacao.inicio, p.citacao.fim) for p in predicted],
                [(g.inicio, g.fim) for g in gold],
                self._iou_threshold,
            )
            hit_predicted: set[int] = set()
            hit_gold: set[int] = set()
            for i, j in pairs:
                pairs_total += 1
                tipo_ok += predicted[i].citacao.tipo == gold[j].tipo
                if self._is_hit(predicted[i], gold[j]):
                    hit_predicted.add(i)
                    hit_gold.add(j)
                    tp[gold[j].classificacao] += weight

            for i, prediction in enumerate(predicted):
                if i not in hit_predicted:
                    fp[prediction.classificacao] += weight
            for j, expected in enumerate(gold):
                if j not in hit_gold:
                    fn[expected.classificacao] += weight

        return ClassificationSummary(
            per_class=tuple(ClassMetrics(c, tp[c], fp[c], fn[c]) for c in CLASSES),
            tipo_corretos=tipo_ok,
            pares=pairs_total,
        )

    @staticmethod
    def _is_hit(prediction: ClassifiedCitation, gold: GoldCitation) -> bool:
        if prediction.classificacao != gold.classificacao:
            return False
        if gold.classificacao == "real":
            return prediction.id_canonico in gold.ids_aceitos
        return True
