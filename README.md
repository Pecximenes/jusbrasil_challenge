# Extração de citações jurídicas — Challenge Jusbrasil × BRACIS 2026

Este projeto lê decisões judiciais em texto, **encontra as citações jurídicas**
que aparecem nelas (processos, súmulas, artigos de lei e referências vagas
como "jurisprudência pacífica desta Corte") e **mede a qualidade** dessa
extração comparando o resultado com as anotações oficiais do desafio
(`goldenset.csv`).

> Nesta etapa o projeto apenas **localiza** as citações. Ele ainda não
> classifica o trecho como lei ou jurisprudência, nem decide se a referência
> é real, inventada ou incompleta.

---

## Sumário

1. [Visão geral do fluxo](#visão-geral-do-fluxo)
2. [Como rodar](#como-rodar)
3. [Estrutura de pastas](#estrutura-de-pastas)
4. [O que cada parte faz](#o-que-cada-parte-faz)
5. [Como as citações são encontradas (regex)](#como-as-citações-são-encontradas-regex)
6. [Como a avaliação funciona](#como-a-avaliação-funciona)
7. [Resultado atual](#resultado-atual)
8. [Problemas comuns](#problemas-comuns)

---

## Visão geral do fluxo

```text
 data/txt/*.txt                                   data/goldenset.csv
       │                                                  │
       ▼                                                  │
┌──────────────┐   ┌──────────────┐   ┌────────────────┐  │
│ 1. INGESTÃO  │──▶│ 2. EXTRAÇÃO  │──▶│ 3. AVALIAÇÃO   │◀─┘
│ lê os TXT e  │   │ pula o       │   │ compara cada   │
│ separa N1/N2 │   │ cabeçalho,   │   │ citação com o  │
│              │   │ aplica regex,│   │ goldenset      │
│              │   │ remove       │   │ (TP, FP, FN)   │
│              │   │ sobreposição │   │                │
└──────────────┘   └──────────────┘   └───────┬────────┘
                                              ▼
                                      ┌────────────────┐
                                      │ 4. RELATÓRIO   │
                                      │ tabela + F1 no │
                                      │ terminal       │
                                      └────────────────┘
```

Tudo isso é coordenado por um único arquivo, `pipeline.py`. Cada etapa fica
em uma pasta própria e pode ser trocada ou testada sozinha.

---

## Como rodar

Requisitos: **Python 3.11+** e **Git**.

### 1. Clonar

```bash
git clone -b develop https://github.com/Pecximenes/jusbrasil_challenge.git
cd jusbrasil_challenge
```

### 2. Criar o ambiente virtual e instalar

**Windows (PowerShell)**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### 3. Executar

```bash
python main.py
# ou, de forma equivalente:
python -m bracis_reader
```

O programa lê `data/txt/`, compara com `data/goldenset.csv` e imprime o
relatório no terminal.

### 4. Lint

```bash
ruff check .    # verifica estilo e imports
```

---

## Estrutura de pastas

```text
.
├── data/
│   ├── txt/                       # 26 decisões judiciais (13 N1 + 13 N2)
│   └── goldenset.csv              # Citações anotadas (gabarito)
├── refs/                          # Material original enviado pela Jusbrasil
├── src/bracis_reader/             # Código do projeto
│   ├── pipeline.py                # Orquestra o fluxo completo
│   ├── __main__.py                # Permite `python -m bracis_reader`
│   ├── domain/                    # Modelos de dados
│   ├── ingestion/                 # Etapa 1 — leitura dos documentos
│   ├── extraction/                # Etapa 2 — detecção das citações
│   │   └── patterns/              #   catálogo de regex
│   ├── evaluation/                # Etapa 3 — comparação com o gabarito
│   └── reporting/                 # Etapa 4 — saída no terminal
├── main.py                        # Atalho para rodar o projeto
├── pyproject.toml                 # Dependências e configuração
└── .gitattributes                 # Garante quebras de linha LF nos TXT
```

As dependências entre as pastas seguem uma única direção, sem ciclos:

```text
domain ◀── ingestion ◀── extraction ◀── evaluation ◀── reporting
                 ▲            ▲              ▲             ▲
                 └────────────┴── pipeline ──┴─────────────┘
```

---

## O que cada parte faz

### `domain/` — modelos de dados

`models.py` define os dois objetos que circulam pelo projeto (Pydantic,
imutáveis):

| Modelo | Campos | Para que serve |
|---|---|---|
| `TextDocument` | `documento_id`, `texto` | Um documento lido da pasta `data/txt` |
| `CitationCandidate` | `inicio`, `fim`, `trecho` | Uma citação encontrada no texto |

`fim` é exclusivo, e o modelo valida que o tamanho do trecho bate com o
intervalo. Toda citação respeita:

```python
documento.texto[citacao.inicio : citacao.fim] == citacao.trecho
```

### `ingestion/` — etapa 1: leitura

| Arquivo | Classe | O que faz |
|---|---|---|
| `directory_loader.py` | `TextDirectoryLoader` | Lê todos os `.txt` em UTF-8, em ordem alfabética, sem alterar o texto. O nome do arquivo vira o `documento_id`. |
| `level_splitter.py` | `DocumentLevelSplitter` | Separa os documentos em N1 e N2 pelo nome (`_n1_` / `_n2_`). Usado só nas estatísticas. |

### `extraction/` — etapa 2: detecção

| Arquivo | Classe | O que faz |
|---|---|---|
| `body_extractor.py` | `DocumentBodyExtractor` | Acha onde o corpo começa (depois de duas linhas vazias seguidas). O cabeçalho não é apagado; apenas não é pesquisado. |
| `detector.py` | `CitationDetector` | Aplica todas as regex no corpo e soma o deslocamento do cabeçalho, para os índices valerem no documento inteiro. |
| `overlap_resolver.py` | `CitationOverlapResolver` | Se duas regex pegam trechos sobrepostos, mantém o mais longo (ex.: fica "REsp 1.234.567/SP", sai só o número). |
| `patterns/` | — | O catálogo de regex, detalhado na próxima seção. |

### `evaluation/` — etapa 3: comparação com o gabarito

| Arquivo | Classe | O que faz |
|---|---|---|
| `goldenset.py` | `GoldensetLoader` | Lê o CSV e agrupa as citações esperadas por documento. Converte o texto `\n` do CSV em quebra de linha real. |
| `evaluator.py` | `CitationEvaluator` | Compara previsão × gabarito pela chave exata `(inicio, fim, trecho)` e calcula TP, FP, FN, precisão, recall e F1. |

### `reporting/` — etapa 4: saída

`console.py` (`ConsoleReportPrinter`) imprime uma linha por documento e as
métricas finais.

### `pipeline.py` — o maestro

`CitationExtractionApplication.run()` chama as etapas na ordem e devolve o
resumo das métricas. Detector, avaliador e relatório podem ser passados no
construtor, o que facilita testar ou trocar uma peça sem mexer no resto.

---

## Como as citações são encontradas (regex)

Os padrões ficam em `src/bracis_reader/extraction/patterns/`, separados
em três famílias. O `registry.py` junta tudo **nesta ordem**, que importa
para o desempate entre sobreposições.

**1. `structured.py` — citações completas**

| Padrão | Exemplo |
|---|---|
| `processo` | `AgInt no REsp nº 1.234.567/SP`, `Reclamação nº 66.516/RO` |
| `processo_trabalhista` | `TST-RR-1000-12.2019.5.02.0001` |
| `sumula` | `Súmula 83 do STJ`, `Súmula Vinculante 10` |
| `dispositivo_legal` | `art. 1.022, II, do CPC`, `art. 5º da Constituição Federal` |
| `numero_cnj` | `0001234-56.2020.8.26.0100` |

**2. `ocr.py` — as mesmas citações com erros de digitalização**

Aceita letras confundidas com dígitos (`O`→0, `I`/`l`→1, `S`→5), espaços e
quebras no meio dos números (`1. 570 531`) e grafias como `Ag. Int.`,
`EDcl`, `Rec. Esp.`.

**3. `generic.py` — referências incompletas (sem número)**

| Padrão | Exemplo |
|---|---|
| `referencia_normativa_generica` | "normas de regência da matéria" |
| `referencia_legislativa_generica` | "lei que disciplina a prescrição" |
| `entendimento_jurisprudencial_generico` | "jurisprudência pacífica desta Corte" |
| `precedente_generico` | "precedentes do STJ" |
| `enunciado_sumular_generico` | "verbete sumular aplicável à espécie" |
| `artigo_generico` | "artigo correspondente do Código Civil" |

Para adicionar um padrão novo: crie o `CitationPattern` no arquivo da
família certa, rode `python main.py` e compare o F1 antes e depois.

---

## Como a avaliação funciona

Uma citação só conta como acerto se **início, fim e trecho** forem
exatamente iguais aos do gabarito. Acerto parcial conta como erro.

| Coluna | Significado |
|---|---|
| `Gold` | Citações esperadas no gabarito |
| `Pred` | Citações encontradas pelo detector |
| `TP` | Acertos exatos |
| `FP` | Encontradas, mas que não estão no gabarito |
| `FN` | Estão no gabarito, mas não foram encontradas |

- **Precisão** = TP / Pred — das que encontrei, quantas estão certas.
- **Recall** = TP / Gold — das que existiam, quantas encontrei.
- **F1** = média harmônica entre as duas.

---

## Resultado atual

```text
Total de documentos: 26
Documentos N1: 13
Documentos N2: 13

Documento         Gold  Pred    TP    FP    FN
----------------------------------------------
gen_n1_001          10     8     7     1     3
...
----------------------------------------------
TOTAL              225   196   146    50    79

Precisão: 0.7449
Recall:   0.6489
F1:       0.6936
```

Onde há mais espaço para melhorar:

- a maior parte dos FN são **jurisprudências incompletas**, descritas sem
  número (ex.: "julgado do STF proferido em 2024 pela relatoria de…");
- os padrões genéricos de jurisprudência e de precedentes concentram boa
  parte dos FP e podem ficar mais restritos.

---

## Problemas comuns

**Todas as linhas mostram `TP = 0`.**
Os índices do gabarito contam a quebra de linha como um caractere (`\n`).
No Windows, o Git pode converter os `.txt` para CRLF (`\r\n`), o que desloca
todas as posições. O `.gitattributes` já impede isso em clones novos. Em um
clone antigo, regrave os arquivos:

```bash
git rm --cached -r .
git reset --hard
```

**`ModuleNotFoundError: No module named 'bracis_reader'`.**
O pacote não foi instalado. Ative o `.venv` e rode
`python -m pip install -e ".[dev]"`.
