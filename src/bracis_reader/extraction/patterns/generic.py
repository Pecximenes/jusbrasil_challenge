"""Padrões genéricos para referências jurídicas incompletas."""

import re

from bracis_reader.extraction.patterns.base import FLAGS, SPACE, CitationPattern


def build_generic_patterns() -> tuple[CitationPattern, ...]:
    """Cria padrões generalizados para citações incompletas."""
    space = SPACE

    legal_norm_pattern = (
        r"\b"
        r"(?:"
        r"normas?|"
        r"legisla(?:ç|c)[aã]o|"
        r"dispositivo|"
        r"preceito|"
        r"diploma"
        r")" + space + r"(?:"
        r"(?:"
        r"constitucional|"
        r"legal|"
        r"infraconstitucional"
        r")"
        r"(?:" + space + r"(?:invocado|aplic[aá]vel)"
        r"(?:" + space + r"(?:na|no|à|ao)" + space + r"(?:origem|caso|esp[eé]cie)"
        r")?"
        r")?|"
        r"de" + space + r"reg[eê]ncia"
        r"(?:"
        + space
        + r"(?:da|do|desta|deste)"
        + space
        + r"(?:mat[eé]ria|caso|controv[eé]rsia)"
        r")?"
        r")"
        r"\b"
    )

    legal_reference_pattern = (
        r"\b"
        r"(?:lei|norma|legisla(?:ç|c)[aã]o)" + space + r"(?:"
        r"que|"
        r"a" + space + r"qual"
        r")" + space + r"(?:"
        r"disciplina|"
        r"regula|"
        r"rege|"
        r"estabelece|"
        r"disp[oõ]e"
        r")" + space + r"(?:sobre" + space + r")?" + r"(?:"
        r"(?:a|o|as|os)" + space + r")?" + r"(?:"
        r"prescri(?:ç|c)[aã]o|"
        r"procedimento|"
        r"compet[eê]ncia|"
        r"mat[eé]ria|"
        r"prazo|"
        r"recurso"
        r")"
        r"(?:" + space + r"(?:no|na)" + space + r"(?:caso|esp[eé]cie|hip[oó]tese)"
        r")?"
        r"\b"
    )

    jurisprudence_pattern = (
        r"\b"
        r"(?:"
        r"jurisprud[eê]ncia|"
        r"entendimento|"
        r"orienta(?:ç|c)[aã]o|"
        r"posicionamento"
        r")" + space + r"(?:"
        r"pac[ií]fic[ao]|"
        r"consolidad[ao]|"
        r"dominante|"
        r"reiterad[ao]|"
        r"jurisprudencial|"
        r"sumulad[ao]"
        r")"
        r"(?:" + space + r"(?:desta|deste|da|do|dos|das)" + space + r"(?:"
        r"Corte(?:" + space + r"Superior)?|"
        r"Tribunal(?:" + space + r"Superior)?|"
        r"Casa|"
        r"STF|STJ|TST|TSE|STM"
        r")"
        r")?"
        r"\b"
    )

    precedent_pattern = (
        r"\b"
        r"precedentes?"
        r"(?:" + space + r"reiterados?"
        r")?" + space + r"(?:desta|deste|da|do|dos|das)" + space + r"(?:"
        r"Corte|"
        r"Tribunal|"
        r"Casa|"
        r"STF|STJ|TST|TSE|STM|"
        r"Superior" + space + r"Tribunal" + space + r"de" + space + r"Justi(?:ç|c)a"
        r")"
        r"(?:" + space + r"em" + space + r"situa(?:ç|c)[oõ]es" + space + r"an[aá]logas"
        r")?"
        r"\b"
    )

    summary_statement_pattern = (
        r"\b"
        r"(?:"
        r"verbete|"
        r"enunciado|"
        r"entendimento|"
        r"orienta(?:ç|c)[aã]o"
        r")" + space + r"(?:sumular|jurisprudencial)"
        r"(?:"
        + space
        + r"(?:aplic[aá]vel|pertinente|relativo)"
        + space
        + r"(?:à|ao|[aà])"
        + space
        + r"(?:"
        r"esp[eé]cie|"
        r"caso|"
        r"mat[eé]ria|"
        r"controv[eé]rsia"
        r")"
        r")?"
        r"\b"
    )

    generic_article_pattern = (
        r"\b"
        r"artigo" + space + r"(?:correspondente|aplic[aá]vel|pertinente)"
        r"(?:" + space + r"(?:d[ao])"
        r")?" + space + r"(?:"
        r"C[oó]digo" + space + r"de" + space + r"Processo" + space + r"(?:Civil|Penal)|"
        r"C[oó]digo" + space + r"(?:Civil|Penal|Eleitoral)|"
        r"Constitui(?:ç|c)[aã]o" + space + r"Federal"
        r")"
        r"\b"
    )

    return (
        CitationPattern(
            name="referencia_normativa_generica",
            expression=re.compile(
                legal_norm_pattern,
                FLAGS,
            ),
        ),
        CitationPattern(
            name="referencia_legislativa_generica",
            expression=re.compile(
                legal_reference_pattern,
                FLAGS,
            ),
        ),
        CitationPattern(
            name="entendimento_jurisprudencial_generico",
            expression=re.compile(
                jurisprudence_pattern,
                FLAGS,
            ),
        ),
        CitationPattern(
            name="precedente_generico",
            expression=re.compile(
                precedent_pattern,
                FLAGS,
            ),
        ),
        CitationPattern(
            name="enunciado_sumular_generico",
            expression=re.compile(
                summary_statement_pattern,
                FLAGS,
            ),
        ),
        CitationPattern(
            name="artigo_generico",
            expression=re.compile(
                generic_article_pattern,
                FLAGS,
            ),
        ),
    )
