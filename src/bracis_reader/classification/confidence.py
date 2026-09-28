"""Confiança calibrada por regra de decisão.

A confiança de cada citação é a taxa de acerto medida para a regra que a
classificou (``regra`` em ``ClassifiedCitation.motivo``). A tabela abaixo é
gerada por ``python -m bracis_reader --calibrar``, que roda o pipeline sobre
um ou mais conjuntos com gabarito e aplica suavização de Laplace:

    confiança = (acertos + 1) / (total + 2)

Regras sem amostra ficam com ``DEFAULT_CONFIDENCE``.
"""

DEFAULT_CONFIDENCE = 0.5

# Medido sobre o goldenset de desenvolvimento (sem ajustes) e dois lotes de
# documentos sintéticos com gabarito próprio (30 documentos cada), 802
# citações ao todo. Entre parênteses: acertos/total.
CALIBRATED: dict[str, float] = {
    "artigo_inexistente": 0.9655,  # 27/27
    "artigo_lei_fora": 0.9565,  # 21/21
    "artigo_real": 0.9649,  # 54/55
    "descricao_sem_correspondencia": 0.7500,  # 2/2
    "descricao_unica": 0.9412,  # 15/15
    "descricao_varios": 0.9890,  # 89/89
    "generica": 0.9903,  # 101/101
    "processo_inventado": 0.9901,  # 99/99
    "processo_inventado_ocr": 0.9630,  # 25/25
    "processo_real": 0.9786,  # 182/185
    "processo_real_ocr": 0.9756,  # 39/39
    "sumula_inventada": 0.9800,  # 48/48
    "sumula_real": 0.9783,  # 44/44
    "tema_oj": 0.9762,  # 40/40
    # Sem amostras suficientes; valores conservadores.
    "processo_real_uf_divergente": 0.6,
    "processo_ambiguo": 0.6,
    "processo_sem_numero": 0.5,
    "sumula_ambigua": 0.6,
    "sumula_sem_numero": 0.5,
    "artigo_sem_numero": 0.5,
}


def confidence_for(rule: str) -> float:
    return CALIBRATED.get(rule, DEFAULT_CONFIDENCE)
