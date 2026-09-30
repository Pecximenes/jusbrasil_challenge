"""Classificação de cada citação em real, inventada ou incompleta."""

from collections.abc import Mapping

from bracis_reader.classification.canonical_base import CanonicalBase
from bracis_reader.classification.confidence import (
    CalibratedConfidence,
    ConfidencePolicy,
)
from bracis_reader.classification.resolvers import (
    CitationResolver,
    GenericResolver,
    default_resolvers,
)
from bracis_reader.domain.models import CitationCandidate, ClassifiedCitation


class CitationClassifier:
    """Encaminha cada citação ao resolvedor do seu padrão.

    Novos tipos de citação entram registrando outro resolvedor, sem alterar
    esta classe.
    """

    def __init__(
        self,
        resolvers: Mapping[str, CitationResolver],
        fallback: CitationResolver | None = None,
        confidence: ConfidencePolicy | None = None,
    ) -> None:
        self._resolvers = dict(resolvers)
        self._fallback = fallback or GenericResolver()
        self._confidence = confidence or CalibratedConfidence()

    @classmethod
    def from_base(
        cls, base: CanonicalBase, confidence: ConfidencePolicy | None = None
    ) -> "CitationClassifier":
        """Classificador com os resolvedores padrão sobre a base informada."""
        return cls(default_resolvers(base), confidence=confidence)

    def classify(self, citation: CitationCandidate) -> ClassifiedCitation:
        """Classifica uma citação encontrada pelo detector."""
        resolver = self._resolvers.get(citation.padrao or "", self._fallback)
        resolution = resolver.resolve(citation.trecho)
        return ClassifiedCitation(
            citacao=citation,
            classificacao=resolution.classificacao,
            id_canonico=resolution.id_canonico,
            confianca=self._confidence.for_rule(resolution.regra),
            motivo=f"{resolution.regra}: {resolution.motivo}",
        )

    def classify_many(
        self, citations: list[CitationCandidate]
    ) -> list[ClassifiedCitation]:
        return [self.classify(citation) for citation in citations]
