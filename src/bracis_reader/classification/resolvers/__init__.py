"""Uma estratégia de classificação para cada padrão de citação."""

from collections.abc import Mapping

from bracis_reader.classification.canonical_base import CanonicalBase
from bracis_reader.classification.canonical_catalog import CanonicalCatalog
from bracis_reader.classification.resolvers.article import ArticleResolver
from bracis_reader.classification.resolvers.base import CitationResolver, Resolution
from bracis_reader.classification.resolvers.description import DescriptionResolver
from bracis_reader.classification.resolvers.fixed import (
    GenericResolver,
    OutOfBaseResolver,
)
from bracis_reader.classification.resolvers.process import ProcessNumberResolver
from bracis_reader.classification.resolvers.sumula import SumulaResolver


def default_resolvers(base: CanonicalBase) -> Mapping[str, CitationResolver]:
    """Associa o nome de cada padrão do detector ao seu resolvedor."""
    catalog = CanonicalCatalog(base)
    process = ProcessNumberResolver(base)
    out_of_base = OutOfBaseResolver()
    return {
        "processo": process,
        "numero_cnj": process,
        "sumula": SumulaResolver(catalog.sumulas),
        "dispositivo_legal": ArticleResolver(catalog.dispositivos),
        "tema": out_of_base,
        "orientacao_jurisprudencial": out_of_base,
        "decisao_descritiva": DescriptionResolver(base),
    }


__all__ = [
    "ArticleResolver",
    "CitationResolver",
    "DescriptionResolver",
    "GenericResolver",
    "OutOfBaseResolver",
    "ProcessNumberResolver",
    "Resolution",
    "SumulaResolver",
    "default_resolvers",
]
