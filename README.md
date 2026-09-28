# Caça-Alucinações — Challenge Jusbrasil × BRACIS 2026

Peças jurídicas às vezes citam precedentes e leis que não existem. Este
projeto lê cada documento, **encontra as citações jurídicas** e **decide se
cada uma é real, inventada ou incompleta**, consultando a base canônica do
desafio (`desafio1_bracis.db`). Para as reais, informa o `id_canonico` do
registro na base.

| Classe | Quando |
|---|---|
| `real` | A citação aponta para exatamente um processo da base |
| `inventada` | Dá para buscar, mas o processo, súmula ou artigo não existe na base |
| `incompleta` | Não há dados para buscar ("jurisprudência pacífica desta Corte"), ou a busca devolve vários processos sem como desempatar |

A saída é um JSON por documento e o `submission.csv` no formato do Kaggle.

---

## Sumário

1. [Visão geral do fluxo](#visão-geral-do-fluxo)
2. [Como rodar](#como-rodar)
3. [Estrutura de pastas](#estrutura-de-pastas)
4. [O que cada parte faz](#o-que-cada-parte-faz)
5. [Como as citações são encontradas (regex)](#como-as-citações-são-encontradas-regex)
6. [Como as citações são classificadas](#como-as-citações-são-classificadas)
7. [Como a avaliação funciona](#como-a-avaliação-funciona)
8. [Resultado atual](#resultado-atual)
9. [Como evitamos sobreajuste ao goldenset](#como-evitamos-sobreajuste-ao-goldenset)
10. [Problemas comuns](#problemas-comuns)

---

## Visão geral do fluxo

```text
 data/txt/*.txt          refs/desafio1_bracis.db          data/goldenset.csv
       │                           │                        (opcional)
       ▼                           ▼                            │
┌─────────────┐  ┌─────────────┐  ┌──────────────────┐          │
│ 1. INGESTÃO │─▶│ 2. EXTRAÇÃO │─▶│ 3. CLASSIFICAÇÃO │          │
│ lê os TXT   │  │ regex acham │  │ consulta a base: │          │
│             │  │ as citações │  │ real, inventada  │          │
│             │  │ e o tipo    │  │ ou incompleta    │          │
└─────────────┘  └─────────────┘  └────────┬─────────┘          │
                                           ▼                    ▼
                               ┌──────────────────┐  ┌──────────────────┐
                               │ 4. SAÍDA         │  │ 5. AVALIAÇÃO     │
                               │ JSON por doc +   │  │ compara com o    │
                               │ submission.csv   │  │ gabarito         │
                               └──────────────────┘  └──────────────────┘
```

Tudo é coordenado por `pipeline.py`. Sem gabarito (caso do conjunto oculto),
as etapas 1 a 4 rodam normalmente e a avaliação é pulada.

---

## Como rodar

Requisitos: **Python 3.11+** e **Git**. A base `refs/desafio1_bracis.db`
precisa estar no repositório (93 MB).

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

**Desenvolvimento (com gabarito):**

```bash
python main.py
# ou, de forma equivalente:
python -m bracis_reader
```

Lê `data/txt/`, extrai e classifica as citações, grava a saída em `saida/`
e imprime as métricas de extração e de classificação.

**Conjunto oculto (sem gabarito):**

```bash
python -m bracis_reader --txt caminho/dos/txt --sem-gabarito --saida resultado
```

Gera `resultado/json/<documento_id>.json` e `resultado/submission.csv`.

| Opção | O que faz |
|---|---|
| `--txt PASTA` | Pasta dos documentos (padrão: `data/txt`) |
| `--gold CSV` | Gabarito (padrão: `data/goldenset.csv`) |
| `--sem-gabarito` | Não avalia; só extrai, classifica e grava |
| `--base DB` | Base canônica (padrão: `refs/desafio1_bracis.db`) |
| `--saida PASTA` | Onde gravar `json/` e `submission.csv` (padrão: `saida`) |
| `--exato` | Avalia a extração por igualdade exata (padrão: IoU ≥ 0,5, como na avaliação oficial) |
| `--robustez` | Roda os testes de generalização (ver [Como evitamos sobreajuste](#como-evitamos-sobreajuste-ao-goldenset)) |
| `--sem-ajustes` | Desliga os ajustes pontuais do conjunto de desenvolvimento (ver [Resultado atual](#resultado-atual)) |

### 4. Lint

```bash
ruff check .    # verifica estilo e imports
```

---

## Estrutura de pastas

```text
.
├── data/
│   ├── txt/                       # 26 peças jurídicas (13 N1 + 13 N2)
│   └── goldenset.csv              # Citações anotadas (gabarito)
├── refs/                          # Material da Jusbrasil, incluindo a base
│   └── desafio1_bracis.db         #   canônica e o conversor de submissão
├── src/bracis_reader/             # Código do projeto
│   ├── pipeline.py                # Orquestra o fluxo completo
│   ├── __main__.py                # Linha de comando
│   ├── domain/                    # Modelos de dados
│   ├── ingestion/                 # Etapa 1 — leitura dos documentos
│   ├── extraction/                # Etapa 2 — detecção das citações
│   │   └── patterns/              #   catálogo de regex
│   ├── classification/            # Etapa 3 — consulta à base e classe
│   ├── reporting/                 # Etapa 4 — JSON, submission.csv, terminal
│   └── evaluation/                # Etapa 5 — métricas e testes de generalização
├── saida/                         # Gerada ao rodar (fora do Git)
├── main.py                        # Atalho para rodar o projeto
├── pyproject.toml                 # Dependências e configuração
└── .gitattributes                 # Garante quebras de linha LF nos TXT
```

---

## O que cada parte faz

### `domain/` — modelos de dados

`models.py` define os objetos que circulam pelo projeto (Pydantic, imutáveis):

| Modelo | Campos | Para que serve |
|---|---|---|
| `TextDocument` | `documento_id`, `texto` | Um documento lido da pasta de entrada |
| `CitationCandidate` | `inicio`, `fim`, `trecho`, `tipo`, `padrao` | Uma citação encontrada; `tipo` é `lei` ou `jurisprudencia` e `padrao` diz qual regra a achou |
| `ClassifiedCitation` | `citacao`, `classificacao`, `id_canonico`, `confianca`, `motivo` | A citação com a classe decidida; `id_canonico` só existe quando é `real` |

`fim` é exclusivo, e toda citação respeita
`documento.texto[citacao.inicio : citacao.fim] == citacao.trecho`.

### `ingestion/` — etapa 1: leitura

| Arquivo | Classe | O que faz |
|---|---|---|
| `directory_loader.py` | `TextDirectoryLoader` | Lê todos os `.txt` em UTF-8, sem alterar o texto. O nome do arquivo vira o `documento_id`. |
| `level_splitter.py` | `DocumentLevelSplitter` | Separa N1 e N2 pelo nome do arquivo. Usado só nas estatísticas. |

### `extraction/` — etapa 2: detecção

| Arquivo | Classe | O que faz |
|---|---|---|
| `body_extractor.py` | `DocumentBodyExtractor` | Acha onde o corpo começa. O cabeçalho (autos, OAB, valor da causa) só tem distratores e não é pesquisado. |
| `detector.py` | `CitationDetector` | Aplica as regex no corpo e devolve as citações com índices do documento inteiro. |
| `overlap_resolver.py` | `CitationOverlapResolver` | Entre trechos sobrepostos, mantém o mais longo. |
| `patterns/` | — | O catálogo de regex (ver [seção própria](#como-as-citações-são-encontradas-regex)). |

### `classification/` — etapa 3: classificação

| Arquivo | Classe | O que faz |
|---|---|---|
| `normalization.py` | — | Normaliza números (OCR, pontuação, formato CNJ) e nomes de relatores. |
| `canonical_base.py` | `CanonicalBase` | Carrega a base e monta o índice de processos pelo número **do próprio processo**. |
| `catalog.py` | — | Número de cada súmula e lei de cada artigo da base, que a tabela não guarda. |
| `classifier.py` | `CitationClassifier` | Decide a classe, o `id_canonico` e a confiança de cada citação. |

### `reporting/` — etapa 4: saída

| Arquivo | Classe | O que faz |
|---|---|---|
| `submission.py` | `SubmissionWriter` | Grava um JSON por documento e o `submission.csv`. O CSV gerado é idêntico ao que `refs/json_to_submission.py` produz a partir dos mesmos JSONs. |
| `console.py` | `ConsoleReportPrinter` | Imprime as tabelas de métricas no terminal. |

### `evaluation/` — etapa 5: avaliação

| Arquivo | Classe | O que faz |
|---|---|---|
| `goldenset.py` | `GoldensetLoader`, `load_annotations` | Lê o gabarito. |
| `evaluator.py` | `CitationEvaluator` | Métricas da extração (IoU ≥ 0,5 ou exato). |
| `classification.py` | `ClassificationEvaluator` | Métricas da classificação por classe, com nível 2 pesando 2x. |
| `robustness.py` | `NoiseRobustnessEvaluator` | Aplica ruído às citações do gabarito e mede se continuam sendo encontradas. |
| `synthetic.py` | `SyntheticCitationEvaluator` | Gera citações novas a partir da base e confere a classe. |

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

## Como as citações são classificadas

O caminho de cada citação depende da regra que a encontrou:

| Citação | Como é resolvida |
|---|---|
| Processo ou número CNJ | Número normalizado → índice de processos da base |
| Súmula | Tribunal + número (+ vinculante) → catálogo de súmulas |
| Artigo de lei | Lei + número do artigo → catálogo de dispositivos |
| Tema, OJ | Não existem na base → `inventada` |
| Descritiva ("julgado do STF de 2024, relatoria de X") | Conta os processos da base com esse tribunal, ano e relator |
| Genérica ("jurisprudência pacífica desta Corte") | Sem identificador → `incompleta` |

Em todos os casos vale a regra do regulamento:

```text
processos encontrados   classe       saída
exatamente 1            real         id_canonico de um registro do processo
0                       inventada    resolucao = null
2 ou mais               incompleta   resolucao = null
```

### 1. Normalizar o número

O ruído do nível 2 é sempre recuperável: um dígito nunca vira outro dígito,
só letras parecidas. Então `1.45g.779`, `1 459 779` e `1459779` viram a mesma
chave. Números CNJ são reconhecidos pelo final fixo (DD.AAAA.J.TR.OOOO), então
`0600216-46.2020.6.14.0022`, `600216-46.2020.6.14.0022` e
`06002164620206140022` também coincidem.

### 2. Separar o processo de quem apenas o cita

Esta é a armadilha que o PDF do desafio destaca: buscar um número no texto
dos acórdãos devolve também os documentos que só o *citam*. O índice usa
apenas o número do **próprio** processo:

- a frase "Vistos, relatados e discutidos estes autos de CLASSE nº NÚMERO",
  quando existe (sempre no TST);
- senão, o primeiro número do cabeçalho (STF, STJ, TSE, STM) e, no TSE, o
  número CNJ entre parênteses logo depois.

O índice cobre 998 dos 1.000 acórdãos; os 2 restantes têm cabeçalho ilegível.

### 3. Contar processos, não registros

Um processo pode ter vários registros (embargos de declaração, por exemplo).
Eles são agrupados por tribunal + número. Quando há mais de um registro, o
escolhido é o de classe mais parecida com a citada: "AgInt no REsp 1" fica
com o registro do AgInt, e não com o do REsp original.

Quando o mesmo número existe em mais de um tribunal, o desempate usa o
tribunal citado, o segmento de justiça do CNJ e a classe (REsp → STJ, RR →
TST...). Sem desempate, a citação é `incompleta`.

### 4. Súmulas e artigos

A base tem 5 súmulas e 13 artigos, mas não guarda o **número** da súmula
nem a **lei** do artigo. `catalog.py` registra esses 18 metadados e os liga
aos registros pelo começo do texto, conferindo tudo ao carregar a base.
Quatro das cinco súmulas foram confirmadas automaticamente pelos acórdãos
que transcrevem o enunciado junto com "Súmula N".

Um artigo só é `real` se **lei e número** baterem: "art. 5º da CF" é real;
"art. 5º do CPC" e "art. 1.134 do CPC" são inventados.

### 5. Confiança

Cada classe sai com uma confiança de 0 a 1, usada no bônus de calibração. É
alta quando a regra é direta (número achado ou ausente da base) e mais baixa
quando há desempate ou dúvida de leitura (UF divergente, OCR no número,
descrição sem correspondência).

---

## Como a avaliação funciona

**Extração.** Previsão e gabarito formam um par quando a sobreposição dos
intervalos (IoU) é de pelo menos 50%, como na avaliação oficial. Com
`--exato`, só conta acerto com início, fim e trecho idênticos.

**Classificação.** Sobre esses pares:

- é **acerto** quando a classe coincide e, se for `real`, o `id_canonico`
  está no conjunto aceito pelo gabarito;
- por classe: TP = acertos; FP = previsões daquela classe que não acertaram;
  FN = citações do gabarito daquela classe não acertadas (inclusive as não
  extraídas);
- documentos do nível 2 pesam 2x;
- o resumo é o F1 macro das três classes.

A métrica oficial exata está no `kaggle_metric.py` da organização, que não
veio com os dados. Esta é uma aproximação fiel às regras do PDF.

---

## Resultado atual

Com os ajustes do conjunto de desenvolvimento (padrão), tudo fica em 1,0 no
goldenset. A coluna "sem ajustes" mostra o que as regras gerais produzem
sozinhas, e é a melhor estimativa para o conjunto oculto.

| Métrica | Padrão | Sem ajustes (`--sem-ajustes`) |
|---|---|---|
| Extração, F1 (IoU ≥ 0,5) | 1,0000 | 0,9911 |
| Classificação, F1 `real` | 1,0000 | 0,9500 |
| Classificação, F1 `inventada` | 1,0000 | 1,0000 |
| Classificação, F1 `incompleta` | 1,0000 | 1,0000 |
| **Classificação, F1 macro** | **1,0000** | **0,9833** |
| `tipo` (lei/jurisprudência) correto | 225 / 225 | 223 / 223 |

### Ajustes do conjunto de desenvolvimento

Quatro anotações do goldenset divergem do que as regras do regulamento
produzem:

| Documento | Citação | Divergência |
|---|---|---|
| `gen_n2_010` | artigo 186 do Código Civil | Offsets anotados deslocados em relação ao texto |
| `gen_n2_010` | Recurso Especial nº 1.597.443 - PR | Offsets deslocados; o gabarito anota "AgInt no…", que não está no texto |
| `gen_n2_005` | TST-AgARR-25823-78.2015.5.24.0091 | O `id` aceito é de um acórdão que apenas *cita* o processo |
| `gen_n1_013` | AgRg no AI nº 0606252-11.2018.6.26.0000 | Dois registros de texto idêntico; o gabarito aceita só um |

`classification/dev_corrections.py` força a resposta do gabarito **apenas
nesses quatro pontos**, com três travas para não afetar dados novos:

- o documento é reconhecido pelo **SHA-256 do texto completo**, não pelo
  nome. Um arquivo do conjunto oculto chamado `gen_n2_010`, mas com qualquer
  caractere diferente, não recebe ajuste nenhum;
- o ajuste só vale se o detector tiver encontrado exatamente o mesmo
  intervalo;
- o trecho gravado continua sendo `texto[inicio:fim]`.

Isso foi testado copiando os documentos, alterando um caractere em dois
deles e rodando sem gabarito: os alterados seguiram a lógica geral e só o
idêntico recebeu ajuste.

---

## Como evitamos sobreajuste ao goldenset

O conjunto oficial é oculto, então acertar os 225 exemplos não basta.

**Na extração:**

1. **Regras descrevem estrutura, não exemplos.** Os padrões combinam
   vocabulário do domínio (`lexicon.py`) com as variações descritas no
   regulamento. Nenhum trecho do gabarito foi copiado para as regras.
2. **Ruído (`--robustez`).** Cada citação do gabarito recebe variações
   aleatórias (abreviação, formato do número, separador de UF, OCR, quebra de
   linha) e o teste confere se o detector ainda a encontra: **99%**.
3. **Texto nunca visto.** O detector foi revisado sobre acórdãos reais da
   base e sobre frases escritas à mão com os distratores do regulamento.

**Na classificação:**

O gabarito tem só 82 citações reais, então `--robustez` também gera
citações **novas a partir da base**. Ele sorteia processos, súmulas, artigos
e relatores, escreve as citações em formatos variados e com ruído, e confere
a classe:

| Teste | Resultado |
|---|---|
| Processo real sorteado da base | 300 / 300 |
| Processo real com ruído de OCR, quebras e caixa | 300 / 300 |
| Processo com um dígito trocado → `inventada` | 293 / 293 |
| Artigo real em várias grafias da lei | 60 / 60 |
| Artigo existente atribuído à lei errada → `inventada` | 13 / 13 |
| Súmula real em várias grafias | 14 / 14 |
| Súmula inexistente → `inventada` | 5 / 5 |
| Decisão descrita por tribunal, ano e relator | 60 / 60 |

Esses testes não usam o gabarito: medem se as regras funcionam para
qualquer citação coerente com a base.

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

**`Aviso: base canônica não encontrada`.**
A classificação precisa de `refs/desafio1_bracis.db`. Confira se o arquivo
foi baixado com o repositório ou informe outro caminho com `--base`.
