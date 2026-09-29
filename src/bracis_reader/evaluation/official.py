"""Nota oficial do desafio, reproduzindo o ``kaggle_metric.py`` da organização."""

from dataclasses import dataclass, field

from bracis_reader.domain.models import ClassifiedCitation
from bracis_reader.evaluation.goldenset import GoldCitation

CLASSES = ("real", "inventada", "incompleta")
LEVEL_WEIGHTS = {1: 1.0, 2: 2.0}
GAMMA = 0.5
BONUS_CAP = 0.10
IOU_MIN = 0.5
EXTRA_FRACTION = 0.9


@dataclass
class _Accumulator:
    tp: dict[str, int] = field(default_factory=lambda: dict.fromkeys(CLASSES, 0))
    fp: dict[str, int] = field(default_factory=lambda: dict.fromkeys(CLASSES, 0))
    fn: dict[str, int] = field(default_factory=lambda: dict.fromkeys(CLASSES, 0))
    support: dict[str, int] = field(default_factory=lambda: dict.fromkeys(CLASSES, 0))
    tau_num: int = 0
    tau_den: int = 0
    brier_terms: list[float] = field(default_factory=list)


@dataclass(frozen=True)
class LevelScore:
    macro_f1: float
    f1_per_class: dict[str, float]
    tau: float
    bonus: float
    score: float


@dataclass(frozen=True)
class OfficialScore:
    final: float
    levels: dict[int, LevelScore]


def _intersection(a: tuple[int, int], b: tuple[int, int]) -> int:
    return max(0, min(a[1], b[1]) - max(a[0], b[0]))


def _iou(a: tuple[int, int], b: tuple[int, int]) -> float:
    inter = _intersection(a, b)
    if inter == 0:
        return 0.0
    return inter / ((a[1] - a[0]) + (b[1] - b[0]) - inter)


def _match(golds: list[tuple[int, int]], preds: list[tuple[int, int]]):
    candidates = sorted(
        (-_iou(g, p), gi, pi)
        for gi, g in enumerate(golds)
        for pi, p in enumerate(preds)
        if _iou(g, p) >= IOU_MIN
    )
    used_g: set[int] = set()
    used_p: set[int] = set()
    pairs = []
    for _, gi, pi in candidates:
        if gi in used_g or pi in used_p:
            continue
        used_g.add(gi)
        used_p.add(pi)
        pairs.append((gi, pi))
    return pairs, used_g, used_p


def _accumulate(
    acc: _Accumulator,
    golds: list[GoldCitation],
    preds: list[ClassifiedCitation],
) -> None:
    gold_spans = [(g.inicio, g.fim) for g in golds]
    pred_spans = [(p.citacao.inicio, p.citacao.fim) for p in preds]
    pairs, used_g, used_p = _match(gold_spans, pred_spans)

    for gold in golds:
        acc.support[gold.classificacao] += 1
        acc.tau_den += gold.classificacao == "inventada"

    for gi, pi in pairs:
        gold, pred = golds[gi], preds[pi]
        expected, predicted = gold.classificacao, pred.classificacao
        if expected == predicted:
            hit = expected != "real" or pred.id_canonico in gold.ids_aceitos
            if hit:
                acc.tp[expected] += 1
            else:
                acc.fp["real"] += 1
        else:
            hit = False
            acc.fn[expected] += 1
            acc.fp[predicted] += 1
            acc.tau_num += expected == "inventada" and predicted == "real"
        acc.brier_terms.append((pred.confianca - (1.0 if hit else 0.0)) ** 2)

    for gi, gold in enumerate(golds):
        if gi not in used_g:
            acc.fn[gold.classificacao] += 1

    matched = [gold_spans[gi] for gi, _ in pairs]
    for pi, span in enumerate(pred_spans):
        if pi in used_p:
            continue
        width = span[1] - span[0]
        is_component = any(
            width > 0 and _intersection(span, g) / width >= EXTRA_FRACTION
            for g in matched
        )
        if not is_component:
            acc.fp[preds[pi].classificacao] += 1


def _level_score(acc: _Accumulator) -> LevelScore | None:
    f1s = {}
    for c in CLASSES:
        if acc.support[c] == 0:
            continue
        denom = 2 * acc.tp[c] + acc.fp[c] + acc.fn[c]
        f1s[c] = 2 * acc.tp[c] / denom if denom else 0.0
    if not f1s:
        return None
    macro = sum(f1s.values()) / len(f1s)
    tau = acc.tau_num / acc.tau_den if acc.tau_den else 0.0
    s = macro * (1.0 - GAMMA * tau)
    bonus = 0.0
    if acc.brier_terms:
        brier = sum(acc.brier_terms) / len(acc.brier_terms)
        bonus = max(0.0, min(BONUS_CAP, BONUS_CAP * (1.0 - brier)))
    return LevelScore(macro, f1s, tau, bonus, s * (1.0 + bonus))


def official_score(
    predictions: dict[str, list[ClassifiedCitation]],
    annotations: dict[str, list[GoldCitation]],
) -> OfficialScore:
    """Nota oficial, documento a documento, agregada por nível."""
    accumulators: dict[int, _Accumulator] = {}
    for documento_id in sorted(set(predictions) | set(annotations)):
        golds = annotations.get(documento_id, [])
        level = golds[0].nivel if golds else (2 if "_n2_" in documento_id else 1)
        _accumulate(
            accumulators.setdefault(level, _Accumulator()),
            golds,
            predictions.get(documento_id, []),
        )
    levels = {
        level: score
        for level, acc in sorted(accumulators.items())
        if (score := _level_score(acc)) is not None
    }
    total_weight = sum(LEVEL_WEIGHTS.get(level, 1.0) for level in levels)
    final = (
        sum(LEVEL_WEIGHTS.get(level, 1.0) * s.score for level, s in levels.items())
        / total_weight
        if total_weight
        else 0.0
    )
    return OfficialScore(final=final, levels=levels)
