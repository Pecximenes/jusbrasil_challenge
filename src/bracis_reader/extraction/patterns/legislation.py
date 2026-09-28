"""Padrões de dispositivos legais identificados.

    art./artigo NÚMERO [, § 1º | , I | , 'a' | , parágrafo único]... da|do LEI

"LEI" pode ser uma lei numerada, um código, a Constituição, a CLT, um
estatuto ou a sigla de um diploma (CPC, CLT, CF/88...).
"""

import re

from bracis_reader.extraction.patterns.base import CitationPattern
from bracis_reader.extraction.patterns.lexicon import LAW_ACRONYMS
from bracis_reader.extraction.patterns.text import (
    FLAGS,
    NUMBER_MARKER,
    OPTIONAL_SPACE,
    SHORT_NUMBER,
    SMALL_NUMBER,
    SPACE,
    any_of,
    any_phrase,
    case_sensitive,
    fuzzy_phrase,
    fuzzy_word,
)

# Palavra com inicial maiúscula ou toda em maiúsculas ("Civil", "CIVIL").
_CAPITALIZED = case_sensitive(r"(?:[A-ZÀ-Ý][a-zà-ÿ]+|[A-ZÀ-Ý]{2,})")
_OF = any_of(fuzzy_word(w) for w in ("de", "do", "da", "dos", "das"))

_ARTICLE_WORD = any_of([fuzzy_word("artigo") + "s?", fuzzy_word("art") + r"s?\.?"])
_ORDINAL_SIGN = r"(?:\s?[º°o](?![a-z]))?"
_ARTICLE_NUMBER = rf"{SHORT_NUMBER}{_ORDINAL_SIGN}(?:\s?-\s?[A-Z]\b)?"

_ROMAN = case_sensitive(r"[IVXLCDM]{1,7}\b")
_MODIFIER = any_of(
    [
        rf"§{{1,2}}{OPTIONAL_SPACE}{SMALL_NUMBER}{_ORDINAL_SIGN}(?:\s?-\s?[A-Z]\b)?",
        fuzzy_phrase("parágrafo único"),
        fuzzy_word("caput"),
        rf"{fuzzy_word('inciso')}{SPACE}{_ROMAN}",
        rf"{fuzzy_word('inc')}\.{OPTIONAL_SPACE}{_ROMAN}",
        rf"{fuzzy_word('alínea')}{SPACE}['\"‘’]?[a-z]['\"‘’]?",
        r"['\"‘’][a-z]['\"‘’]",
        case_sensitive(r"[a-z]\)"),
        _ROMAN,
    ]
)
_MODIFIERS = rf"(?:{OPTIONAL_SPACE},?{OPTIONAL_SPACE}{_MODIFIER})*"

_NUMBERED_LAW = (
    rf"(?:(?:{fuzzy_word('lei')}|{case_sensitive('LC')})"
    rf"(?:{SPACE}{any_phrase(('complementar', 'ordinária', 'federal', 'estadual'))})?"
    rf"|{fuzzy_word('decreto')}(?:-{fuzzy_word('lei')})?"
    rf"|{fuzzy_phrase('medida provisória')})"
    rf"(?:{OPTIONAL_SPACE}{NUMBER_MARKER})?{OPTIONAL_SPACE}"
    rf"\d{{1,2}}(?:\.?\s?\d{{3}})*"
    rf"(?:{OPTIONAL_SPACE}/{OPTIONAL_SPACE}\d{{2,4}}|,{SPACE}{fuzzy_word('de')}{SPACE}\d{{4}})?"
)
_CODE = (
    rf"{fuzzy_word('código')}"
    rf"(?:{SPACE}(?:{_OF}{SPACE})?{_CAPITALIZED}){{1,4}}"
)
_CONSTITUTION = any_of(
    [
        rf"{fuzzy_word('constituição')}"
        rf"(?:{SPACE}(?:{fuzzy_word('da')}{SPACE})?{_CAPITALIZED}){{0,2}}"
        rf"(?:{SPACE}{fuzzy_word('de')}{SPACE}(?:19)?88)?",
        any_phrase(
            ("Carta Magna", "Carta da República", "Carta Política", "Lei Maior")
        ),
    ]
)
_CLT = fuzzy_phrase("Consolidação das Leis do Trabalho")
_STATUTE = (
    rf"{fuzzy_word('estatuto')}{SPACE}{_OF}{SPACE}{_CAPITALIZED}"
    rf"(?:{SPACE}(?:(?:{_OF}|e){SPACE})?{_CAPITALIZED}){{0,3}}"
)
_ACRONYM = case_sensitive(any_of(re.escape(a) for a in LAW_ACRONYMS)) + r"(?![\w/])"

LAW_NAME = any_of([_NUMBERED_LAW, _CODE, _CONSTITUTION, _CLT, _STATUTE, _ACRONYM])

ARTICLE = (
    rf"\b{_ARTICLE_WORD}{OPTIONAL_SPACE}{_ARTICLE_NUMBER}"
    rf"{_MODIFIERS}"
    rf"{OPTIONAL_SPACE},?{SPACE}"
    rf"(?:{_OF}|{any_of(fuzzy_word(w) for w in ('desta', 'deste', 'dessa', 'desse'))})"
    rf"{SPACE}{LAW_NAME}"
)


def build_legislation_patterns() -> tuple[CitationPattern, ...]:
    """Cria o padrão de dispositivo legal."""
    return (
        CitationPattern(
            name="dispositivo_legal",
            expression=re.compile(ARTICLE, FLAGS),
            tipo="lei",
        ),
    )
