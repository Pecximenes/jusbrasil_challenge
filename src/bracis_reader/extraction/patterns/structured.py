"""Padrões estruturados para documentos com texto limpo.

Processos, números CNJ, súmulas e dispositivos legais.
"""

import re

from bracis_reader.extraction.patterns.base import FLAGS, SPACE, CitationPattern


def build_structured_patterns() -> tuple[CitationPattern, ...]:
    """Cria os padrões estruturados mais precisos."""
    whitespace = SPACE

    process_class = (
        r"(?:"
        r"AgInt|AgRg|AgREsp|AREspEI|AREsp|REsp|RHC|RMS|HC|"
        r"RE|RSE|Rcl|RCL|Recl\.?|APL|AR|REspe|AGR-RESPE|"
        r"AIRR|ARR|RR|RO|AI|MS|ADI|ADPF|R-Rp|"
        r"Reclama(?:ç|c)[aã]o|"
        r"Recurso"
        + whitespace
        + r"em"
        + whitespace
        + r"Habeas"
        + whitespace
        + r"Corpus|"
        r"Recurso" + whitespace + r"Especial(?:" + whitespace + r"Eleitoral)?|"
        r"Agravo"
        + whitespace
        + r"em"
        + whitespace
        + r"Recurso"
        + whitespace
        + r"Especial"
        r")"
    )

    procedural_class = (
        rf"{process_class}"
        rf"(?:"
        rf"{whitespace}"
        rf"(?:no|na|nos|nas)"
        rf"{whitespace}"
        rf"{process_class}"
        rf")*"
    )

    number_marker = (
        rf"(?:"
        rf"{whitespace}"
        rf"(?:n[.º°o]|n[uú]mero|Nº|No)"
        rf")?"
        rf"{whitespace}"
    )

    cnj_number = (
        r"\d{1,7}-\d{2}\.\d{4}\.\d"
        r"(?:\.\d{2})?\.\d{4}"
    )

    ordinary_number = r"\d{1,7}(?:\.\d{3})*"

    court_suffix = (
        r"(?:"
        r"\s*(?:/|-|–|—)\s*[A-Z]{2,5}|"
        r"\s*\([A-Z]{2,5}\)"
        r")?"
    )

    process_number = (
        rf"(?:{cnj_number}|{ordinary_number})"
        rf"{court_suffix}"
    )

    labor_process = (
        r"(?:"
        r"processo\s+"
        r"(?:n[.º°o]|n[uú]mero)\s*"
        r")?"
        r"(?:TST-)?"
        r"(?:[A-Z]{1,6}-){1,6}"
        r"\d{1,7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}"
    )

    article_reference = (
        r"\bart(?:igo)?\.?" + whitespace + r"\d+(?:\.\d+)?(?:º|°)?" + rf"(?:"
        rf"\s*,\s*"
        rf"(?:"
        rf"§(?:{whitespace})?\d+(?:º|°)?(?:-[A-Z])?|"
        r"[IVXLCDM]+|"
        r"['\u2018\u2019][a-z]['\u2018\u2019]"
        rf")"
        rf")*" + rf"\s*,?{whitespace}"
        rf"(?:d[ao]|das|dos){whitespace}" + r"(?:"
        r"Lei(?:" + whitespace + r"Complementar)?" + rf"(?:"
        rf"{whitespace}"
        rf"(?:n[.º°o]|n[uú]mero|Nº|No)"
        rf")?"
        rf"{whitespace}" + r"\d+(?:\.\d+)*(?:/\d{4})?|"
        r"C[oó]digo" + whitespace + r"(?:"
        r"Civil|Eleitoral|"
        r"Penal(?:" + whitespace + r"Militar)?|"
        r"de"
        + whitespace
        + r"Defesa"
        + whitespace
        + r"do"
        + whitespace
        + r"Consumidor|"
        r"de" + whitespace + r"Processo" + whitespace + r"(?:Civil|Penal)"
        r")|"
        r"Constitui(?:ç|c)[aã]o(?:" + whitespace + r"(?:"
        r"Federal|"
        r"da" + whitespace + r"Rep[uú]blica|"
        r"Fedcral"
        r")"
        r")?|"
        r"Consolida(?:ç|c)[aã]o"
        + whitespace
        + r"das"
        + whitespace
        + r"Leis"
        + whitespace
        + r"do"
        + whitespace
        + r"Trabalho|"
        r"CPC|CPP|CPM|CLT|CDC"
        r")"
    )

    return (
        CitationPattern(
            name="processo",
            expression=re.compile(
                rf"\b"
                rf"{procedural_class}"
                rf"{number_marker}"
                rf"{process_number}"
                rf"\b",
                FLAGS,
            ),
        ),
        CitationPattern(
            name="processo_trabalhista",
            expression=re.compile(
                rf"\b{labor_process}\b",
                FLAGS,
            ),
        ),
        CitationPattern(
            name="sumula",
            expression=re.compile(
                r"\b"
                r"(?:S[uú]mula|S[uú]m\.|5[uú]mula)"
                rf"(?:{whitespace}Vinculante)?"
                rf"(?:"
                rf"{whitespace}"
                rf"(?:n[.º°o]|n[uú]mero)"
                rf")?"
                rf"{whitespace}\d+"
                rf"(?:"
                rf"{whitespace}d[ao]"
                rf"{whitespace}[A-Z]{{2,5}}"
                rf")?"
                r"\b",
                FLAGS,
            ),
        ),
        CitationPattern(
            name="dispositivo_legal",
            expression=re.compile(
                article_reference,
                FLAGS,
            ),
        ),
        CitationPattern(
            name="numero_cnj",
            expression=re.compile(
                rf"\b{cnj_number}{court_suffix}\b",
                FLAGS,
            ),
        ),
    )
