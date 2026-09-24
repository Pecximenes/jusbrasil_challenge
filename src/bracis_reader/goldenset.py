"""Leitura das anotações de referência do goldenset."""

import csv
from collections import defaultdict
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
