"""Catálogo de expressões regulares para citações jurídicas."""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class CitationPattern:
    """Expressão regular usada para localizar uma família de citações."""

    name: str
    expression: re.Pattern[str]


class CitationPatternRegistry:
    """Constrói o conjunto de padrões utilizados pelo detector."""

    _FLAGS = re.IGNORECASE | re.VERBOSE
    _SPACE = r"[ \t\r\n]+"

    @classmethod
    def build(cls) -> tuple[CitationPattern, ...]:
        """Cria todos os padrões usados na extração."""
        structured_patterns = cls._build_structured_patterns()
        generic_patterns = cls._build_generic_patterns()

        return structured_patterns + generic_patterns

    @classmethod
    def _build_structured_patterns(
        cls,
    ) -> tuple[CitationPattern, ...]:
        """Cria padrões estruturados, incluindo variações de OCR."""
        whitespace = cls._SPACE

        # ============================================================
        # Padrões regulares para documentos com texto mais limpo
        # ============================================================

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

        # ============================================================
        # Padrões tolerantes a erros de OCR
        # ============================================================

        # Caracteres frequentemente confundidos pelo OCR:
        #
        # O ou o -> 0
        # I ou l -> 1
        # S      -> 5
        ocr_digit = r"[0-9OoIlS]"

        # Aceita espaços, pontos e traços entre os grupos numéricos.
        ocr_separator = r"[\s.\-–—]*"

        # O primeiro traço continua obrigatório para diminuir
        # falsos positivos.
        ocr_cnj_number = (
            rf"{ocr_digit}{{1,7}}"
            rf"\s*[-–—]\s*"
            rf"{ocr_digit}{{2}}"
            rf"{ocr_separator}"
            rf"{ocr_digit}{{4}}"
            rf"{ocr_separator}"
            rf"{ocr_digit}"
            rf"{ocr_separator}"
            rf"{ocr_digit}{{2}}"
            rf"{ocr_separator}"
            rf"{ocr_digit}{{4}}"
        )

        # Número comum com pontos, espaços ou quebras de linha.
        #
        # Exemplos:
        # 1.570.531
        # 1 570 531
        # 1. 570.531
        ocr_ordinary_number = (
            rf"{ocr_digit}{{1,7}}"
            rf"(?:[\s.]+{ocr_digit}{{1,3}})*"
        )

        ocr_class_atom = (
            r"(?:"
            r"Ag\.?\s*Int\.?|"
            r"AgInt|AGINT|"
            r"AgRg|"
            r"AgR(?:-AI|-REspe)?|"
            r"AgREsp|"
            r"EDcl|EDs?|"
            r"AREspEI|AREsp|ARESP|"
            r"REsp|RESP|"
            r"REspe|RESPE|"
            r"RHC|RMS|HC|"
            r"Rcl|RCL|Recl\.?|"
            r"APL|RSE|AR|RR|AI|"
            r"Rec\.?\s*Esp\.?|"
            r"R\.?\s*Esp\.?|"
            r"Recurso\s+Especial(?:\s+Eleitoral)?|"
            r"Recurso\s+em\s+Habeas\s+Corpus|"
            r"Reclama(?:ç|c)[aã]o|"
            r"Agravo\s+em\s+Recurso\s+Especial"
            r")"
        )

        # Permite cadeias como:
        #
        # EDcl no AgInt no REsp
        # AgInt nos EDcl no REsp
        # EDcl no Agravo em Recurso Especial
        ocr_process_class = (
            rf"{ocr_class_atom}"
            rf"(?:"
            rf"\s+(?:no|na|nos|nas)\s+"
            rf"{ocr_class_atom}"
            rf")*"
        )

        ocr_number_marker = (
            r"(?:"
            r"\s*"
            r"(?:n[.º°o]|n[uú]mero|Nº|No)"
            r")?"
        )

        ocr_court_suffix = (
            r"(?:"
            r"\s*(?:/|-|–|—)\s*[A-Z]{2,5}|"
            r"\s*\(\s*[A-Z]{2,5}\s*\)"
            r")?"
        )

        ocr_process_number = (
            rf"(?:"
            rf"{ocr_cnj_number}|"
            rf"{ocr_ordinary_number}"
            rf")"
            rf"{ocr_court_suffix}"
        )

        # ============================================================
        # Retorno dos padrões
        # ============================================================

        return (
            # --------------------------------------------------------
            # Padrões mais precisos
            # --------------------------------------------------------
            CitationPattern(
                name="processo",
                expression=re.compile(
                    rf"\b"
                    rf"{procedural_class}"
                    rf"{number_marker}"
                    rf"{process_number}"
                    rf"\b",
                    cls._FLAGS,
                ),
            ),
            CitationPattern(
                name="processo_trabalhista",
                expression=re.compile(
                    rf"\b{labor_process}\b",
                    cls._FLAGS,
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
                    cls._FLAGS,
                ),
            ),
            CitationPattern(
                name="dispositivo_legal",
                expression=re.compile(
                    article_reference,
                    cls._FLAGS,
                ),
            ),
            CitationPattern(
                name="numero_cnj",
                expression=re.compile(
                    rf"\b{cnj_number}{court_suffix}\b",
                    cls._FLAGS,
                ),
            ),
            # --------------------------------------------------------
            # Padrões tolerantes a OCR
            # --------------------------------------------------------
            CitationPattern(
                name="processo_ocr",
                expression=re.compile(
                    rf"\b"
                    rf"{ocr_process_class}"
                    rf"{ocr_number_marker}"
                    rf"\s+"
                    rf"{ocr_process_number}"
                    rf"\b",
                    cls._FLAGS,
                ),
            ),
            CitationPattern(
                name="numero_cnj_ocr",
                expression=re.compile(
                    rf"\b"
                    rf"{ocr_cnj_number}"
                    rf"{ocr_court_suffix}"
                    rf"\b",
                    cls._FLAGS,
                ),
            ),
        )

    @classmethod
    def _build_generic_patterns(
        cls,
    ) -> tuple[CitationPattern, ...]:
        """Cria padrões generalizados para citações incompletas."""
        space = cls._SPACE

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
            r"(?:"
            + space
            + r"em"
            + space
            + r"situa(?:ç|c)[oõ]es"
            + space
            + r"an[aá]logas"
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
            r"C[oó]digo"
            + space
            + r"de"
            + space
            + r"Processo"
            + space
            + r"(?:Civil|Penal)|"
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
                    cls._FLAGS,
                ),
            ),
            CitationPattern(
                name="referencia_legislativa_generica",
                expression=re.compile(
                    legal_reference_pattern,
                    cls._FLAGS,
                ),
            ),
            CitationPattern(
                name="entendimento_jurisprudencial_generico",
                expression=re.compile(
                    jurisprudence_pattern,
                    cls._FLAGS,
                ),
            ),
            CitationPattern(
                name="precedente_generico",
                expression=re.compile(
                    precedent_pattern,
                    cls._FLAGS,
                ),
            ),
            CitationPattern(
                name="enunciado_sumular_generico",
                expression=re.compile(
                    summary_statement_pattern,
                    cls._FLAGS,
                ),
            ),
            CitationPattern(
                name="artigo_generico",
                expression=re.compile(
                    generic_article_pattern,
                    cls._FLAGS,
                ),
            ),
        )
