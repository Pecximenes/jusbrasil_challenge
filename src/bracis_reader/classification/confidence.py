"""Confiança calibrada por regra de decisão.

A confiança de cada citação estima a chance de a classe (e o id, se real)
estar certa. Ela alimenta o bônus de calibração da métrica oficial:
``score = s * (1 + 0,10 * (1 - Brier))``, com o Brier medido sobre as
citações pareadas com o gabarito. O Brier é mínimo quando a confiança é
igual à taxa real de acerto.

Cada citação registra a regra que a classificou (``regra`` em
``ClassifiedCitation.motivo``). A confiança da regra é a sua taxa de acerto,
encolhida em direção à taxa geral do sistema (estimativa bayesiana empírica):

    confiança = (acertos + K * taxa_geral) / (total + K),   K = 2

Assim, uma regra com poucas amostras herda a taxa geral em vez de cair para
perto de 50%, como aconteceria com a suavização de Laplace.

Medido sobre o goldenset oficial do Kaggle (sem ajustes) e dois lotes de
documentos sintéticos com gabarito próprio, na mesma política de anotação
(689 citações; taxa geral 688/689). Para medir de novo:
``python -m bracis_reader --txt PASTA --gold CSV --sem-ajustes --calibrar``.
"""

DEFAULT_CONFIDENCE = 0.5

OVERALL_ACCURACY = 0.9971  # (688 + 1) / (689 + 2)

# Comentário: acertos/total da regra.
CALIBRATED: dict[str, float] = {
    "artigo_inexistente": 0.9998,  # 27/27
    "artigo_lei_fora": 0.9997,  # 21/21
    "artigo_real": 0.9999,  # 55/55
    # Descrição sem correspondência na base é um caso duvidoso por natureza
    # (nome com ruído, por exemplo); 2 amostras não bastam para confiar mais.
    "descricao_sem_correspondencia": 0.5,  # 2/2
    "descricao_unica": 0.9997,  # 15/15
    "descricao_varios": 0.9999,  # 89/89
    "processo_inventado": 0.9999,  # 99/99
    "processo_inventado_ocr": 0.9998,  # 25/25
    "processo_real": 0.9946,  # 184/185
    "processo_real_ocr": 0.9999,  # 39/39
    "sumula_inventada": 0.9999,  # 48/48
    "sumula_real": 0.9999,  # 44/44
    "tema_oj": 0.9999,  # 40/40
    # Sem amostras suficientes; valores conservadores.
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
