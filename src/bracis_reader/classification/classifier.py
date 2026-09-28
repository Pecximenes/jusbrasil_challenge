"""Classificação de cada citação em real, inventada ou incompleta.

Regra do regulamento, aplicada à base canônica:

    feitos encontrados   classe       saída
    exatamente 1         real         id_canonico de qualquer registro do feito
    0                    inventada    sem resolução
    2 ou mais            incompleta   sem resolução (não há como desempatar)

Citações sem identificador suficiente para montar a consulta ("jurisprudência
pacífica desta Corte") são incompletas sem passar pela base.

O caminho de cada citação depende do padrão que a encontrou:

- processo / número CNJ  -> número normalizado no índice de feitos
- súmula                 -> catálogo de súmulas (tribunal + número)
- dispositivo legal      -> catálogo de dispositivos (lei + artigo)
- tema / OJ              -> não existem na base: inventada
- decisão descritiva     -> contagem por tribunal, ano e relator
- genéricas              -> incompleta
"""

import re
from dataclasses import dataclass

from bracis_reader.classification.canonical_base import (
    CanonicalBase,
    Feito,
    extract_numbers,
    extract_uf,
    raw_numbers,
)
from bracis_reader.classification.catalog import (
    DISPOSITIVOS,
    LAW_PATTERNS,
    SUMULAS,
)
from bracis_reader.classification.normalization import (
    cnj_justice_segment,
    strip_accents,
    to_digits,
)
from bracis_reader.domain.models import CitationCandidate, ClassifiedCitation

_COURTS = ("STF", "STJ", "TST", "TSE", "STM")
_COURT_NAMES = {
    "supremo tribunal federal": "STF",
    "superior tribunal de justica": "STJ",
    "tribunal superior do trabalho": "TST",
    "tribunal superior eleitoral": "TSE",
    "superior tribunal militar": "STM",
}
_CNJ_SEGMENT_COURT = {"5": "TST", "6": "TSE", "7": "STM"}

# Pistas de tribunal pela classe, usadas só para desempatar.
_CLASS_COURT_HINTS: tuple[tuple[str, str], ...] = (
    (r"eleitoral|respe|\bagr-", "TSE"),
    (r"\btst\b|\b(?:ai)?rr\b|\barr\b|revista", "TST"),
    (r"\bapl\b|\brse\b|apela|sentido estrito", "STM"),
    (r"\bresp\b|\baresp\b|especial|\brhc\b|\brms\b|\bagrg\b|\bedcl\b", "STJ"),
    (r"\bre\b|\bare\b|extraordin|\badi\b|\badpf\b|\badc\b", "STF"),
)

# Marcadores de recurso sobre recurso. "AgInt no REsp 1" e "REsp 1" são o
# mesmo feito, mas registros diferentes; o marcador escolhe o registro.
_APPEAL_MARKERS = {
    "agravo": (
        r"\bag(?:int|rg|r|reg)?\b|\bag\.\s?(?:int|reg|rg)"
        r"|agravo (?:interno|regimental)"
    ),
    "declaracao": r"\bed(?:cl|s)?\b|embargos de declara",
    "embargos": r"\be-|\bembargos(?! de declara)|\beresp\b",
}


def _appeal_markers(text: str) -> set[str]:
    plain = _plain(text)
    return {
        name for name, pattern in _APPEAL_MARKERS.items() if re.search(pattern, plain)
    }


_YEAR = re.compile(r"\b(?:19|2[0O])[0-9OoIlSs]{2}\b")
_RAPPORTEUR = re.compile(
    r"(?:relatoria\s+d\w{0,2}|relatad[oa]\s+pel[oa]|\brel(?:ator|atora)?\.?)"
    r"(?:\s+(?:exm[oa]\.?\s+)?(?:(?:sr|sra)\.?\s+)?(?:ministr[oa]|min\.|des\.))?"
    r"\s+(?P<nome>.+)$",
    re.IGNORECASE | re.DOTALL,
)
# Número começa por dígito real, ou por letra-dígito seguida de dígito ("l86").
_NUM = r"(?:[0-9]|[OoIlSs](?=[0-9]))[0-9OoIlSs.]*"
_ARTICLE_NUMBER = re.compile(rf"art(?:igo)?s?\.?\s*({_NUM})", re.I)
_SUMULA_NUMBER = re.compile(
    rf"(?:mula|m\.|enunciado|\bSV\b)\D{{0,20}}?\b({_NUM})", re.I
)


