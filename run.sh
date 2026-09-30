#!/usr/bin/env bash
# Uso: bash run.sh <caminho_db> <pasta_txt> <arquivo_saida>
# Gera <arquivo_saida> no formato do submission.csv e, na mesma pasta,
# json/<documento_id>.json com as citações de cada documento.
set -euo pipefail

if [ "$#" -ne 3 ]; then
    echo "uso: bash run.sh <caminho_db> <pasta_txt> <arquivo_saida>" >&2
    exit 2
fi

DB="$1"
TXT="$2"
OUT="$3"

if [ ! -f "$DB" ]; then
    echo "erro: base canônica não encontrada: $DB" >&2
    exit 1
fi
if [ ! -d "$TXT" ]; then
    echo "erro: pasta de documentos não encontrada: $TXT" >&2
    exit 1
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-$(command -v python3 || command -v python)}"
OUT_DIR="$(dirname "$OUT")"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}" PYTHONHASHSEED=0 \
    "$PYTHON" -m bracis_reader --base "$DB" --txt "$TXT" --sem-gabarito --saida "$WORK"

mkdir -p "$OUT_DIR/json"
cp "$WORK/submission.csv" "$OUT"
cp "$WORK"/json/*.json "$OUT_DIR/json/"
