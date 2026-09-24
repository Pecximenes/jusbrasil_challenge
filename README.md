# Extração de citações jurídicas — BRACIS 2026

Projeto para leitura dos documentos do Challenge Jusbrasil × BRACIS 2026,
extração de citações jurídicas e avaliação por correspondência exata com o
`goldenset.csv`.

A etapa atual apenas localiza as citações. Ela não classifica o trecho como
lei ou jurisprudência e não determina se a referência é real, inventada ou
incompleta.

## Funcionalidades

- carrega todos os arquivos `.txt` de um diretório;
- separa os documentos entre N1 e N2;
- ignora o cabeçalho sem alterar o texto original;
- extrai processos, números CNJ, súmulas e dispositivos legais;
- aceita variações de espaços, quebras de linha e alguns ruídos de OCR;
- detecta referências jurídicas incompletas por padrões linguísticos;
- remove candidatos sobrepostos, mantendo o trecho mais completo;
- preserva os índices absolutos `inicio` e `fim`;
- compara as previsões com o goldenset;
- calcula precisão, recall e F1.

## Estrutura

```text
.
├── data/
│   ├── txt/                            # Documentos jurídicos (LF)
│   └── goldenset.csv                   # Anotações de referência
├── refs/                               # Material original enviado pela Jusbrasil
├── src/
│   └── bracis_reader/
│       ├── __init__.py                 # API pública do pacote
│       ├── __main__.py                 # `python -m bracis_reader`
│       ├── pipeline.py                 # Orquestração do fluxo completo
│       ├── domain/
│       │   └── models.py               # Modelos Pydantic
│       ├── ingestion/
│       │   ├── directory_loader.py     # Leitura dos arquivos TXT
│       │   └── level_splitter.py       # Separação N1/N2
│       ├── extraction/
│       │   ├── body_extractor.py       # Localização do início do corpo
│       │   ├── detector.py             # Aplicação das regex
│       │   ├── overlap_resolver.py     # Remoção de sobreposições
│       │   └── patterns/
│       │       ├── base.py             # CitationPattern, flags e espaços
│       │       ├── structured.py       # Processos, CNJ, súmulas, artigos
│       │       ├── ocr.py              # Variações tolerantes a OCR
│       │       ├── generic.py          # Referências incompletas
│       │       └── registry.py         # Junta os catálogos na ordem correta
│       ├── evaluation/
│       │   ├── goldenset.py            # Leitura do goldenset
│       │   └── evaluator.py            # TP, FP, FN e métricas
│       └── reporting/
│           └── console.py              # Tabela exibida no terminal
├── tests/                              # Testes com pytest
├── main.py                             # Atalho para `python -m bracis_reader`
├── .gitattributes                      # Força LF nos TXT/CSV (ver abaixo)
└── pyproject.toml                      # Dependências e ferramentas
```

Cada subpacote corresponde a uma etapa do pipeline e só depende de `domain`
e das etapas anteriores:

```text
domain  ←  ingestion  ←  extraction  ←  evaluation  ←  reporting
                               ↖______ pipeline ______↗
```

### Quebras de linha

Os índices `inicio`/`fim` do goldenset contam quebras de linha como `\n`.
No Windows, o Git converte arquivos de texto para CRLF por padrão, o que
desloca todos os spans e zera os acertos. O `.gitattributes` força `eol=lf`
nos `.txt` e mantém os `.csv` exatamente como foram enviados. Se o repositório já estava clonado antes dessa
mudança, rode `git rm --cached -r . && git reset --hard` para regravar os
arquivos.

## Arquitetura

O projeto segue responsabilidade única e inversão de dependência de forma
simples. O fluxo principal depende de componentes pequenos e substituíveis:

```text
main.py
   ↓
CitationExtractionApplication
   ├── TextDirectoryLoader
   ├── DocumentLevelSplitter
   ├── CitationDetector
   │      ├── DocumentBodyExtractor
   │      ├── CitationPatternRegistry
   │      └── CitationOverlapResolver
   ├── GoldensetLoader
   ├── CitationEvaluator
   └── ConsoleReportPrinter
```

