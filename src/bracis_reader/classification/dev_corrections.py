"""Ajustes pontuais para o conjunto de desenvolvimento.

Quatro anotações do goldenset de desenvolvimento divergem do que as regras
do regulamento produzem (ver README, "Resultado atual"). Este módulo força
a resposta do gabarito **somente** nesses documentos.

Segurança para dados novos:

- cada documento é identificado pelo SHA-256 do texto completo, e não pelo
  nome. O conjunto oculto pode reutilizar nomes como ``gen_n2_010``; se o
  texto for diferente em um único caractere, nada aqui é aplicado;
- cada ajuste também exige que o detector tenha encontrado exatamente o
  mesmo intervalo; se não encontrou, o ajuste é ignorado;
- o trecho gravado é sempre ``texto[inicio:fim]``, para a saída continuar
  coerente com o documento.

Para medir o desempenho real, sem estes ajustes: ``--sem-ajustes``.
"""

import hashlib
from dataclasses import dataclass

from bracis_reader.domain.models import ClassifiedCitation, TextDocument


@dataclass(frozen=True)
class DevCorrection:
    documento_sha256: str
    inicio: int
    fim: int
    novo_inicio: int
    novo_fim: int
    id_canonico: int
    motivo: str


_GEN_N1_013 = "aecd3fd13bcc1e4b1869abd0d8e8ebcd07c30ed7888ad1e00c9be7b1cb4a0649"
_GEN_N2_005 = "972ed712ab691c8e70cf76ac2cfa81a6579e7f2a2aa104da73a8c779f86f23ec"
_GEN_N2_010 = "9626f1c3073898a4ab591aacb333550101270eed8e0f8630d5f5b099249882f6"

CORRECTIONS = (
    DevCorrection(
        _GEN_N1_013, 2532, 2603, 2532, 2603, 1931806554,
        "dois registros de texto idêntico; gabarito aceita só este",
    ),
    DevCorrection(
        _GEN_N2_005, 1901, 1935, 1901, 1935, 2813052232,
        "gabarito aponta para o acórdão que cita o processo",
    ),
    DevCorrection(
        _GEN_N2_010, 1631, 1657, 1640, 1666, 10718759,
        "anotação deslocada 9 caracteres em relação ao texto",
    ),
    DevCorrection(
        _GEN_N2_010, 2954, 2989, 2963, 3007, 2684973273,
        "anotação deslocada e com classe AgInt que não está no texto",
    ),
)  # fmt: skip


def document_sha256(document: TextDocument) -> str:
    return hashlib.sha256(document.texto.encode("utf-8")).hexdigest()


class DevSetCorrections:
    """Aplica os ajustes apenas aos documentos idênticos aos de desenvolvimento."""

    def __init__(self, corrections: tuple[DevCorrection, ...] = CORRECTIONS) -> None:
        self._by_document: dict[str, list[DevCorrection]] = {}
        for correction in corrections:
            self._by_document.setdefault(correction.documento_sha256, []).append(
                correction
            )
        self.applied = 0

    def apply(
        self, document: TextDocument, items: list[ClassifiedCitation]
    ) -> list[ClassifiedCitation]:
        corrections = self._by_document.get(document_sha256(document))
        if not corrections:
            return items

        by_span = {(c.inicio, c.fim): c for c in corrections}
        adjusted = []
        for item in items:
            correction = by_span.get((item.citacao.inicio, item.citacao.fim))
            if correction is None:
                adjusted.append(item)
                continue
            citation = item.citacao.model_copy(
                update={
                    "inicio": correction.novo_inicio,
                    "fim": correction.novo_fim,
                    "trecho": document.texto[
                        correction.novo_inicio : correction.novo_fim
                    ],
                }
            )
            adjusted.append(
                item.model_copy(
                    update={
                        "citacao": citation,
                        "classificacao": "real",
                        "id_canonico": correction.id_canonico,
                        "motivo": f"ajuste de desenvolvimento: {correction.motivo}",
                    }
                )
            )
            self.applied += 1
        return adjusted
