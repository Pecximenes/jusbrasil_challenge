"""Resolução de candidatos de citação que ocupam o mesmo intervalo."""

from bracis_reader.domain.models import CitationCandidate


class CitationOverlapResolver:
    """Mantém o trecho mais completo quando candidatos se sobrepõem."""

    def resolve(
        self,
        candidates: list[CitationCandidate],
    ) -> list[CitationCandidate]:
        """Remove sobreposições e devolve os candidatos em ordem textual."""
        candidates_by_priority = sorted(
            candidates,
            key=lambda item: (item.inicio, -(item.fim - item.inicio)),
        )
        selected: list[CitationCandidate] = []

        for candidate in candidates_by_priority:
            if self._overlaps_any(candidate, selected):
                continue
            selected.append(candidate)

        return sorted(selected, key=lambda item: item.inicio)

    @staticmethod
    def _overlaps_any(
        candidate: CitationCandidate,
        selected: list[CitationCandidate],
    ) -> bool:
        return any(
            candidate.inicio < current.fim and current.inicio < candidate.fim
            for current in selected
        )
