"""Blocos de construção para regex tolerantes a ruído de OCR e formatação."""

import re
import unicodedata

FLAGS = re.IGNORECASE | re.UNICODE

SPACE = r"\s+"
OPTIONAL_SPACE = r"\s*"

_LETTER_VARIANTS: dict[str, str] = {
    "a": "aáàâãä",
    "c": "cçe",
    "e": "eéêèëc",
    "i": "iíìîïl1",
    "l": "l1iI|",
    "n": "nñ",
    "o": "oóòôõö0",
    "s": "s5",
    "u": "uúùûü",
}


def _strip_accent(char: str) -> str:
    decomposed = unicodedata.normalize("NFD", char)
    return decomposed[0] if decomposed else char


def fuzzy_word(word: str) -> str:
    """Compila uma palavra em regex tolerante a acentos e a OCR."""
    parts: list[str] = []
    i = 0
    lowered = word.lower()
    while i < len(lowered):
        char = lowered[i]
        if lowered.startswith("rn", i):
            parts.append("(?:rn|m)")
            i += 2
            continue
        if char == "m":
            parts.append("(?:m|rn)")
        elif char.isalpha():
            base = _strip_accent(char)
            variants = _LETTER_VARIANTS.get(base, base)
            if char not in variants:
                variants += char
            parts.append(f"[{re.escape(variants)}]")
        elif char == ".":
            parts.append(r"\.")
        elif char == " ":
            parts.append(SPACE)
        else:
            parts.append(re.escape(char))
        i += 1
    return "".join(parts)


def fuzzy_phrase(phrase: str) -> str:
    """Compila uma expressão de várias palavras separadas por qualquer espaço."""
    return SPACE.join(fuzzy_word(word) for word in phrase.split())


def any_of(options) -> str:
    """Alternância não capturante, com as opções mais longas primeiro."""
    ordered = sorted(set(options), key=len, reverse=True)
    return "(?:" + "|".join(ordered) + ")"


def any_phrase(phrases) -> str:
    """Alternância de expressões compiladas com :func:`fuzzy_phrase`."""
    return any_of(fuzzy_phrase(phrase) for phrase in phrases)


def case_sensitive(expression: str) -> str:
    """Desliga o IGNORECASE só dentro de ``expression``."""
    return f"(?-i:{expression})"


OCR_DIGIT_LETTERS = "OoDQIl|iZzSsGbTBgq"
_DIGIT = rf"[0-9{re.escape(OCR_DIGIT_LETTERS)}]"

_GROUP = (
    rf"(?:[0-9]|(?<![^\W\d_])[{re.escape(OCR_DIGIT_LETTERS)}](?=[.\s\-]{{0,2}}[0-9]))"
    rf"{_DIGIT}*"
)

_SEPARATOR = r"[\s.\-–—]{1,4}"

PROCESS_NUMBER = rf"{_GROUP}(?:{_SEPARATOR}{_GROUP}){{0,8}}"

_CNJ_SEP = r"[\s.\-–—]{0,3}"
CNJ_NUMBER = (
    rf"{_DIGIT}{{7}}{_CNJ_SEP}{_DIGIT}{{2}}{_CNJ_SEP}{_DIGIT}{{4}}"
    rf"{_CNJ_SEP}{_DIGIT}{_CNJ_SEP}{_DIGIT}{{2}}{_CNJ_SEP}{_DIGIT}{{4}}"
)

_OCR_ORDINAL = rf"(?<![^\W\d_])[{re.escape(OCR_DIGIT_LETTERS)}](?=\s?[º°])"

SHORT_NUMBER = rf"(?:{_GROUP}(?:\.\s?{_DIGIT}{{3}})?|{_OCR_ORDINAL})"

NUMBER_MARKER = (
    r"(?:n\.?\s?[º°o]\.?|n\.|"
    + fuzzy_word("número")
    + "|"
    + case_sensitive(r"N[º°o]?\.?|No\.?")
    + ")"
)

YEAR = rf"(?:19|2[0O]){_DIGIT}{{2}}"

SMALL_NUMBER = rf"(?:{_GROUP}|{_OCR_ORDINAL})"
