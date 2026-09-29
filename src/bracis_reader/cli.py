"""Interface de linha de comando: ``python -m bracis_reader``."""

import argparse
import sys
from pathlib import Path

from bracis_reader import bootstrap, diagnostics
from bracis_reader.settings import (
    DEFAULT_OUTPUT_DIRECTORY,
    KAGGLE_DATA,
    ORIGINAL_DATA,
    Settings,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bracis_reader",
        description="Extrai e classifica citações jurídicas.",
    )
    parser.add_argument("--txt", type=Path, default=None)
    parser.add_argument("--gold", type=Path, default=None)
    parser.add_argument("--kaggle", action="store_true")
    parser.add_argument("--sem-gabarito", action="store_true")
    parser.add_argument("--base", type=Path, default=None)
    parser.add_argument("--saida", type=Path, default=DEFAULT_OUTPUT_DIRECTORY)
    parser.add_argument("--exato", action="store_true")
    parser.add_argument("--robustez", action="store_true")
    parser.add_argument("--calibrar", action="store_true")
    parser.add_argument("--genericas", action="store_true")
    parser.add_argument("--confianca-calibrada", action="store_true")
    parser.add_argument(
        "--confianca-maxima", action="store_true", help=argparse.SUPPRESS
    )
    return parser


def parse_settings(argv: list[str] | None = None) -> Settings:
    """Converte os argumentos em uma configuração resolvida."""
    args = _parser().parse_args(argv)
    profile = KAGGLE_DATA if args.kaggle else ORIGINAL_DATA
    return Settings(
        txt=args.txt or profile.txt,
        goldenset=None if args.sem_gabarito else (args.gold or profile.goldenset),
        base=args.base or profile.base,
        output=args.saida,
        exact_match=args.exato,
        include_generic=args.genericas,
        calibrated_confidence=args.confianca_calibrada,
        robustness=args.robustez,
        calibration=args.calibrar,
    )


def main(argv: list[str] | None = None) -> None:
    """Executa o fluxo com os caminhos informados."""
    settings = parse_settings(argv)
    components = bootstrap.build(settings)
    if components.classifier is None:
        print(
            f"Aviso: base canônica não encontrada em {settings.base}; "
            "a classificação e a saída serão puladas.",
            file=sys.stderr,
        )

    components.application.run(
        txt_directory=settings.txt,
        goldenset_path=settings.goldenset,
        output_directory=settings.output,
    )
    _run_diagnostics(settings, components)


def _run_diagnostics(settings: Settings, components: bootstrap.Components) -> None:
    base, classifier, goldenset = (
        components.base,
        components.classifier,
        settings.goldenset,
    )
    if settings.calibration and classifier is not None and goldenset is not None:
        diagnostics.print_calibration(settings.txt, goldenset, classifier)
    if settings.robustness and goldenset is not None:
        diagnostics.print_noise_robustness(settings.txt, goldenset)
    if settings.robustness and base is not None and classifier is not None:
        diagnostics.print_synthetic(base, classifier)
