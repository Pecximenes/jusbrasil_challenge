"""Citações identificadas pelo número do processo."""

import re

from bracis_reader.classification.canonical_base import (
    CanonicalBase,
    Feito,
    extract_numbers,
    extract_uf,
    raw_numbers,
)
from bracis_reader.classification.legal_text import court_mentioned, plain
from bracis_reader.classification.normalization import cnj_justice_segment
from bracis_reader.classification.resolvers.base import Resolution

_CNJ_SEGMENT_COURT = {"5": "TST", "6": "TSE", "7": "STM"}

_CLASS_COURT_HINTS: tuple[tuple[str, str], ...] = (
    (r"eleitoral|respe|\bagr-", "TSE"),
    (r"\btst\b|\b(?:ai)?rr\b|\barr\b|revista", "TST"),
    (r"\bapl\b|\brse\b|apela|sentido estrito", "STM"),
    (r"\bresp\b|\baresp\b|especial|\brhc\b|\brms\b|\bagrg\b|\bedcl\b", "STJ"),
    (r"\bre\b|\bare\b|extraordin|\badi\b|\badpf\b|\badc\b", "STF"),
)

_APPEAL_MARKERS = {
    "agravo": (
        r"\bag(?:int|rg|r|reg)?\b|\bag\.\s?(?:int|reg|rg)"
        r"|agravo (?:interno|regimental)"
    ),
    "declaracao": r"\bed(?:cl|s)?\b|embargos de declara",
    "embargos": r"\be-|\bembargos(?! de declara)|\beresp\b",
}


def _appeal_markers(text: str) -> set[str]:
    normalized = plain(text)
    return {
        name
        for name, pattern in _APPEAL_MARKERS.items()
        if re.search(pattern, normalized)
    }


def _class_prefix(text: str) -> str:
    return re.split(r"\d", text, maxsplit=1)[0]


class ProcessNumberResolver:
    """Procura o feito pelo número e escolhe o registro da classe citada."""

    def __init__(self, base: CanonicalBase) -> None:
        self._base = base

    def resolve(self, trecho: str) -> Resolution:
        keys = extract_numbers(trecho)
        if not keys:
            return Resolution.incompleta("processo_sem_numero", "sem número utilizável")

        feitos = {
            (feito.tribunal, feito.numero): feito
            for key in keys
            for feito in self._base.find_feitos(key)
        }
        candidates = list(feitos.values())
        ocr_used = any(
            char.isalpha() for number in raw_numbers(trecho) for char in number
        )

        if not candidates:
            rule = "processo_inventado_ocr" if ocr_used else "processo_inventado"
            return Resolution.inventada(rule, "número fora da base")

        if len(candidates) > 1:
            candidates = self._break_tie(trecho, keys, candidates)

        if len(candidates) > 1:
            return Resolution.incompleta(
                "processo_ambiguo", f"{len(candidates)} feitos com o mesmo número"
            )

        feito = candidates[0]
        uf = extract_uf(trecho)
        rule = "processo_real_ocr" if ocr_used else "processo_real"
        if uf and feito.ufs and uf not in feito.ufs:
            rule = "processo_real_uf_divergente"
        return Resolution.real(
            self._best_record(trecho, feito), rule, f"feito {feito.tribunal}"
        )

    @staticmethod
    def _best_record(trecho: str, feito: Feito) -> int:
        """Registro do feito cuja classe mais se parece com a citada."""
        cited = _appeal_markers(_class_prefix(trecho))

        def distance(record_id: int) -> tuple[int, int]:
            heading = _class_prefix(feito.headings.get(record_id, ""))
            return (len(cited ^ _appeal_markers(heading)), record_id)

        return min(feito.ids, key=distance)

    @staticmethod
    def _court_hint(trecho: str, keys: list[str]) -> str | None:
        court = court_mentioned(trecho)
        if court is not None:
            return court
        for key in keys:
            court = _CNJ_SEGMENT_COURT.get(cnj_justice_segment(key) or "")
            if court:
                return court
        normalized = plain(trecho)
        return next(
            (c for pattern, c in _CLASS_COURT_HINTS if re.search(pattern, normalized)),
            None,
        )

    def _break_tie(
        self, trecho: str, keys: list[str], candidates: list[Feito]
    ) -> list[Feito]:
        court = self._court_hint(trecho, keys)
        uf = extract_uf(trecho)
        narrowed = [f for f in candidates if court is None or f.tribunal == court]
        if uf and len(narrowed) > 1:
            by_uf = [f for f in narrowed if uf in f.ufs]
            narrowed = by_uf or narrowed
        return narrowed or candidates
