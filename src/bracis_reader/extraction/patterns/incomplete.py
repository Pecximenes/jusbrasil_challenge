"""Padrões de citações sem identificador completo."""

import re

from bracis_reader.extraction.patterns.base import CitationPattern
from bracis_reader.extraction.patterns.jurisprudence import CLASS_EXPRESSION, COURT
from bracis_reader.extraction.patterns.legislation import LAW_NAME
from bracis_reader.extraction.patterns.lexicon import DECISION_NOUNS
from bracis_reader.extraction.patterns.text import (
    FLAGS,
    SPACE,
    YEAR,
    any_of,
    any_phrase,
    case_sensitive,
    fuzzy_word,
)


def _inflect(stem: str) -> list[str]:
    """ "pacífic" -> pacífico, pacífica, pacíficos, pacíficas."""
    return [stem + ending for ending in ("o", "a", "os", "as")]


def _words(*words: str) -> str:
    return any_of(fuzzy_word(word) for word in words)


_OF = _words("de", "do", "da", "dos", "das")
_OF_THIS = _words(
    "de", "do", "da", "dos", "das", "desta", "deste", "destes", "destas",
    "nesta", "neste", "no", "na", "nos", "nas",
)  # fmt: skip
_TO = _words("à", "ao", "a", "aos", "às")


_DECISION = any_of(
    [
        any_phrase(DECISION_NOUNS),
        any_phrase(("entendimento", "julgamento", "voto condutor", "voto")),
        CLASS_EXPRESSION,
    ]
)
_DECIDED = _words(
    "julgado", "julgada", "proferido", "proferida", "publicado", "publicada",
    "prolatado", "prolatada", "firmado", "firmada", "exarado", "exarada",
    "fixado", "fixada", "realizado", "realizada", "lavrado", "lavrada",
)  # fmt: skip
_BY_OR_OF = _words("do", "da", "dos", "das", "pelo", "pela", "no", "na")
_COURT_SPEC = rf"(?:{_DECIDED}{SPACE})?{_BY_OR_OF}{SPACE}{COURT}"
_YEAR_SPEC = (
    rf"(?:{_DECIDED}{SPACE})?{_words('em', 'de')}{SPACE}"
    rf"(?:{_words('ano')}{SPACE}{_words('de')}{SPACE})?{YEAR}\b"
)
_NAME_WORD = case_sensitive(r"[A-ZÀ-Ý][A-Za-zÀ-ÿ'’]+")
_NAME_LINK = case_sensitive(r"(?:de|da|do|dos|das|De|Da|Do|Dos|Das|DE|DA|DO|DOS|DAS|e)")
_NAME = rf"{_NAME_WORD}(?:{SPACE}(?:{_NAME_LINK}{SPACE})?{_NAME_WORD}){{0,5}}"
_MINISTER = any_of(
    [
        _words(
            "ministro",
            "ministra",
            "desembargador",
            "desembargadora",
            "juiz",
            "juíza",
        ),  # fmt: skip
        rf"{_words('min', 'des')}\.",
    ]
)
_HONORIFIC = (
    rf"(?:{_words('exmo', 'exma')}\.?{SPACE}(?:{_words('sr', 'sra')}\.?{SPACE})?)"
)
_TITLES = rf"(?:{SPACE}{_HONORIFIC})?(?:{SPACE}{_MINISTER}){{0,2}}"
_RAPPORTEUR = (
    rf"(?:"
    rf"(?:(?:{_words('pela', 'sob', 'da', 'de', 'com')}{SPACE}(?:a{SPACE})?)?"
    rf"{fuzzy_word('relatoria')}{SPACE}{_OF}"
    rf"|{_words('relatado', 'relatada')}{SPACE}{_words('pelo', 'pela')}"
    rf"|{_words('rel', 'relator', 'relatora')}\.?)"
    rf"{_TITLES}"
    rf"|{_words('do', 'da', 'pelo', 'pela')}(?:{SPACE}{_HONORIFIC})?"
    rf"(?:{SPACE}{_MINISTER}){{1,2}}"
    rf"){SPACE}{_NAME}"
)
_SEP = r"\s*,?\s*"
_DETAIL = rf"(?:{_COURT_SPEC}|{_YEAR_SPEC}|{_RAPPORTEUR})"

_TWO_DETAILS = (
    rf"(?:{_SEP}{_COURT_SPEC}{_SEP}(?:{_YEAR_SPEC}|{_RAPPORTEUR})"
    rf"|{_SEP}{_YEAR_SPEC}{_SEP}(?:{_RAPPORTEUR}|{_COURT_SPEC})"
    rf"|{_SEP}{_RAPPORTEUR}{_SEP}(?:{_YEAR_SPEC}|{_COURT_SPEC}))"
)
DESCRIPTIVE_DECISION = (
    rf"(?<!\d\s)(?<![\d.])\b(?:{fuzzy_word('recente')}{SPACE})?{_DECISION}"
    rf"{_TWO_DETAILS}(?:{_SEP}{_DETAIL}){{0,2}}"
)


