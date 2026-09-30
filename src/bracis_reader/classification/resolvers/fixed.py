"""Resolvedores sem consulta à base."""

from bracis_reader.classification.resolvers.base import Resolution


class OutOfBaseResolver:
    """Temas e orientações jurisprudenciais não existem na base canônica."""

    def resolve(self, trecho: str) -> Resolution:
        return Resolution.inventada("tema_oj", "tipo de precedente fora da base")


class GenericResolver:
    """Alusões sem identificador nunca podem ser confirmadas."""

    def resolve(self, trecho: str) -> Resolution:
        return Resolution.incompleta("generica", "sem identificador")
