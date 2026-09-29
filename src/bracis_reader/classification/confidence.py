"""Confiança calibrada por regra de decisão."""

DEFAULT_CONFIDENCE = 0.5

OVERALL_ACCURACY = 0.9971

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


def confidence_for(rule: str) -> float:
    return CALIBRATED.get(rule, DEFAULT_CONFIDENCE)
