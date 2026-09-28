"""Leitura das anotações de referência do goldenset."""

import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

CitationKey = tuple[int, int, str]
GoldensetByDocument = dict[str, set[CitationKey]]


class GoldensetLoader:
    """Carrega os spans esperados e os agrupa por documento."""

    def load(self, csv_path: str | Path) -> GoldensetByDocument:
        """Lê o CSV preservando quebras de linha registradas nos trechos."""
        expected: dict[str, set[CitationKey]] = defaultdict(set)

        with Path(csv_path).open(
            mode="r",
            encoding="utf-8-sig",
            newline="",
        ) as csv_file:
            for row in csv.DictReader(csv_file):
                expected[row["documento_id"]].add(
                    (
                        int(row["inicio"]),
                        int(row["fim"]),
                        row["trecho"].replace("\\n", "\n"),
                    )
                )

        return dict(expected)


@dataclass(frozen=True)
class GoldCitation:
    """Uma linha completa do goldenset."""

    documento_id: str
    nivel: int
    inicio: int
    fim: int
    trecho: str
    tipo: str
    classificacao: str
    ids_aceitos: frozenset[int]


def load_annotations(csv_path: str | Path) -> dict[str, list[GoldCitation]]:
    """Lê todas as colunas do goldenset, agrupadas por documento."""
    annotations: dict[str, list[GoldCitation]] = defaultdict(list)
    with Path(csv_path).open(mode="r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            annotations[row["documento_id"]].append(
                GoldCitation(
                    documento_id=row["documento_id"],
                    nivel=int(row["nivel"]),
                    inicio=int(row["inicio"]),
                    fim=int(row["fim"]),
                    trecho=row["trecho"].replace("\\n", "\n"),
                    tipo=row["tipo"],
                    classificacao=row["classificacao"],
                    ids_aceitos=frozenset(
                        int(value) for value in (row.get("id_canonico") or "").split()
                    ),
                )
            )
    return dict(annotations)
