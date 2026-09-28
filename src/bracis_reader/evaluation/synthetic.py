"""Teste da classificação com citações montadas a partir da própria base.

O gabarito tem só 82 citações reais. Para saber se a classificação
generaliza, este módulo sorteia processos, súmulas, artigos e relatores da
base canônica, escreve citações novas com eles (em formatos e ruídos
variados), insere cada uma numa frase e confere a classe devolvida:

- processo existente, qualquer formatação/ruído       -> real, com id do feito
- mesmo processo com um dígito trocado (não existe)   -> inventada
- súmula ou artigo do catálogo, em várias grafias     -> real
- número de súmula ou lei trocados                    -> inventada
- decisão descrita por tribunal, ano e relator        -> incompleta (ou real,
  se a descrição for única na base)

Nada disso depende do goldenset.
"""

import random
from dataclasses import dataclass, field

from bracis_reader.classification.canonical_base import CanonicalBase, Feito
from bracis_reader.classification.catalog import DISPOSITIVOS, SUMULAS
from bracis_reader.classification.classifier import CitationClassifier
from bracis_reader.domain.models import ClassifiedCitation, TextDocument
from bracis_reader.evaluation.robustness import (
    vary_case,
    vary_line_break,
    vary_ocr,
    vary_uf_separator,
)
from bracis_reader.extraction.detector import CitationDetector

_CLASSES_BY_COURT = {
    "STJ": ("REsp", "AgInt no REsp", "AREsp", "Recurso Especial", "HC", "RHC"),
    "STF": ("Rcl", "AgR na Rcl", "RE", "ARE", "HC"),
    "TST": ("RR", "AIRR", "Ag-AIRR", "E-RR"),
    "TSE": ("REspe", "AgR-REspe", "RO"),
    "STM": ("APL", "RSE", "Apelação Criminal"),
}
_LAW_FORMS = {
    "CPC": ("do CPC", "do Código de Processo Civil", "da Lei 13.105/2015"),
    "CC": ("do Código Civil", "do CC"),
    "CLT": ("da CLT", "da Consolidação das Leis do Trabalho"),
    "CF": ("da CF", "da Constituição Federal", "da CF/88"),
    "CPP": ("do CPP", "do Código de Processo Penal"),
    "CPM": ("do CPM", "do Código Penal Militar"),
    "CDC": ("do CDC", "do Código de Defesa do Consumidor", "da Lei 8.078/90"),
    "CE": ("do Código Eleitoral",),
    "LC64": ("da Lei Complementar nº 64/1990", "da LC 64/90"),
}
_DESCRIPTIONS = (
    "julgado do {t} proferido em {a} pela relatoria de {n}",
    "precedente do {t} de {a}, da relatoria de {n}",
    "acórdão do {t} julgado em {a} sob relatoria de {n}",
)


@dataclass
class SyntheticResult:
    """Acertos por grupo de citações sintéticas."""

    groups: dict[str, list[int]] = field(default_factory=dict)

    def add(self, group: str, correct: bool) -> None:
        hits, total = self.groups.setdefault(group, [0, 0])
        self.groups[group] = [hits + correct, total + 1]