@dataclass(frozen=True)
class _Resolution:
    classificacao: str
    id_canonico: int | None
    confianca: float
    motivo: str


def _plain(text: str) -> str:
    return re.sub(r"\s+", " ", strip_accents(text).lower())


def _court_mentioned(text: str) -> str | None:
    for court in _COURTS:
        if re.search(rf"\b{court}\b", text):
            return court
    plain = _plain(text)
    for name, court in _COURT_NAMES.items():
        if name in plain:
            return court
    return None


class CitationClassifier:
    """Decide a classe de cada citação consultando a base canônica."""

    def __init__(self, base: CanonicalBase) -> None:
        self._base = base
        self._sumulas = self._resolve_catalog_sumulas()
        self._dispositivos = self._resolve_catalog_dispositivos()

    # ------------------------------------------------------------- catálogo

    def _record_starting_with(self, natureza: str, prefix: str) -> int:
        wanted = _plain(prefix)
        for record in self._base.records:
            if record.natureza != natureza:
                continue
            body = record.texto.split("\n", 1)[-1] if natureza == "sumula" else ""
            if _plain(record.texto).startswith(wanted) or _plain(body).startswith(
                wanted
            ):
                return record.id
        raise LookupError(f"Registro {natureza!r} não encontrado: {prefix!r}")

    def _resolve_catalog_sumulas(self) -> dict[tuple[str, int, bool], int]:
        return {
            (
                entry.tribunal,
                entry.numero,
                entry.vinculante,
            ): self._record_starting_with("sumula", entry.inicio_do_texto)
            for entry in SUMULAS
        }

    def _resolve_catalog_dispositivos(self) -> dict[tuple[str, int], int]:
        return {
            (entry.lei, entry.artigo): self._record_starting_with(
                "dispositivo", entry.inicio_do_texto
            )
            for entry in DISPOSITIVOS
        }

    # -------------------------------------------------------------- público

    def classify(self, citation: CitationCandidate) -> ClassifiedCitation:
        """Classifica uma citação encontrada pelo detector."""
        resolver = {
            "processo": self._by_process_number,
            "numero_cnj": self._by_process_number,
            "sumula": self._by_sumula,
            "dispositivo_legal": self._by_dispositivo,
            "tema": self._not_in_base,
            "orientacao_jurisprudencial": self._not_in_base,
            "decisao_descritiva": self._by_description,
        }.get(citation.padrao or "", self._generic)
        resolution = resolver(citation.trecho)
        return ClassifiedCitation(
            citacao=citation,
            classificacao=resolution.classificacao,
            id_canonico=resolution.id_canonico,
            confianca=resolution.confianca,
            motivo=resolution.motivo,
        )

    def classify_many(
        self, citations: list[CitationCandidate]
    ) -> list[ClassifiedCitation]:
        return [self.classify(citation) for citation in citations]

    # ------------------------------------------------------------- caminhos

    def _by_process_number(self, trecho: str) -> _Resolution:
        keys = extract_numbers(trecho)
        if not keys:
            return _Resolution("incompleta", None, 0.5, "sem número utilizável")

        feitos = {
            (feito.tribunal, feito.numero): feito
            for key in keys
            for feito in self._base.find_feitos(key)
        }
        candidates = list(feitos.values())
        ocr_used = any(
            char.isalpha() for number in raw_numbers(trecho) for char in number
        )

        if not candidates:
            confidence = 0.85 if ocr_used else 0.9
            return _Resolution("inventada", None, confidence, "número fora da base")

        if len(candidates) > 1:
            candidates = self._break_tie(trecho, keys, candidates)

        if len(candidates) == 1:
            feito = candidates[0]
            uf = extract_uf(trecho)
            confidence = 0.95
            if uf and feito.ufs and uf not in feito.ufs:
                confidence = 0.6  # número existe, mas a UF citada diverge
            return _Resolution(
                "real",
                self._best_record(trecho, feito),
                confidence,
                f"feito {feito.tribunal}",
            )

        return _Resolution(
            "incompleta", None, 0.6, f"{len(candidates)} feitos com o mesmo número"
        )

    @staticmethod
    def _best_record(trecho: str, feito: Feito) -> int:
        """Registro do feito cuja classe mais se parece com a citada."""
        cited = _appeal_markers(re.split(r"\d", trecho, maxsplit=1)[0])

        def distance(record_id: int) -> tuple[int, int]:
            heading = feito.headings.get(record_id, "")
            heading = re.split(r"\d", heading, maxsplit=1)[0]
            return (len(cited ^ _appeal_markers(heading)), record_id)

        return min(feito.ids, key=distance)

    def _break_tie(
        self, trecho: str, keys: list[str], candidates: list[Feito]
    ) -> list[Feito]:
        court = _court_mentioned(trecho)
        if court is None:
            for key in keys:
                court = _CNJ_SEGMENT_COURT.get(cnj_justice_segment(key) or "")
                if court:
                    break
        if court is None:
            plain = _plain(trecho)
            court = next(
                (c for pattern, c in _CLASS_COURT_HINTS if re.search(pattern, plain)),
                None,
            )
        uf = extract_uf(trecho)
        narrowed = [f for f in candidates if court is None or f.tribunal == court]
        if uf and len(narrowed) > 1:
            by_uf = [f for f in narrowed if uf in f.ufs]
            narrowed = by_uf or narrowed
        return narrowed or candidates

    def _by_sumula(self, trecho: str) -> _Resolution:
        match = _SUMULA_NUMBER.search(trecho)
        if not match:
            return _Resolution("incompleta", None, 0.6, "súmula sem número")
        numero = int(to_digits(match.group(1)) or 0)
        vinculante = bool(re.search(r"vinculante|\bsv\b", _plain(trecho)))
        court = _court_mentioned(trecho) or ("STF" if vinculante else None)

        found = [
            record_id
            for (tribunal, number, binding), record_id in self._sumulas.items()
            if number == numero
            and binding == vinculante
            and (court is None or tribunal == court)
        ]
        if len(found) == 1:
            return _Resolution("real", found[0], 0.95, "súmula do catálogo")
        if not found:
            return _Resolution("inventada", None, 0.9, "súmula fora da base")
        return _Resolution("incompleta", None, 0.6, "súmula sem tribunal definido")

    def _by_dispositivo(self, trecho: str) -> _Resolution:
        match = _ARTICLE_NUMBER.search(trecho)
        if not match:
            return _Resolution("incompleta", None, 0.6, "artigo sem número")
        artigo = int(to_digits(match.group(1)) or 0)
        law_text = _plain(trecho[match.end() :])
        lei = next(
            (law for law, pattern in LAW_PATTERNS if re.search(pattern, law_text)),
            None,
        )
        if lei is None:
            return _Resolution("inventada", None, 0.85, "diploma fora da base")
        record_id = self._dispositivos.get((lei, artigo))
        if record_id is None:
            return _Resolution("inventada", None, 0.9, f"art. {artigo} do {lei} fora")
        return _Resolution("real", record_id, 0.95, f"art. {artigo} do {lei}")

    def _by_description(self, trecho: str) -> _Resolution:
        year_match = _YEAR.search(trecho)
        ano = int(to_digits(year_match.group(0))) if year_match else None
        rapporteur = _RAPPORTEUR.search(trecho)
        relator = rapporteur.group("nome") if rapporteur else None
        court = _court_mentioned(trecho)

        feitos = self._base.count_described(court, ano, relator)
        if len(feitos) == 1:
            feito = feitos[0]
            return _Resolution("real", min(feito.ids), 0.6, "descrição única na base")
        if not feitos:
            # Pode ser nome com ruído que não casou; o regulamento chamaria de
            # inventada, mas a leitura da descrição é incerta demais.
            return _Resolution("incompleta", None, 0.5, "descrição sem correspondência")
        return _Resolution("incompleta", None, 0.9, f"{len(feitos)} feitos possíveis")

    @staticmethod
    def _not_in_base(trecho: str) -> _Resolution:
        return _Resolution("inventada", None, 0.8, "tipo de precedente fora da base")

    @staticmethod
    def _generic(trecho: str) -> _Resolution:
        return _Resolution("incompleta", None, 0.9, "sem identificador")
