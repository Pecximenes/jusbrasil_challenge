"""Normalização de identificadores antes da consulta à base.

O regulamento garante que o ruído do nível 2 é sempre recuperável: um dígito
nunca vira outro dígito, só letras parecidas. Então basta mapear essas letras
de volta e descartar a pontuação.
"""

import re
import unicodedata

# Letra que o OCR confunde com dígito -> dígito original.
OCR_TO_DIGIT = {
    "O": "0", "o": "0", "D": "0", "Q": "0",
    "I": "1", "l": "1", "i": "1", "|": "1",
    "Z": "2", "z": "2",
    "S": "5", "s": "5",
    "G": "6", "b": "6",
    "T": "7",
    "B": "8",
    "g": "9", "q": "9",
}  # fmt: skip

# Tamanho da parte fixa de um número CNJ: DD + AAAA + J + TR + OOOO.
_CNJ_TAIL = 13


def to_digits(number: str) -> str:
    """ "1.45g.779" -> "1459779"; "7000171-3920237000000" -> só os dígitos."""
    mapped = "".join(OCR_TO_DIGIT.get(char, char) for char in number)
    return re.sub(r"\D", "", mapped)


def looks_like_cnj(digits: str) -> bool:
    """Número CNJ: termina em DD AAAA J TR OOOO, com ano plausível."""
    if len(digits) < _CNJ_TAIL + 1 or len(digits) > 20:
        return False
    year = int(digits[-11:-7])
    return 1980 <= year <= 2035


def number_key(number: str) -> str | None:
    """Chave canônica de um número de processo, independente da formatação.

    - CNJ: sequencial sem zeros à esquerda + 13 dígitos finais
      ("0600216-46.2020.6.14.0022" e "600216-46.2020.6.14.0022" coincidem);
    - demais: o número sem zeros à esquerda.
    """
    digits = to_digits(number).lstrip("0")
    if not digits:
        return "0" if to_digits(number) else None
    if looks_like_cnj(digits):
        return f"{digits[:-_CNJ_TAIL]}-{digits[-_CNJ_TAIL:]}"
    return digits


def cnj_justice_segment(key: str) -> str | None:
    """Dígito J do CNJ (5 = Trabalho, 6 = Eleitoral, 7 = Militar...)."""
    if "-" not in key:
        return None
    return key.split("-")[1][6]


def strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def normalize_name(name: str) -> str:
    """Nome de pessoa comparável: sem acento, minúsculo, espaços simples.

    Também desfaz confusões de OCR comuns em nomes ("rn" -> "m").
    """
    text = strip_accents(name).lower()
    text = re.sub(r"\b(min|ministro|ministra|des|desembargador|rel)\b\.?", " ", text)
    text = re.sub(r"[^a-z ]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


# Estados por extenso (cabeçalhos do STF e do TSE) -> sigla.
STATE_NAMES = {
    "ACRE": "AC", "ALAGOAS": "AL", "AMAPA": "AP", "AMAZONAS": "AM",
    "BAHIA": "BA", "CEARA": "CE", "DISTRITO FEDERAL": "DF",
    "ESPIRITO SANTO": "ES", "GOIAS": "GO", "MARANHAO": "MA",
    "MATO GROSSO DO SUL": "MS", "MATO GROSSO": "MT", "MINAS GERAIS": "MG",
    "PARANA": "PR", "PARAIBA": "PB", "PARA": "PA", "PERNAMBUCO": "PE",
    "PIAUI": "PI", "RIO DE JANEIRO": "RJ", "RIO GRANDE DO NORTE": "RN",
    "RIO GRANDE DO SUL": "RS", "RONDONIA": "RO", "RORAIMA": "RR",
    "SANTA CATARINA": "SC", "SAO PAULO": "SP", "SERGIPE": "SE",
    "TOCANTINS": "TO",
}  # fmt: skip
