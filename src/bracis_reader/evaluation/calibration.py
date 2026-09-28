"""Mede a taxa de acerto de cada regra de classificação.

Serve para calibrar a confiança (bônus de calibração do desafio): uma regra
que acerta 98% das vezes deve informar confiança perto de 0,98.

Uma previsão conta como acerto quando pareia com o gabarito (IoU >= 0,5), a
classe coincide e, se for ``real``, o id está entre os aceitos. Previsões que
não pareiam com nada contam como erro da regra que as produziu.
"""

from collections import defaultdict

from bracis_reader.domain.models import ClassifiedCitation
from bracis_reader.evaluation.evaluator import match_spans
from bracis_reader.evaluation.goldenset import GoldCitation

RuleStats = dict[str, list[int]]  # regra -> [acertos, total]


def rule_of(item: ClassifiedCitation) -> str:
    return item.motivo.split(":", 1)[0]


def measure_rules(
    predictions: dict[str, list[ClassifiedCitation]],
    annotations: dict[str, list[GoldCitation]],
    stats: RuleStats | None = None,
    iou_threshold: float = 0.5,
) -> RuleStats:
    stats = stats if stats is not None else defaultdict(lambda: [0, 0])
    for documento_id, predicted in predictions.items():
        gold = annotations.get(documento_id, [])
        pairs = dict(
            match_spans(
                [(p.citacao.inicio, p.citacao.fim) for p in predicted],
                [(g.inicio, g.fim) for g in gold],
                iou_threshold,
            )
        )
        for i, item in enumerate(predicted):
            j = pairs.get(i)
            hit = j is not None and item.classificacao == gold[j].classificacao
            if hit and item.classificacao == "real":
                hit = item.id_canonico in gold[j].ids_aceitos
            entry = stats[rule_of(item)]
            entry[0] += hit
            entry[1] += 1
    return stats


def laplace(hits: int, total: int) -> float:
    return (hits + 1) / (total + 2)
