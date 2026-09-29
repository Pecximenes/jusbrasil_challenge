"""Padrões de jurisprudência identificada: processos, súmulas, temas e OJs."""

import re

from bracis_reader.extraction.patterns.base import CitationPattern
from bracis_reader.extraction.patterns.lexicon import (
    CLASS_ACRONYMS,
    CLASS_NAMES,
    COURT_ACRONYMS,
    COURT_NAMES,
    UFS,
)
from bracis_reader.extraction.patterns.text import (
    CNJ_NUMBER,
    FLAGS,
    NUMBER_MARKER,
    OPTIONAL_SPACE,
    PROCESS_NUMBER,
    SHORT_NUMBER,
    SPACE,
    any_of,
    any_phrase,
    case_sensitive,
    fuzzy_phrase,
    fuzzy_word,
)

_PREPOSITIONS = {"de", "do", "da", "dos", "das", "em", "e", "no", "na"}

_CHAIN_ONLY = {"E", "Ag", "R"}


def _abbreviated_word(word: str) -> str:
    """ "Recurso" -> Recurso | Rec. | Recu. | Re."""
    options = [fuzzy_word(word)]
    if word.lower() not in _PREPOSITIONS and len(word) >= 4:
        options += [fuzzy_word(word[:size]) + r"\." for size in range(2, 5)]
    return any_of(options)


def _class_name(name: str) -> str:
    """Nome por extenso com cada palavra podendo vir abreviada."""
    return SPACE.join(_abbreviated_word(word) for word in name.split())


def _acronym(acronym: str) -> str:
    """ "REsp" -> R.Esp. | R. Esp | REsp | RESP ... (pontos e espaços opcionais)."""

    def compile_segments(text: str) -> str:
        segments = re.findall(r"[A-Z][a-z]*|[a-z]+|\d+|-", text)
        joined = r"\.?\s?".join(
            r"\s*-\s*" if segment == "-" else re.escape(segment) for segment in segments
        )
        return joined + r"\.?"

    if len(acronym.replace("-", "")) <= 2:
        variants = {compile_segments(acronym), compile_segments(acronym.upper())}
        return case_sensitive(any_of(variants))
    return compile_segments(acronym)


_ACRONYM_PREFIX = any_of(
    _acronym(p) for p in ("Ag", "AgR", "AgRg", "AgInt", "E", "ED", "EDcl", "A")
)
_BASES = any_of(_acronym(a) for a in CLASS_ACRONYMS if a not in _CHAIN_ONLY)
_ACRONYM_MAIN = rf"(?:{_ACRONYM_PREFIX}(?=[A-Z]))?{_BASES}"
_ACRONYM_ANY = any_of([_ACRONYM_MAIN] + [_acronym(a) for a in _CHAIN_ONLY])
_FULL_NAME = any_of(_class_name(name) for name in CLASS_NAMES)

_QUALIFIER = any_phrase(("eleitoral", "criminal", "cível", "trabalhista", "militar"))

_HYPHEN = r"\s*-\s*"
_CLASS_UNIT = (
    rf"(?:{_FULL_NAME}"
    rf"|(?:{_ACRONYM_ANY}{_HYPHEN})+{_ACRONYM_ANY}"
    rf"|{_ACRONYM_MAIN}(?:{SPACE}{_QUALIFIER})?)"
)
_CONNECTOR = (
    SPACE + any_of(fuzzy_word(w) for w in ("no", "na", "nos", "nas", "em")) + SPACE
)
_ORDINAL = any_phrase(("primeiro", "segundo", "terceiro", "quarto", "quinto", "sexto"))

CLASS_EXPRESSION = (
    rf"(?:{_ORDINAL}{SPACE})?{_CLASS_UNIT}(?:{_CONNECTOR}{_CLASS_UNIT}){{0,5}}"
)

_UF = case_sensitive(any_of(UFS))
UF_SUFFIX = rf"(?:\s*[/\-–—]\s*{_UF}\b|\s*\(\s*{_UF}\s*\))"

COURT = any_of([case_sensitive(any_of(COURT_ACRONYMS)), any_phrase(COURT_NAMES)])

