"""Teste de robustez a ruído: mede se o detector generaliza além do gabarito."""

import random
import re
from collections.abc import Callable
from dataclasses import dataclass

from bracis_reader.domain.models import TextDocument
from bracis_reader.evaluation.evaluator import span_iou
from bracis_reader.evaluation.goldenset import GoldensetByDocument
from bracis_reader.extraction.detector import CitationDetector

Transform = Callable[[str, random.Random], str]

_UF = "AC|AL|AP|AM|BA|CE|DF|ES|GO|MA|MT|MS|MG|PA|PB|PR|PE|PI|RJ|RN|RS|RO|RR|SC|SP|SE|TO"

_ABBREVIATIONS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (r"\bREsp\b", ("R.Esp.", "Rec. Esp.", "Recurso Especial", "RESP")),
    (r"\bRecurso Especial\b", ("REsp", "Rec. Esp.", "R. Esp.")),
    (r"\bAREsp\b", ("Agravo em Recurso Especial", "ARESP", "A.REsp")),
    (r"\bAgInt\b", ("Ag. Int.", "AGINT", "Agravo Interno")),
    (r"\bAgRg\b", ("Ag. Rg.", "Agravo Regimental")),
    (r"\bEDcl\b", ("Embargos de Declaração", "ED")),
    (r"\bRHC\b", ("R.H.C.", "Recurso em Habeas Corpus")),
    (r"\bHC\b", ("H.C.", "Habeas Corpus")),
    (r"\bRMS\b", ("Recurso em Mandado de Segurança",)),
    (r"\bRcl\b", ("Reclamação", "Recl.", "RCL")),
    (r"\bReclamação\b", ("Rcl", "Recl.")),
    (r"\bSúmula\b", ("Súm.", "SÚMULA", "Enunciado")),
    (r"\bart\.", ("artigo", "art", "Art.")),
    (r"\bartigo\b", ("art.",)),
)

_NUMBER_MARKERS = ("nº", "n.", "n°", "No", "Nº", "número")


def _replace_one(pattern: str, text: str, rng: random.Random, repl) -> str:
    matches = list(re.finditer(pattern, text))
    if not matches:
        return text
    match = rng.choice(matches)
    replacement = repl(match) if callable(repl) else repl
    return text[: match.start()] + replacement + text[match.end() :]


def vary_abbreviation(text: str, rng: random.Random) -> str:
    options = [(p, alts) for p, alts in _ABBREVIATIONS if re.search(p, text)]
    if not options:
        return text
    pattern, alternatives = rng.choice(options)
    return _replace_one(pattern, text, rng, rng.choice(alternatives))


def vary_number_marker(text: str, rng: random.Random) -> str:
    return _replace_one(
        r"\b(?:n[º°]|N[º°o]|n\.)(?=\s)", text, rng, rng.choice(_NUMBER_MARKERS)
    )


def vary_number_format(text: str, rng: random.Random) -> str:
    """1.741.784 -> 1741784 | 1 741 784 | 1.741. 784"""

    def reformat(match: re.Match[str]) -> str:
        groups = match.group(0).split(".")
        style = rng.choice(("sem_ponto", "espacos", "ponto_espaco"))
        if style == "sem_ponto":
            return "".join(groups)
        if style == "espacos":
            return " ".join(groups)
        position = rng.randrange(1, len(groups))
        return ".".join(groups[:position]) + ". " + ".".join(groups[position:])

    return _replace_one(r"\b\d{1,3}(?:\.\d{3})+\b", text, rng, reformat)


def vary_uf_separator(text: str, rng: random.Random) -> str:
    def reformat(match: re.Match[str]) -> str:
        uf = match.group("uf")
        return rng.choice((f"/{uf}", f" - {uf}", f" ({uf})", f"-{uf}", f"/ {uf}"))

    pattern = rf"(?:\s*[/\-–]\s*|\s*\(\s*)(?P<uf>{_UF})\)?$"
    return _replace_one(pattern, text, rng, reformat)


def vary_ocr(text: str, rng: random.Random) -> str:
    """Confusões do regulamento: 0↔O, 1↔l, 5↔S, m↔rn (nunca dígito↔dígito)."""
    swaps = {"0": "O", "1": "l", "5": "S", "m": "rn"}
    positions = [i for i, char in enumerate(text) if char in swaps]
    if not positions:
        return text
    i = rng.choice(positions)
    return text[:i] + swaps[text[i]] + text[i + 1 :]


def vary_line_break(text: str, rng: random.Random) -> str:
    return _replace_one(r" (?=\S)", text, rng, "\n")


def vary_case(text: str, rng: random.Random) -> str:
    return _replace_one(r"\b[A-Za-zÀ-ÿ]{3,}\b", text, rng, lambda m: m.group(0).upper())


TRANSFORMS: tuple[Transform, ...] = (
    vary_abbreviation,
    vary_number_marker,
    vary_number_format,
    vary_uf_separator,
    vary_ocr,
    vary_line_break,
    vary_case,
)


@dataclass(frozen=True)
class RobustnessResult:
    """Resultado agregado do teste de robustez."""

    variants: int
    detected: int

    @property
    def recall(self) -> float:
        return self.detected / self.variants if self.variants else 0.0


class NoiseRobustnessEvaluator:
    """Gera variantes ruidosas das citações do gabarito e mede o recall."""

    def __init__(
        self,
        detector: CitationDetector | None = None,
        variants_per_citation: int = 5,
        max_transforms: int = 3,
        iou_threshold: float = 0.5,
        seed: int = 2026,
    ) -> None:
        self._detector = detector or CitationDetector()
        self._variants = variants_per_citation
        self._max_transforms = max_transforms
        self._iou_threshold = iou_threshold
        self._seed = seed

    def evaluate(
        self,
        documents: list[TextDocument],
        expected_by_document: GoldensetByDocument,
    ) -> RobustnessResult:
        rng = random.Random(self._seed)
        total = detected = 0

        for document in documents:
            gold = sorted(expected_by_document.get(document.documento_id, set()))
            for start, end, snippet in gold:
                if document.texto[start:end] != snippet:
                    continue
                for _ in range(self._variants):
                    variant = self._make_variant(snippet, rng)
                    if variant == snippet:
                        continue
                    total += 1
                    detected += self._is_detected(document, start, end, variant)

        return RobustnessResult(variants=total, detected=detected)

    def _make_variant(self, snippet: str, rng: random.Random) -> str:
        variant = snippet
        for transform in rng.sample(TRANSFORMS, rng.randint(1, self._max_transforms)):
            variant = transform(variant, rng)
        return variant

    def _is_detected(
        self, document: TextDocument, start: int, end: int, variant: str
    ) -> bool:
        text = document.texto[:start] + variant + document.texto[end:]
        noisy = TextDocument(documento_id=document.documento_id, texto=text)
        target = (start, start + len(variant))
        return any(
            span_iou((c.inicio, c.fim), target) >= self._iou_threshold
            for c in self._detector.detect(noisy)
        )