### `TextDirectoryLoader`

Lê os arquivos `.txt` em UTF-8, usa o nome do arquivo como `documento_id` e
preserva o texto original, inclusive as quebras de linha.

### `DocumentLevelSplitter`

Separa documentos com `_n1_` e `_n2_` no nome. A separação é usada somente
para estatísticas; o detector funciona da mesma forma nos dois níveis.

### `DocumentBodyExtractor`

Localiza o corpo após duas linhas vazias consecutivas. O cabeçalho não é
apagado: o detector pesquisa apenas no corpo e soma o deslocamento inicial ao
resultado. Dessa forma, os índices continuam referentes ao documento inteiro.

### `CitationPatternRegistry`

Centraliza todas as expressões regulares. Os padrões estão separados em:

- estruturados: processos, CNJ, súmulas, artigos e códigos;
- tolerantes a OCR: espaços, separadores e caracteres confundidos;
- genéricos: referências incompletas, como entendimento sumular ou norma de
  regência.

Os nomes dos padrões são internos e não classificam a saída.

### `CitationDetector`

Aplica os padrões ao corpo do documento e cria objetos `CitationCandidate`.
O construtor permite injetar padrões, extrator de corpo e resolvedor de
sobreposição, facilitando testes e futuras alterações.

### `CitationOverlapResolver`

Quando duas regex encontram intervalos que se sobrepõem, mantém o candidato
mais longo. Isso evita retornar separadamente o número CNJ e a citação completa
que contém esse número.

### `GoldensetLoader`

Lê o CSV e agrupa as anotações por `documento_id`. Sequências textuais `\n` do
CSV são convertidas para quebras de linha reais antes da comparação.

### `CitationEvaluator`

Compara cada previsão pela chave exata:

```python
(inicio, fim, trecho)
```

Uma detecção parcialmente correta não conta como acerto.

### `ConsoleReportPrinter`

Exibe uma linha por documento e as métricas agregadas.

## Modelos

### `TextDocument`

```python
{
    "documento_id": "gen_n1_001",
    "texto": "conteúdo integral do documento",
}
```

### `CitationCandidate`

```python
{
    "inicio": 797,
    "fim": 820,
    "trecho": "Reclamação nº 66.516/RO",
}
```

`fim` é exclusivo. Todo resultado deve respeitar:

```python
documento.texto[citacao.inicio : citacao.fim] == citacao.trecho
```

## Instalação no Ubuntu

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Execução

Com os documentos em `data/txt` e o CSV em `data/goldenset.csv`:

```bash
python main.py
# ou
python -m bracis_reader
```

Testes e lint:

```bash
pytest
ruff check .
```

Exemplo de saída:

```text
Documento         Gold  Pred    TP    FP    FN
----------------------------------------------
gen_n1_001          10     8     8     0     2
...
----------------------------------------------
TOTAL               225   176   150    26    75

Precisão: 0.8523
Recall:   0.6667
F1:       0.7481
```

As métricas do exemplo são ilustrativas.

## Significado das métricas

- `Gold`: quantidade esperada no goldenset;
- `Pred`: quantidade extraída pelo detector;
- `TP`: intervalo e trecho exatamente corretos;
- `FP`: previsão sem correspondência exata;
- `FN`: citação esperada que não foi encontrada;
- precisão: proporção das previsões que estão corretas;
- recall: proporção das citações esperadas que foram encontradas;
- F1: equilíbrio entre precisão e recall.


## Cuidados contra superajuste

- nenhuma regra depende do `documento_id`;
- nenhuma regra usa uma posição fixa;
- os padrões estruturados representam formatos jurídicos reutilizáveis;
- regras de OCR tratam categorias de ruído, não números específicos;
- padrões genéricos devem ser monitorados, pois têm maior risco de falso
  positivo;
- treino e validação devem ser separados por documento;
- alterações devem ser avaliadas por TP, FP, FN e F1, não apenas pelo total de
  citações encontradas.
