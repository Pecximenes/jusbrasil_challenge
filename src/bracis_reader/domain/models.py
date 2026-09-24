"""Modelos utilizados na leitura e na detecção de citações."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TextDocument(BaseModel):
    """Documento carregado da pasta TXT."""

    model_config = ConfigDict(frozen=True)

    documento_id: str = Field(min_length=1)
    texto: str = Field(min_length=1)


class CitationCandidate(BaseModel):
    """Trecho identificado como uma possível citação jurídica."""

    model_config = ConfigDict(frozen=True)

    inicio: int = Field(ge=0)
    fim: int = Field(gt=0)
    trecho: str = Field(min_length=1)
    tipo: Literal["lei", "jurisprudencia"] | None = None

    @model_validator(mode="after")
    def validate_span(self) -> "CitationCandidate":
        """Valida a coerência entre o intervalo e o trecho."""
        if self.fim <= self.inicio:
            raise ValueError("fim deve ser maior que inicio")

        if self.fim - self.inicio != len(self.trecho):
            raise ValueError("o tamanho do trecho deve corresponder ao intervalo")

        return self
