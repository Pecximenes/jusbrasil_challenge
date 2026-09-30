"""Configuração de uma execução, independente de como foi informada."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DataProfile:
    """Conjunto de arquivos usado por padrão em uma execução."""

    txt: Path
    goldenset: Path
    base: Path


ORIGINAL_DATA = DataProfile(
    txt=Path("data/txt"),
    goldenset=Path("data/goldenset.csv"),
    base=Path("refs/desafio1_bracis.db"),
)
KAGGLE_DATA = DataProfile(
    txt=Path("data/kaggle/txt"),
    goldenset=Path("data/kaggle/goldenset.csv"),
    base=Path("data/kaggle/desafio1_bracis.db"),
)
DEFAULT_OUTPUT_DIRECTORY = Path("saida")


@dataclass(frozen=True)
class Settings:
    """Parâmetros já resolvidos de uma execução."""

    txt: Path
    goldenset: Path | None
    base: Path
    output: Path = DEFAULT_OUTPUT_DIRECTORY
    exact_match: bool = False
    include_generic: bool = False
    calibrated_confidence: bool = False
    robustness: bool = False
    calibration: bool = False
