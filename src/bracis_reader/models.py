"""Modelo utilizado para representar um documento de texto."""

from pydantic import BaseModel, ConfigDict, Field


class TextDocument(BaseModel):
    """Documento carregado da pasta TXT."""

    model_config = ConfigDict(frozen=True)

    documento_id: str = Field(min_length=1)
    texto: str = Field(min_length=1)
