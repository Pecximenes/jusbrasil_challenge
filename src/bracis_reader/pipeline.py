"""Extração seguida de classificação, sem entrada, saída ou métricas."""

from collections.abc import Iterable
from dataclasses import dataclass

from bracis_reader.domain.models import TextDocument
from bracis_reader.domain.ports import (
    CandidatesByDocument,
    CitationClassifierPort,
    CitationExtractor,
    ResultsByDocument,
)


@dataclass(frozen=True)
class PipelineOutput:
    """Citações encontradas e, se houver classificador, suas classes."""

    predictions: CandidatesByDocument
    results: ResultsByDocument


class CitationPipeline:
    """Aplica o extrator e, quando disponível, o classificador."""

    def __init__(
        self,
        extractor: CitationExtractor,
        classifier: CitationClassifierPort | None = None,
    ) -> None:
        self._extractor = extractor
        self._classifier = classifier

    def process(self, documents: Iterable[TextDocument]) -> PipelineOutput:
        predictions = self._extractor.detect_many(documents)
        if self._classifier is None:
            return PipelineOutput(predictions=predictions, results={})
        results = {
            documento_id: self._classifier.classify_many(citations)
            for documento_id, citations in predictions.items()
        }
        return PipelineOutput(predictions=predictions, results=results)
