"""Blocos de construção para regex tolerantes a ruído de OCR e formatação.

Em vez de escrever cada variante à mão ("Súmula", "5úmula", "SÚMULA",
"Sumula"...), as palavras são compiladas a partir de uma tabela geral de
confusões de OCR. Assim, qualquer palavra nova do vocabulário ganha a mesma
tolerância automaticamente.
"""

import re
import unicodedata

FLAGS = re.IGNORECASE | re.UNICODE

# Qualquer espaço, inclusive quebra de linha e espaço não separável (\xa0).
SPACE = r"\s+"
OPTIONAL_SPACE = r"\s*"

# Confusões típicas de OCR entre letras. Acentos são sempre opcionais.
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
    """Compila uma palavra em regex tolerante a acentos e a OCR.

    - acentos opcionais ("jurisprudência" casa "jurisprudencia");
    - trocas de caractere comuns (c↔e, l↔1, o↔0, s↔5...);
    - "m" casa "rn" e vice-versa.
    """
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


# ----------------------------------------------------------------------------
# Números
# ----------------------------------------------------------------------------

# Letras que o OCR confunde com dígitos. O regulamento garante que um dígito
# nunca é trocado por outro dígito; só por letras parecidas.
OCR_DIGIT_LETTERS = "OoDQIl|iZzSsGbTBgq"
_DIGIT = rf"[0-9{re.escape(OCR_DIGIT_LETTERS)}]"

# Um grupo começa com dígito real, ou com letra-dígito seguida de dígito real
# ("l.996", "O600216"). Isso impede que siglas como "SC" ou "TO" sejam lidas
# como números.
# A letra-dígito inicial não pode vir colada a outra letra: em "Rcl 36.670" ou
# "No 7001184", o "l" e o "o" são o fim de uma palavra, não um dígito.
_GROUP = (
    rf"(?:[0-9]|(?<![^\W\d_])[{re.escape(OCR_DIGIT_LETTERS)}](?=[.\s]?[0-9]))"
    rf"{_DIGIT}*"
)

# Separadores aceitos entre grupos: ponto, hífen, travessão, espaço, quebra
# de linha e combinações curtas deles ("33.-\n474", "7220273--\n23").
_SEPARATOR = r"[\s.\-–—]{1,4}"

# Número de processo em qualquer formatação: 1.741.784 | 1741784 |
# 1 741 784 | 1.741. 784 | 0600216-46.2020.6.14.0022 | 7000171-3920237000000
PROCESS_NUMBER = rf"{_GROUP}(?:{_SEPARATOR}{_GROUP}){{0,8}}"

# Número CNJ (NNNNNNN-DD.AAAA.J.TR.OOOO), com qualquer separador ou nenhum.
_CNJ_SEP = r"[\s.\-–—]{0,3}"
CNJ_NUMBER = (
    rf"{_DIGIT}{{7}}{_CNJ_SEP}{_DIGIT}{{2}}{_CNJ_SEP}{_DIGIT}{{4}}"
    rf"{_CNJ_SEP}{_DIGIT}{_CNJ_SEP}{_DIGIT}{{2}}{_CNJ_SEP}{_DIGIT}{{4}}"
)

# Número curto (súmulas, temas, artigos): 83 | 1.022 | 2.680
SHORT_NUMBER = rf"{_GROUP}(?:\.\s?{_DIGIT}{{3}})?"

# "nº", "n°", "n.", "No", "Nº", "n.º", "número"
NUMBER_MARKER = (
    r"(?:n\.?\s?[º°o]\.?|n\.|"
    + fuzzy_word("número")
    + "|"
    + case_sensitive(r"N[º°o]?\.?|No\.?")
    + ")"
)

# Ano com tolerância a OCR ("2O24", "202l").
YEAR = rf"(?:19|2[0O]){_DIGIT}{{2}}"

# Dígitos simples com tolerância a OCR ("§ lº").
SMALL_NUMBER = _GROUP
