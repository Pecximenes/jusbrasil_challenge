# Extração de citações jurídicas — Challenge Jusbrasil × BRACIS 2026

Este projeto lê decisões judiciais em texto, **encontra as citações jurídicas**
que aparecem nelas (processos, súmulas, artigos de lei e referências vagas
como "jurisprudência pacífica desta Corte") e **mede a qualidade** dessa
extração comparando o resultado com as anotações oficiais do desafio
(`goldenset.csv`).

> Nesta etapa o projeto **localiza** as citações e indica se cada uma é
> `lei` ou `jurisprudencia`. Ele ainda não decide se a referência é real,
> inventada ou incompleta, o que exige consultar a base canônica.

---

## Sumário

1. [Visão geral do fluxo](#visão-geral-do-fluxo)
2. [Como rodar](#como-rodar)
3. [Estrutura de pastas](#estrutura-de-pastas)
4. [O que cada parte faz](#o-que-cada-parte-faz)
5. [Como as citações são encontradas (regex)](#como-as-citações-são-encontradas-regex)
6. [Como a avaliação funciona](#como-a-avaliação-funciona)
7. [Resultado atual](#resultado-atual)
8. [Como evitamos sobreajuste ao goldenset](#como-evitamos-sobreajuste-ao-goldenset)
9. [Problemas comuns](#problemas-comuns)

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

Opções:

| Opção | O que faz |
|---|---|
| `--exato` | Conta acerto só com início, fim e trecho idênticos (padrão: IoU ≥ 0,5, como na avaliação oficial) |
| `--robustez` | Roda também o teste de robustez a ruído (ver [Como evitamos sobreajuste](#como-evitamos-sobreajuste-ao-goldenset)) |
| `--txt PASTA` | Usa outra pasta de documentos |
| `--gold CSV` | Usa outro gabarito |

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
│   │   └── patterns/              #   catálogo de regex (ver abaixo)
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
| `CitationCandidate` | `inicio`, `fim`, `trecho`, `tipo` | Uma citação encontrada no texto; `tipo` é `lei` ou `jurisprudencia` |

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
| `body_extractor.py` | `DocumentBodyExtractor` | Acha onde o corpo começa (depois de duas linhas vazias seguidas; se não houver, na primeira linha vazia). O cabeçalho, com número dos autos, OAB e valor da causa, não é apagado; apenas não é pesquisado. |
| `detector.py` | `CitationDetector` | Aplica todas as regex no corpo e soma o deslocamento do cabeçalho, para os índices valerem no documento inteiro. |
| `overlap_resolver.py` | `CitationOverlapResolver` | Se duas regex pegam trechos sobrepostos, mantém o mais longo (ex.: fica "REsp 1.234.567/SP", sai só o número). |
| `patterns/` | — | O catálogo de regex, detalhado na próxima seção. |

### `evaluation/` — etapa 3: comparação com o gabarito

| Arquivo | Classe | O que faz |
|---|---|---|
| `goldenset.py` | `GoldensetLoader` | Lê o CSV e agrupa as citações esperadas por documento. Converte o texto `\n` do CSV em quebra de linha real. |
| `evaluator.py` | `CitationEvaluator` | Pareia previsão × gabarito por IoU ≥ 0,5 (critério oficial) ou por igualdade exata, e calcula TP, FP, FN, precisão, recall e F1. |
| `robustness.py` | `NoiseRobustnessEvaluator` | Gera variantes ruidosas das citações do gabarito e mede quantas o detector ainda encontra. |

### `reporting/` — etapa 4: saída

`console.py` (`ConsoleReportPrinter`) imprime uma linha por documento e as
métricas finais.

### `pipeline.py` — o maestro

`CitationExtractionApplication.run()` chama as etapas na ordem e devolve o
resumo das métricas. Detector, avaliador e relatório podem ser passados no
construtor, o que facilita testar ou trocar uma peça sem mexer no resto.

---

## Como as citações são encontradas (regex)

As regras ficam em `src/bracis_reader/extraction/patterns/`. A ideia central
é **não escrever uma regex por exemplo**, e sim descrever *como uma citação é
formada* e deixar cada parte tolerante às variações previstas no regulamento.

| Arquivo | Conteúdo |
|---|---|
| `text.py` | Blocos genéricos: palavras tolerantes a OCR, números, ano, marcador "nº" |
| `lexicon.py` | Vocabulário jurídico: classes processuais, siglas, tribunais, UFs, códigos |
| `jurisprudence.py` | Processos, números CNJ, súmulas, temas e OJs |
| `legislation.py` | Artigos de lei, códigos e Constituição |
| `incomplete.py` | Citações sem número (descritivas e genéricas) |
| `registry.py` | Junta tudo na ordem de prioridade |

### Tolerância a ruído, aplicada a tudo

- **Palavras** são compiladas por `fuzzy_word()`, que aceita acentos opcionais,
  maiúsculas/minúsculas e as trocas de OCR mais comuns (`c↔e`, `l↔1`, `o↔0`,
  `s↔5`, `m↔rn`). "Súmula", "SÚMULA", "Sumula", "5úmula" e "entendirnento"
  saem da mesma regra.
- **Números** aceitam qualquer formatação: `1.741.784`, `1741784`,
  `1 741 784`, `1.741. 784`, `33.-⏎474`, letras no lugar de dígitos
  (`2l737l8`, `170076O`) e quebras de linha. Um grupo precisa começar por
  dígito real, para que siglas como "SC" ou "TO" não virem número.
- **Espaços** incluem quebra de linha e espaço não separável (`\xa0`).

### Jurisprudência com identificador (`jurisprudence.py`)

```text
[processo nº] CLASSE [no|na|nos|nas|em CLASSE]... [nº] NÚMERO [/UF]
```

- **CLASSE** vem do vocabulário: nomes por extenso (cada palavra pode vir
  abreviada: "Rec. Esp.", "Ag. Reg."), siglas com pontos opcionais ("R.Esp.",
  "H.C.", "A.REsp"), siglas compostas por prefixo (Ag+REsp = AgREsp,
  E+REsp = EREsp) e cadeias do TST com hífen (`E-ED-RR`, `AgR-REspe`).
- **UF** só aceita as 27 siglas reais, em qualquer separador (`/SP`, `- SP`,
  `(SP)`, `/ SP`).
- Também: **súmulas** (`Súmula 83 do STJ`, `Súm. 7/STJ`, `Súmula Vinculante 10`),
  **temas** (`Tema 1.046 da repercussão geral`), **OJs** (`OJ 191 da SBDI-1`)
  e **números CNJ** soltos no corpo.

### Legislação (`legislation.py`)

```text
art./artigo NÚMERO [, § 1º | , I | , 'g' | , parágrafo único]... da|do LEI
```

**LEI** pode ser lei numerada (`Lei nº 13.105/2015`, `Lei 8.078, de 1990`),
qualquer "Código ..." (`Código de Defesa do Consumidor`, `Código Penal Militar`),
a Constituição, a CLT por extenso, um estatuto ou uma sigla (`CPC`, `CF/88`).

### Citações sem número (`incomplete.py`)

1. **Descritivas**, que dá para buscar na base por tribunal, ano e relator:

   ```text
   DECISÃO [do TRIBUNAL] [, em|de ANO] [, relatoria de NOME]   (exige ano ou relator)
   ```

   Ex.: "julgado do STF proferido em 2024 pela relatoria de Dias Toffoli",
   "Rcl de 2021, Rel. Min. Rosa Weber".

2. **Genéricas**, que só aludem a uma fonte. Para contar como citação, a
   alusão precisa ser específica: **um qualificador de autoridade e uma
   âncora**, ou duas âncoras.

   | | Exemplos |
   |---|---|
   | Qualificador | pacífica, consolidada, sumulado, reiterados, firme, recente, aplicável |
   | Âncora | desta Corte, do STJ, sobre a matéria, à espécie, em sede de recurso repetitivo, de regência, na origem, que disciplina a prescrição |

   Assim entram "jurisprudência pacífica desta Corte" e "normas de regência da
   matéria". Ficam de fora frases soltas ou que só retomam outra citação,
   como "a orientação dominante", "a orientação firmada no REsp X" e "os
   dispositivos invocados".

### Como adicionar uma regra

Na maioria dos casos basta **acrescentar uma palavra ao `lexicon.py`**: uma
nova classe, sigla ou tribunal passa a valer em todas as combinações. Depois,
rode `python main.py --robustez` e confira que as três métricas (gabarito,
robustez e ausência de novos FP) não pioraram.

---

## Como a avaliação funciona

Por padrão o projeto usa o **mesmo critério da avaliação oficial**: previsão
e gabarito formam um par quando a sobreposição dos intervalos (IoU) é de pelo
menos 50%, e cada citação entra em no máximo um par. Com `--exato`, só conta
acerto quando início, fim e trecho são idênticos.

| Coluna | Significado |
|---|---|
| `Gold` | Citações esperadas no gabarito |
| `Pred` | Citações encontradas pelo detector |
| `TP` | Acertos |
| `FP` | Encontradas, mas sem par no gabarito |
| `FN` | Estão no gabarito, mas não foram encontradas |

- **Precisão** = TP / Pred: das que encontrei, quantas estão certas.
- **Recall** = TP / Gold: das que existiam, quantas encontrei.
- **F1** = média harmônica entre as duas.

---

## Resultado atual

| Métrica | Regras antigas | Regras atuais |
|---|---|---|
| F1 no gabarito, critério oficial (IoU ≥ 0,5) | 0,8219 | **0,9911** |
| F1 no gabarito, critério exato | 0,6936 | **0,9733** |
| F1 nível 1 / nível 2 | 0,84 / 0,80 | **1,00 / 0,98** |
| Robustez: variantes ruidosas encontradas | 70,4% | **99,1%** |
| Frases escritas fora do gabarito: positivos encontrados | 23 / 36 | **36 / 36** |
| Frases escritas fora do gabarito: distratores com FP | 1 / 19 | **0 / 19** |
| `tipo` (lei/jurisprudência) correto nos acertos | não havia | **223 / 223** |

Os 2 erros restantes no gabarito não são do detector: no documento
`gen_n2_010`, seis anotações têm offsets deslocados em relação ao texto (o
trecho anotado não está na posição indicada), e duas delas não chegam a 50%
de sobreposição com a citação correta.

---

## Como evitamos sobreajuste ao goldenset

O conjunto oficial é oculto, então acertar o goldenset não basta: uma regra
pode decorar os 225 exemplos e falhar no resto. Três cuidados:

1. **Regras descrevem estrutura, não exemplos.** Os padrões são montados a
   partir de vocabulário do domínio (`lexicon.py`) e das variações descritas
   no regulamento (abreviação, formatação do número, separador de UF, OCR,
   quebras de linha). Nenhum trecho do gabarito foi copiado para as regras.
2. **Teste de robustez (`--robustez`).** Cada citação do gabarito recebe
   variações aleatórias de superfície, como `REsp` → `Rec. Esp.`,
   `1.741.784` → `1741784`, `/PR` → `(PR)`, `1` → `l` e espaço → quebra de
   linha. A variante é recolocada no documento e o teste verifica se o
   detector ainda a encontra. Isso mede se a regra generaliza para formas
   que não estão no gabarito.
3. **Texto nunca visto.** O detector foi rodado sobre as 1.000 decisões reais
   da base canônica e sobre frases escritas à mão, com citações e com os
   distratores do regulamento (OAB, fls., valor da causa, CNPJ, protocolo).
   As capturas foram revisadas por amostragem.

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
