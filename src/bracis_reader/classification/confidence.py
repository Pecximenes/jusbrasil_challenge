"""Políticas de confiança atribuída a cada decisão do classificador."""

from typing import Protocol

DEFAULT_CONFIDENCE = 0.5

CALIBRATED: dict[str, float] = {
    "artigo_inexistente": 0.9998,
    "artigo_lei_fora": 0.9997,
    "artigo_real": 0.9999,
    "descricao_sem_correspondencia": 0.5,
    "descricao_unica": 0.9997,
    "descricao_varios": 0.9999,
    "processo_inventado": 0.9999,
    "processo_inventado_ocr": 0.9998,
    "processo_real": 0.9946,
    "processo_real_ocr": 0.9999,
    "sumula_inventada": 0.9999,
    "sumula_real": 0.9999,
    "tema_oj": 0.9999,
    "processo_real_uf_divergente": 0.6,
    "processo_ambiguo": 0.6,
    "processo_sem_numero": 0.5,
    "sumula_ambigua": 0.6,
    "sumula_sem_numero": 0.5,
    "artigo_sem_numero": 0.5,
    "generica": 0.9,
}


class ConfidencePolicy(Protocol):
    """Converte a regra que decidiu a citação em uma probabilidade."""

    def for_rule(self, rule: str) -> float: ...


class CalibratedConfidence:
    """Taxa de acerto medida para cada regra (ver ``--calibrar``)."""

    def __init__(
        self,
        table: dict[str, float] | None = None,
        default: float = DEFAULT_CONFIDENCE,
    ) -> None:
        self._table = CALIBRATED if table is None else table
        self._default = default

    def for_rule(self, rule: str) -> float:
        return self._table.get(rule, self._default)


class FixedConfidence:
    """Mesma confiança para todas as decisões."""

    def __init__(self, value: float = 1.0) -> None:
        if not 0.0 <= value <= 1.0:
            raise ValueError("a confiança deve estar entre 0 e 1")
        self._value = value

    def for_rule(self, rule: str) -> float:
        return self._value