class SyntheticCitationEvaluator:
    """Gera citações a partir da base e mede a classificação."""

    def __init__(
        self,
        base: CanonicalBase,
        classifier: CitationClassifier | None = None,
        detector: CitationDetector | None = None,
        sample_size: int = 300,
        seed: int = 42,
    ) -> None:
        self._base = base
        self._classifier = classifier or CitationClassifier(base)
        self._detector = detector or CitationDetector()
        self._sample_size = sample_size
        self._rng = random.Random(seed)

    def evaluate(self) -> SyntheticResult:
        result = SyntheticResult()
        feitos = list(self._base.feitos.values())
        self._rng.shuffle(feitos)
        sample = feitos[: self._sample_size]

        for feito in sample:
            self._check_real(feito, result, noisy=False)
            self._check_real(feito, result, noisy=True)
            self._check_invented(feito, result)
        self._check_catalog(result)
        self._check_descriptions(result)
        return result

    # ----------------------------------------------------------- auxiliares

    def _classify(self, sentence: str) -> list[ClassifiedCitation]:
        document = TextDocument(documento_id="sintetico", texto="CAB\n\n\n" + sentence)
        return self._classifier.classify_many(self._detector.detect(document))

    def _format_number(self, key: str) -> str:
        rng = self._rng
        if "-" in key:
            seq, tail = key.split("-")
            dd, yyyy, j, tr, oooo = tail[:2], tail[2:6], tail[6], tail[7:9], tail[9:]
            return rng.choice(
                (
                    f"{seq}-{dd}.{yyyy}.{j}.{tr}.{oooo}",
                    f"{seq.zfill(7)}-{dd}.{yyyy}.{j}.{tr}.{oooo}",
                    f"{seq.zfill(7)}-{dd}{yyyy}{j}{tr}{oooo}",
                )
            )
        dotted = f"{int(key):,}".replace(",", ".")
        return rng.choice((dotted, str(int(key)), dotted.replace(".", " ")))

    def _citation(self, feito: Feito, number: str) -> str:
        rng = self._rng
        classe = rng.choice(_CLASSES_BY_COURT[feito.tribunal])
        separator = (
            "-" if feito.tribunal == "TST" else rng.choice((" nº ", " n. ", " "))
        )
        text = f"{classe}{separator}{number}"
        uf = next(iter(sorted(feito.ufs)), None)
        if uf:
            text += rng.choice((f"/{uf}", f" - {uf}", f" ({uf})"))
        return text

    def _check_real(self, feito: Feito, result: SyntheticResult, noisy: bool) -> None:
        text = self._citation(feito, self._format_number(feito.numero))
        if noisy:
            transforms = (vary_ocr, vary_line_break, vary_uf_separator, vary_case)
            for transform in self._rng.sample(transforms, 2):
                text = transform(text, self._rng)
        found = self._classify(f"Conforme o {text}, a tese foi acolhida.")
        correct = any(
            item.classificacao == "real" and item.id_canonico in feito.ids
            for item in found
        )
        result.add("processo real com ruído" if noisy else "processo real", correct)

    def _check_invented(self, feito: Feito, result: SyntheticResult) -> None:
        key = feito.numero
        positions = [i for i, char in enumerate(key) if char.isdigit()][:4]
        i = self._rng.choice(positions)
        digit = str((int(key[i]) + self._rng.randint(1, 8)) % 10)
        fake = key[:i] + digit + key[i + 1 :]
        if fake.startswith("0") or self._base.find_feitos(fake):
            return
        text = self._citation(feito, self._format_number(fake))
        found = self._classify(f"Conforme o {text}, a tese foi acolhida.")
        correct = any(item.classificacao == "inventada" for item in found) and not any(
            item.classificacao == "real" for item in found
        )
        result.add("processo inventado", correct)

    def _check_catalog(self, result: SyntheticResult) -> None:
        for entry in DISPOSITIVOS:
            for form in _LAW_FORMS[entry.lei]:
                for article in (f"art. {entry.artigo}", f"artigo {entry.artigo}º, I,"):
                    found = self._classify(f"Nos termos do {article} {form}, procede.")
                    result.add(
                        "artigo real", any(i.classificacao == "real" for i in found)
                    )
            wrong_law = self._rng.choice(
                [law for law in _LAW_FORMS if law != entry.lei]
            )
            if any(
                d.lei == wrong_law and d.artigo == entry.artigo for d in DISPOSITIVOS
            ):
                continue
            wrong_form = _LAW_FORMS[wrong_law][0]
            found = self._classify(
                f"Nos termos do art. {entry.artigo} {wrong_form}, procede."
            )
            result.add(
                "artigo em lei errada",
                any(i.classificacao == "inventada" for i in found),
            )

        for entry in SUMULAS:
            if entry.vinculante:
                forms = (f"Súmula Vinculante {entry.numero}", f"SV {entry.numero}")
            else:
                forms = (
                    f"Súmula {entry.numero} do {entry.tribunal}",
                    f"Súmula nº {entry.numero}/{entry.tribunal}",
                    f"SÚMULA {entry.numero} DO {entry.tribunal}",
                )
            for form in forms:
                found = self._classify(f"Incide a {form} ao caso.")
                result.add("súmula real", any(i.classificacao == "real" for i in found))
            other = entry.numero + self._rng.randint(1, 50)
            found = self._classify(f"Incide a Súmula {other} do {entry.tribunal}.")
            result.add(
                "súmula inexistente",
                any(i.classificacao == "inventada" for i in found),
            )

    def _check_descriptions(self, result: SyntheticResult) -> None:
        records = [
            r
            for r in self._base.records
            if r.natureza == "acordao" and r.relator and r.ano
        ]
        for record in self._rng.sample(records, min(60, len(records))):
            name = record.relator.replace("Min. ", "")
            template = self._rng.choice(_DESCRIPTIONS)
            text = template.format(t=record.tribunal, a=record.ano, n=name)
            expected = self._base.count_described(record.tribunal, record.ano, name)
            expected_class = "real" if len(expected) == 1 else "incompleta"
            found = [
                item
                for item in self._classify(f"Invoca-se o {text}, no ponto.")
                if item.citacao.padrao == "decisao_descritiva"
            ]
            correct = bool(found) and found[0].classificacao == expected_class
            if correct and expected_class == "real":
                correct = found[0].id_canonico in expected[0].ids
            result.add("decisão descritiva", correct)
