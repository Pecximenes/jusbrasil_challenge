"""Confiança calibrada por regra de decisão.

A confiança de cada citação estima a chance de a classe (e o id, se real)
estar certa, para o bônus de calibração do desafio. É o produto de dois
fatores:

1. **taxa de acerto da regra** que classificou a citação (``regra`` em
   ``ClassifiedCitation.motivo``), com suavização de Laplace:
   ``(acertos + 1) / (total + 2)``;
2. **concordância com o gabarito oficial**: no goldenset de
   desenvolvimento, sem ajustes, 221 de 225 citações (0,9822) saem certas.
   Os 4 erros vêm de anotações divergentes (offsets deslocados, id de outro
   registro), um ruído que pode atingir qualquer regra. O fator desconta
   esse ruído para a confiança não ficar otimista.

A taxa por regra foi medida em 802 citações: o goldenset de desenvolvimento
e dois lotes de documentos sintéticos com gabarito próprio. Para medir de
novo com outro conjunto: ``python -m bracis_reader --txt PASTA --gold CSV
--sem-ajustes --calibrar``.

Regras sem amostra suficiente ficam com valores conservadores.
"""

DEFAULT_CONFIDENCE = 0.5

GOLD_AGREEMENT = 0.9822  # 221/225 no goldenset de desenvolvimento

# Laplace(acertos, total) x GOLD_AGREEMENT. Comentário: acertos/total.
CALIBRATED: dict[str, float] = {
    "artigo_inexistente": 0.9484,  # 27/27
    "artigo_lei_fora": 0.9395,  # 21/21
    "artigo_real": 0.9478,  # 54/55
    "descricao_sem_correspondencia": 0.7367,  # 2/2
    "descricao_unica": 0.9244,  # 15/15
    "descricao_varios": 0.9714,  # 89/89
    "generica": 0.9727,  # 101/101
    "processo_inventado": 0.9725,  # 99/99
    "processo_inventado_ocr": 0.9458,  # 25/25
    "processo_real": 0.9612,  # 182/185
    "processo_real_ocr": 0.9583,  # 39/39
    "sumula_inventada": 0.9626,  # 48/48
    "sumula_real": 0.9609,  # 44/44
    "tema_oj": 0.9588,  # 40/40
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