_DOCTRINE_NOUN = any_phrase(
    (
        "jurisprudência", "entendimento", "entendimentos", "orientação",
        "orientações", "posicionamento", "precedentes", "julgados", "arestos",
        "tese", "súmula",
    )
)  # fmt: skip
_ANY_JURIS_NOUN = any_of(
    [
        _DOCTRINE_NOUN,
        any_phrase(("precedente", "acórdão", "julgado", "verbete", "enunciado")),
    ]
)
_JURIS_ADJECTIVE = any_of(
    fuzzy_word(word)
    for word in [
        *_inflect("pacífic"), *_inflect("consolidad"), *_inflect("reiterad"),
        *_inflect("sumulad"), *_inflect("firmad"), *_inflect("remansos"),
        *_inflect("iterativ"), *_inflect("majoritári"), *_inflect("uníson"),
        *_inflect("uniformizad"), *_inflect("assentad"), *_inflect("pacificad"),
        "dominante", "dominantes", "predominante", "sumular", "sumulares",
        "jurisprudencial", "jurisprudenciais", "assente", "vinculante",
        "vinculantes", "recente", "recentes", "notória", "notório", "firme",
        "firmes", "uniforme", "uniformes", *_inflect("sedimentad"),
        *_inflect("tranquil"), *_inflect("maciç"),
        "aplicável", "aplicáveis", "pertinente", "pertinentes",
    ]
)  # fmt: skip
_CASE_NOUN = _words(
    "espécie", "caso", "matéria", "controvérsia", "hipótese", "tema", "questão"
)
_BINDING_PROCEDURE = any_phrase(
    (
        "recurso repetitivo", "recursos repetitivos", "repercussão geral",
        "incidente de assunção de competência", "IRDR",
    )
)  # fmt: skip
_ANALOGOUS = any_phrase(
    (
        "situações análogas",
        "casos análogos",
        "casos semelhantes",
        "situações semelhantes",
    )
)
_JURIS_COMPLEMENT = any_of(
    [
        rf"{_OF_THIS}{SPACE}{COURT}",
        rf"{_words('sobre')}{SPACE}{_words('a', 'o')}{SPACE}{_CASE_NOUN}",
        rf"{_TO}{SPACE}{_CASE_NOUN}",
        rf"{_words('em')}{SPACE}{_words('sede')}{SPACE}{_OF}{SPACE}"
        rf"{_BINDING_PROCEDURE}",
        rf"{_words('em')}{SPACE}{_ANALOGOUS}",
    ]
)

GENERIC_JURISPRUDENCE = (
    rf"\b(?:"
    rf"{_JURIS_ADJECTIVE}{SPACE}{_ANY_JURIS_NOUN}"
    rf"(?:{SPACE}{_JURIS_ADJECTIVE}){{0,2}}(?:{SPACE}{_JURIS_COMPLEMENT}){{1,2}}"
    rf"|{_ANY_JURIS_NOUN}(?:{SPACE}{_JURIS_ADJECTIVE}){{1,2}}"
    rf"(?:{SPACE}{_JURIS_COMPLEMENT}){{1,2}}"
    rf"|{_DOCTRINE_NOUN}{SPACE}{_JURIS_COMPLEMENT}{SPACE}{_JURIS_COMPLEMENT}"
    rf")\b"
)


_LAW_NOUN = any_phrase(
    (
        "norma", "normas", "legislação", "dispositivo", "dispositivos",
        "preceito", "preceitos", "diploma", "lei", "artigo", "art.", "regra", "regras",
        "texto normativo", "comando normativo",
    )
)  # fmt: skip
_LAW_ADJECTIVE = any_of(
    fuzzy_word(word)
    for word in [
        "constitucional", "constitucionais", "legal", "legais",
        "infraconstitucional", "infraconstitucionais", "correspondente",
        "aplicável", "aplicáveis", "pertinente", "pertinentes", "regente",
        *_inflect("específic"), *_inflect("invocad"), *_inflect("violad"),
        *_inflect("mencionad"), *_inflect("apontad"),
    ]
)  # fmt: skip
_REGULATES = _words(
    "disciplina", "regula", "rege", "regulamenta", "estabelece", "dispõe", "trata"
)
_ARTICLE = _words("a", "o", "as", "os", "da", "do")
_LAW_COMPLEMENT = any_of(
    [
        rf"{_words('de')}{SPACE}{fuzzy_word('regência')}(?:{SPACE}{_OF}{SPACE}{_CASE_NOUN})?",
        rf"{_OF}{SPACE}{LAW_NAME}",
        rf"{_TO}{SPACE}{_CASE_NOUN}",
        rf"{_words('na', 'no', 'nos')}{SPACE}{_words('origem', 'autos', 'recurso')}",
        rf"{_words('que')}{SPACE}{_REGULATES}"
        rf"(?:{SPACE}{_words('sobre')})?(?:{SPACE}{_ARTICLE})?"
        rf"{SPACE}[a-zà-ÿ]{{4,}}"
        rf"(?:{SPACE}{_words('no', 'na')}{SPACE}{_CASE_NOUN})?",
    ]
)

GENERIC_LEGISLATION = (
    rf"\b{_LAW_NOUN}(?:{SPACE}{_LAW_ADJECTIVE}){{0,2}}{SPACE}{_LAW_COMPLEMENT}\b"
)


def build_incomplete_patterns() -> tuple[CitationPattern, ...]:
    """Cria os padrões de citações descritivas e genéricas."""
    return (
        CitationPattern(
            name="decisao_descritiva",
            expression=re.compile(DESCRIPTIVE_DECISION, FLAGS),
            tipo="jurisprudencia",
        ),
        CitationPattern(
            name="jurisprudencia_generica",
            expression=re.compile(GENERIC_JURISPRUDENCE, FLAGS),
            tipo="jurisprudencia",
        ),
        CitationPattern(
            name="legislacao_generica",
            expression=re.compile(GENERIC_LEGISLATION, FLAGS),
            tipo="lei",
        ),
    )