_MARKER = rf"(?:{NUMBER_MARKER}{OPTIONAL_SPACE})"
_PROCESS_PREFIX = rf"(?:{fuzzy_word('processo')}{SPACE}{_MARKER}?)"
_TST_PREFIX = rf"(?:TST{_HYPHEN})"
_CLASS_TO_NUMBER = rf"(?:{_HYPHEN}|{OPTIONAL_SPACE}{_MARKER}|{SPACE})"

PROCESS = (
    rf"\b{_PROCESS_PREFIX}?{_TST_PREFIX}?"
    rf"{CLASS_EXPRESSION}"
    rf"{_CLASS_TO_NUMBER}"
    rf"{PROCESS_NUMBER}"
    rf"{UF_SUFFIX}?"
)

CNJ_REFERENCE = rf"(?<![\w.\-]){_PROCESS_PREFIX}?{CNJ_NUMBER}{UF_SUFFIX}?(?![\w])"

_SUMULA_WORD = any_of(
    [
        fuzzy_word("súmula"),
        fuzzy_word("súm") + r"\.",
        fuzzy_word("enunciado"),
        case_sensitive("SV"),
    ]
)
SUMULA = (
    rf"\b{_SUMULA_WORD}(?:{SPACE}{fuzzy_word('vinculante')})?"
    rf"(?:{OPTIONAL_SPACE}{NUMBER_MARKER})?{OPTIONAL_SPACE}{SHORT_NUMBER}\b"
    rf"(?:{OPTIONAL_SPACE}[/\-,]?{OPTIONAL_SPACE}"
    rf"(?:{any_of(fuzzy_word(w) for w in ('do', 'da'))}{SPACE})?{COURT})?"
)

_OF_COURT = (
    rf"(?:{any_of(fuzzy_word(w) for w in ('do', 'da', 'deste', 'desta'))}{SPACE})"
)
SUMULA_REVERSED = (
    rf"\b{any_of(fuzzy_word(w) for w in ('verbete', 'enunciado'))}"
    rf"(?:{OPTIONAL_SPACE}{NUMBER_MARKER})?{OPTIONAL_SPACE}{SHORT_NUMBER}"
    rf"{SPACE}{any_of(fuzzy_word(w) for w in ('da', 'de'))}"
    rf"{SPACE}{fuzzy_word('súmula')}"
    rf"(?:{SPACE}{fuzzy_word('vinculante')})?"
    rf"(?:{SPACE}{_OF_COURT}?{COURT})?"
)

_TEMA_SCOPE = any_phrase(
    ("repercussão geral", "recursos repetitivos", "recurso repetitivo")
)
TEMA = (
    rf"\b{fuzzy_word('tema')}(?:{OPTIONAL_SPACE}{NUMBER_MARKER})?{OPTIONAL_SPACE}"
    rf"{SHORT_NUMBER}\b"
    rf"(?:{SPACE}{any_of(fuzzy_word(w) for w in ('da', 'do', 'dos'))}"
    rf"{SPACE}(?:{_TEMA_SCOPE}|{COURT}))?"
)

ORIENTACAO_JURISPRUDENCIAL = (
    rf"\b(?:{fuzzy_phrase('orientação jurisprudencial')}|{case_sensitive('OJ')})"
    rf"(?:{OPTIONAL_SPACE}{NUMBER_MARKER})?{OPTIONAL_SPACE}\d{{1,4}}\b"
    rf"(?:{SPACE}{any_of(fuzzy_word(w) for w in ('da', 'do'))}{SPACE}{COURT})?"
)


def build_jurisprudence_patterns() -> tuple[CitationPattern, ...]:
    """Cria os padrões de jurisprudência com identificador."""

    def pattern(name: str, expression: str) -> CitationPattern:
        return CitationPattern(
            name=name,
            expression=re.compile(expression, FLAGS),
            tipo="jurisprudencia",
        )

    return (
        pattern("processo", PROCESS),
        pattern("sumula", SUMULA),
        pattern("sumula", SUMULA_REVERSED),
        pattern("tema", TEMA),
        pattern("orientacao_jurisprudencial", ORIENTACAO_JURISPRUDENCIAL),
        pattern("numero_cnj", CNJ_REFERENCE),
    )
