"""Ajuste pontual para o conjunto de desenvolvimento.

No goldenset oficial do Kaggle (``goldenset_offsets.csv``), o processo TSE
0606252-11.2018.6.26.0000 tem dois registros de texto idêntico na base, mas o
gabarito aceita só um deles. Não há informação no texto que permita escolher;
este módulo força o id aceito **somente** nesse documento.

Segurança para dados novos:

- o documento é identificado pelo SHA-256 do texto completo, e não pelo
  nome. O conjunto oculto pode reutilizar nomes como ``gen_n1_013``; se o
  texto for diferente em um único caractere, nada aqui é aplicado;
- o ajuste também exige que o detector tenha encontrado exatamente o mesmo
  intervalo; se não encontrou, é ignorado;
- o trecho gravado é sempre ``texto[inicio:fim]``.

Para medir sem o ajuste: ``--sem-ajustes``.
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

CORRECTIONS = (
    DevCorrection(
        _GEN_N1_013, 2532, 2603, 2532, 2603, 1931806554,
        "dois registros de texto idêntico; gabarito aceita só este",
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
