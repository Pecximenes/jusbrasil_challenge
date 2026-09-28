"""Gravação da saída no formato do desafio.

- um ``.json`` por documento, no formato do contrato de entrada e saída;
- ``submission.csv`` com uma linha por documento, no mesmo formato gerado
  por ``refs/json_to_submission.py``:
  ``inicio,fim,classe,id_canonico,confianca|...`` ("-" quando ausente).
"""

import csv
import json
from pathlib import Path

from bracis_reader.domain.models import ClassifiedCitation


def citation_to_contract(item: ClassifiedCitation) -> dict:
    citation = item.citacao
    return {
        "inicio": citation.inicio,
        "fim": citation.fim,
        "trecho": citation.trecho,
        "tipo": citation.tipo,
        "classificacao": item.classificacao,
        "resolucao": (
            {"id_canonico": item.id_canonico} if item.id_canonico is not None else None
        ),
        "confianca": round(item.confianca, 4),
    }


def _encode_submission(items: list[ClassifiedCitation]) -> str:
    parts = []
    for item in items:
        id_canonico = str(item.id_canonico) if item.id_canonico is not None else "-"
        parts.append(
            f"{item.citacao.inicio},{item.citacao.fim},{item.classificacao},"
            f"{id_canonico},{item.confianca:.4f}"
        )
    return "|".join(parts) if parts else "-"


class SubmissionWriter:
    """Escreve os JSONs por documento e o ``submission.csv``."""

    def __init__(self, output_directory: str | Path) -> None:
        self._output = Path(output_directory)

    def write(self, results: dict[str, list[ClassifiedCitation]]) -> Path:
        json_directory = self._output / "json"
        json_directory.mkdir(parents=True, exist_ok=True)

        for documento_id, items in sorted(results.items()):
            payload = {
                "documento_id": documento_id,
                "citacoes": [citation_to_contract(item) for item in items],
            }
            (json_directory / f"{documento_id}.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )

        submission = self._output / "submission.csv"
        with submission.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["documento_id", "citacoes"])
            for documento_id, items in sorted(results.items()):
                writer.writerow([documento_id, _encode_submission(items)])
        return submission
