"""Acesso à base canônica ``desafio1_bracis.db`` e índices para consulta."""

import re
import sqlite3
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from bracis_reader.classification.normalization import (
    STATE_NAMES,
    normalize_name,
    number_key,
    strip_accents,
)
from bracis_reader.extraction.patterns.jurisprudence import (
    CNJ_REFERENCE,
    PROCESS,
    UF_SUFFIX,
)
from bracis_reader.extraction.patterns.text import FLAGS, PROCESS_NUMBER

_PROCESS = re.compile(PROCESS, FLAGS)
_CNJ = re.compile(CNJ_REFERENCE, FLAGS)
_NUMBER = re.compile(PROCESS_NUMBER, FLAGS)
_UF = re.compile(UF_SUFFIX + r"\s*$", FLAGS)
_LOOSE_CNJ = re.compile(r"\d{1,7}\s?[-–]\s?\d{2}\.\s?\d{4}\.\s?\d\.\s?\d{2}\.\s?\d{4}")
_JUDGED_CASE = re.compile(
    r"(?:vistos|relatados)[^.]{0,60}?autos\s+d[eo]s?\s+"
    r"(?P<objeto>.{0,300}?)(?:,|\s+em\s+que\b)",
    re.IGNORECASE | re.DOTALL,
)

HEADER_WINDOW = 400
JUDGED_CASE_WINDOW = 500


@dataclass(frozen=True)
class Record:
    """Um registro da base."""

    id: int
    documento_id: str
    tribunal: str | None
    ano: int | None
    relator: str | None
    natureza: str
    tipo: str
    texto: str


@dataclass
class Feito:
    """Um processo da base, com todos os seus registros."""

    tribunal: str
    numero: str
    ufs: set[str] = field(default_factory=set)
    ids: set[int] = field(default_factory=set)
    headings: dict[int, str] = field(default_factory=dict)


def _first_number_match(text: str) -> re.Match[str] | None:
    """Primeira citação numerada do texto, em qualquer dos formatos."""
    matches = [
        match
        for pattern in (_PROCESS, _CNJ, _LOOSE_CNJ)
        if (match := pattern.search(text))
    ]
    return min(matches, key=lambda match: match.start()) if matches else None


def raw_numbers(snippet: str) -> list[str]:
    """Os números como aparecem no texto, antes da normalização."""
    return [match.group(0) for match in _NUMBER.finditer(snippet)]


def extract_numbers(snippet: str) -> list[str]:
    """Chaves de número presentes em um trecho que já é uma citação."""
    keys = []
    for match in _NUMBER.finditer(snippet):
        key = number_key(match.group(0))
        if key and len(key.replace("-", "")) >= 2:
            keys.append(key)
    return keys


def extract_uf(snippet: str) -> str | None:
    """UF no final de uma citação ("/SP", "- SP", "(SP)")."""
    match = _UF.search(snippet)
    if not match:
        return None
    return re.sub(r"[^A-Z]", "", match.group(0).upper())[-2:]


def _header_uf(header: str) -> str | None:
    uf = None
    for match in _PROCESS.finditer(header):
        uf = uf or extract_uf(match.group(0))
    if uf:
        return uf
    plain = re.sub(r"\s+", " ", strip_accents(header).upper())
    plain = re.sub(r"\b([A-Z]) (?=[A-Z]\b)", r"\1", plain)
    for name, code in sorted(STATE_NAMES.items(), key=lambda item: -len(item[0])):
        if re.search(rf"\b{name}\b", plain):
            return code
    return None


class CanonicalBase:
    """Base canônica carregada em memória, com índices de consulta."""

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = Path(db_path)
        if not self._db_path.is_file():
            raise FileNotFoundError(f"Base canônica não encontrada: {db_path}")
        self.records = self._load_records()
        self.by_id = {record.id: record for record in self.records}
        self.feitos = self._index_feitos()
        self._by_number: dict[str, list[Feito]] = defaultdict(list)
        for feito in self.feitos.values():
            self._by_number[feito.numero].append(feito)

    def _load_records(self) -> list[Record]:
        with sqlite3.connect(self._db_path) as connection:
            rows = connection.execute(
                "SELECT id, documento_id, tribunal, ano, relator, natureza, tipo, "
                "texto FROM documentos"
            ).fetchall()
        return [Record(*row) for row in rows]

    def _index_feitos(self) -> dict[tuple[str, str], Feito]:
        feitos: dict[tuple[str, str], Feito] = {}
        for record in self.records:
            if record.natureza != "acordao" or not record.tribunal:
                continue
            numbers, uf, heading = self.own_numbers(record.texto)
            for numero in numbers:
                key = (record.tribunal, numero)
                feito = feitos.setdefault(key, Feito(record.tribunal, numero))
                feito.ids.add(record.id)
                feito.headings[record.id] = heading
                if uf:
                    feito.ufs.add(uf)
        return feitos

    @staticmethod
    def own_numbers(texto: str) -> tuple[list[str], str | None, str]:
        """Números do próprio processo (não os que ele apenas cita)."""
        header = texto[:HEADER_WINDOW]
        snippets: list[str] = []

        judged = _JUDGED_CASE.search(texto)
        if judged:
            first = _first_number_match(judged.group("objeto"))
            if first:
                snippets.append(first.group(0))

        if not snippets:
            first = _first_number_match(header)
            if first:
                snippets.append(first.group(0))
                following = header[first.end() : first.end() + 60]
                extra = _CNJ.search(following) or _LOOSE_CNJ.search(following)
                if extra:
                    snippets.append(extra.group(0))

        numbers: list[str] = []
        for snippet in snippets:
            for key in extract_numbers(snippet):
                if key not in numbers:
                    numbers.append(key)
        return numbers, _header_uf(header), " ".join(snippets)

    def find_feitos(
        self,
        numero: str,
        tribunal: str | None = None,
    ) -> list[Feito]:
        """Feitos com esse número (opcionalmente só de um tribunal)."""
        found = self._by_number.get(numero, [])
        if tribunal:
            found = [feito for feito in found if feito.tribunal == tribunal]
        return found

    def count_described(
        self,
        tribunal: str | None,
        ano: int | None,
        relator: str | None,
    ) -> list[Feito]:
        """Feitos que casam com tribunal, ano e relator de uma citação descritiva."""
        wanted_name = normalize_name(relator) if relator else None
        matches: dict[tuple[str, str], Feito] = {}
        for feito in self.feitos.values():
            if tribunal and feito.tribunal != tribunal:
                continue
            records = [self.by_id[i] for i in feito.ids]
            if ano and not any(r.ano == ano for r in records):
                continue
            if wanted_name and not any(
                r.relator and _same_person(wanted_name, normalize_name(r.relator))
                for r in records
            ):
                continue
            matches[(feito.tribunal, feito.numero)] = feito
        return list(matches.values())


def _similar_word(a: str, b: str) -> bool:
    """Igual, ou uma letra de diferença em palavras longas (ruído de OCR)."""
    if a == b:
        return True
    if min(len(a), len(b)) < 5 or abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b, strict=True)) <= 1
    shorter, longer = sorted((a, b), key=len)
    return any(longer[:i] + longer[i + 1 :] == shorter for i in range(len(longer)))


def _same_person(cited: str, registered: str) -> bool:
    """Todas as palavras citadas precisam estar no nome registrado."""
    cited_words = [w for w in cited.split() if len(w) > 2]
    registered_words = registered.split()
    return bool(cited_words) and all(
        any(_similar_word(word, other) for other in registered_words)
        for word in cited_words
    )
