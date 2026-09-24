"""Padrões estruturados tolerantes a erros de OCR."""

import re

from bracis_reader.extraction.patterns.base import FLAGS, CitationPattern


def build_ocr_patterns() -> tuple[CitationPattern, ...]:
    """Cria padrões de processos e números CNJ com ruídos de OCR."""
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

    return (
        CitationPattern(
            name="processo_ocr",
            expression=re.compile(
                rf"\b"
                rf"{ocr_process_class}"
                rf"{ocr_number_marker}"
                rf"\s+"
                rf"{ocr_process_number}"
                rf"\b",
                FLAGS,
            ),
        ),
        CitationPattern(
            name="numero_cnj_ocr",
            expression=re.compile(
                rf"\b"
                rf"{ocr_cnj_number}"
                rf"{ocr_court_suffix}"
                rf"\b",
                FLAGS,
            ),
        ),
    )
