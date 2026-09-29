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
5. [Arquitetura e princípios SOLID](#arquitetura-e-princípios-solid)
6. [Como as citações são encontradas (regex)](#como-as-citações-são-encontradas-regex)
7. [Como as citações são classificadas](#como-as-citações-são-classificadas)
8. [Como a avaliação funciona](#como-a-avaliação-funciona)
9. [Resultado atual](#resultado-atual)
10. [Como evitamos sobreajuste ao goldenset](#como-evitamos-sobreajuste-ao-goldenset)
11. [Problemas comuns](#problemas-comuns)

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

Tudo é coordenado por `application.py`, montado em `bootstrap.py`. Sem gabarito (caso do conjunto oculto),
as etapas 1 a 4 rodam normalmente e a avaliação é pulada.

---

## Como rodar

Requisitos: **Python 3.11+** e **Git**. A base canônica atual do Kaggle fica em
`data/kaggle/desafio1_bracis.db` (90 MB); a versão original, em
`refs/desafio1_bracis.db`.

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
python -m bracis_reader --kaggle --txt caminho/dos/txt --sem-gabarito --confianca-maxima --saida resultado
```

Gera `resultado/json/<documento_id>.json` e `resultado/submission.csv`.

| Opção | O que faz |
|---|---|
| `--kaggle` | Usa os textos, o gabarito e a base atuais do Kaggle (`data/kaggle/`) em vez dos originais |
| `--txt PASTA` | Pasta dos documentos (padrão: `data/txt`) |
| `--gold CSV` | Gabarito (padrão: `data/goldenset.csv`) |
| `--sem-gabarito` | Não avalia; só extrai, classifica e grava |
| `--base DB` | Base canônica (padrão: `refs/desafio1_bracis.db`; com `--kaggle`, `data/kaggle/desafio1_bracis.db`) |
| `--saida PASTA` | Onde gravar `json/` e `submission.csv` (padrão: `saida`) |
| `--exato` | Avalia a extração por igualdade exata (padrão: IoU ≥ 0,5, como na avaliação oficial) |
| `--robustez` | Roda os testes de generalização (ver [Como evitamos sobreajuste](#como-evitamos-sobreajuste-ao-goldenset)) |
| `--calibrar` | Mostra a taxa de acerto de cada regra de classificação, usada para calibrar a confiança |
| `--genericas` | Também extrai alusões genéricas ("jurisprudência pacífica desta Corte"), que o gabarito oficial não anota |
| `--confianca-maxima` | Envia confiança 1,0 em todas as citações. Com tudo certo, o bônus de calibração chega aos 10% exatos (nota 1,10000 no desenvolvimento) |

### 4. Lint

```bash
ruff check .    # verifica estilo e imports
```

---

## Estrutura de pastas

```text
.
├── data/
│   ├── txt/                       # 26 peças jurídicas originais (13 N1 + 13 N2)
│   ├── goldenset.csv              # Gabarito original (225 citações)
│   └── kaggle/                    # Versão atual do Kaggle, usada na submissão
│       ├── txt/                   #   4 documentos corrigidos pela organização
│       ├── goldenset.csv          #   goldenset_offsets.csv (192 citações)
│       └── desafio1_bracis.db     #   base atual (1.014 registros)
├── refs/                          # Material da Jusbrasil, incluindo a base
│   └── desafio1_bracis.db         #   canônica e o conversor de submissão
├── src/bracis_reader/             # Código do projeto
│   ├── cli.py                     # Linha de comando -> Settings
│   ├── settings.py                # Configuração resolvida da execução
│   ├── bootstrap.py               # Monta as implementações (raiz de composição)
│   ├── application.py             # Caso de uso: ler, processar, avaliar, gravar
│   ├── pipeline.py                # Extração + classificação, sem E/S
│   ├── diagnostics.py             # Calibração e testes de robustez
│   ├── domain/                    # Modelos e contratos (ports.py)
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
| `catalog.py` | — | Lista de reserva de súmulas e artigos, usada só na base antiga, que não tem títulos. |
| `canonical_catalog.py` | `CanonicalCatalog` | Índices de súmulas e artigos pelo título do registro. |
| `legal_text.py` | — | Normalização de texto e reconhecimento do tribunal citado. |
| `resolvers/` | `ProcessNumberResolver`, `SumulaResolver`, `ArticleResolver`, `DescriptionResolver`, ... | Uma estratégia de decisão por padrão de citação. |
| `confidence.py` | `CalibratedConfidence`, `FixedConfidence` | Políticas de confiança por regra. |
| `classifier.py` | `CitationClassifier` | Encaminha cada citação ao resolvedor do seu padrão e aplica a política de confiança. |

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
| `service.py` | `GoldensetEvaluationService` | Reúne as métricas de extração, classificação e a nota oficial. |
| `classification.py` | `ClassificationEvaluator` | Métricas da classificação por classe, com nível 2 pesando 2x. |
| `robustness.py` | `NoiseRobustnessEvaluator` | Aplica ruído às citações do gabarito e mede se continuam sendo encontradas. |
| `synthetic.py` | `SyntheticCitationEvaluator` | Gera citações novas a partir da base e confere a classe. |

---

## Arquitetura e princípios SOLID

```text
cli.py ──▶ Settings ──▶ bootstrap.build() ──▶ CitationExtractionApplication
                                                 │
            DocumentSource ◀─────────────────────┤  (TextDirectoryLoader)
            CitationPipeline ◀───────────────────┤
              ├─ CitationExtractor               │  (CitationDetector)
              └─ CitationClassifierPort          │  (CitationClassifier)
                   ├─ resolvers por padrão       │
                   └─ ConfidencePolicy           │
            GoldensetEvaluationService ◀─────────┤  (só com gabarito)
            ResultWriter ◀───────────────────────┘  (SubmissionWriter)
```

| Princípio | Onde aparece |
|---|---|
| **S** — responsabilidade única | `cli.py` só lê argumentos; `bootstrap.py` só monta objetos; `pipeline.py` só extrai e classifica; `evaluation/service.py` só mede; `diagnostics.py` só roda os relatórios auxiliares. No classificador, cada tipo de citação tem o seu resolvedor e os índices de súmulas/artigos ficam em `CanonicalCatalog`. |
| **O** — aberto/fechado | Um novo tipo de citação entra registrando outro resolvedor em `default_resolvers`, sem alterar `CitationClassifier`. Uma nova forma de calcular confiança é outra `ConfidencePolicy`. |
| **L** — substituição | Todo resolvedor devolve uma `Resolution` com o mesmo contrato; `CalibratedConfidence` e `FixedConfidence` são intercambiáveis. `--confianca-maxima` apenas troca a política, em vez de reescrever os resultados depois. |
| **I** — segregação de interfaces | `domain/ports.py` define contratos pequenos (`DocumentSource`, `CitationExtractor`, `CitationClassifierPort`, `ResultWriter`), e cada consumidor depende só do que usa. |
| **D** — inversão de dependência | `CitationExtractionApplication` e `CitationPipeline` recebem as dependências prontas e conhecem apenas os protocolos. `bootstrap.py` é o único lugar que escolhe as classes concretas. |

A refatoração não mudou o comportamento: os JSONs, o `submission.csv` e toda
a saída do terminal (inclusive `--robustez` e `--calibrar`) são idênticos
byte a byte aos da versão anterior, e a nota continua 1,10000.

Exemplo de uso como biblioteca, trocando uma peça sem tocar no resto:

```python
from bracis_reader.classification import CanonicalBase, CitationClassifier
from bracis_reader.classification.confidence import FixedConfidence
from bracis_reader.extraction import CitationDetector
from bracis_reader.ingestion import TextDirectoryLoader
from bracis_reader.pipeline import CitationPipeline

base = CanonicalBase("data/kaggle/desafio1_bracis.db")
classifier = CitationClassifier.from_base(base, FixedConfidence(1.0))
pipeline = CitationPipeline(CitationDetector(), classifier)
output = pipeline.process(TextDirectoryLoader("data/kaggle/txt").load())
```

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
- Também: **súmulas** (`Súmula 83 do STJ`, `Súm. 7/STJ`, `Súmula Vinculante 10`,
  `SV 10`, e na ordem inversa: `verbete nº 331 da Súmula do TST`),
  **temas** (`Tema 1.046 da repercussão geral`), **OJs** (`OJ 191 da SBDI-1`)
  e **números CNJ** soltos no corpo.

### Legislação (`legislation.py`)

```text
art./artigo NÚMERO [, § 1º | , I | , 'g' | , parágrafo único]... da|do LEI
```

**LEI** pode ser lei numerada (`Lei nº 13.105/2015`, `Lei 8.078, de 1990`),
qualquer "Código ..." (`Código de Defesa do Consumidor`, `Código Penal Militar`),
a Constituição (também "Carta Magna", "Lei Maior", `CRFB/88`), a CLT por
extenso, um estatuto ou uma sigla (`CPC`, `CF/88`, `LC 64/90`).

### Citações sem número (`incomplete.py`)

1. **Descritivas**, que dá para buscar na base por tribunal, ano e relator:

   ```text
   DECISÃO  +  pelo menos DOIS entre  TRIBUNAL · ANO · RELATOR  (em qualquer ordem)
   ```

   Ex.: "julgado do STF proferido em 2024 pela relatoria de Dias Toffoli",
   "Rcl de 2021, Rel. Min. Rosa Weber", "acórdão proferido pelo STJ em 2019,
   sob a relatoria do Min. X", "voto condutor do Ministro X no STF, em 2020".

   Com um detalhe só, a frase costuma não ser citação ("o voto do Ministro
   X", "julgado em 2018"). Por isso a regra exige dois. Assim ela não dispara
   em nenhum de 250 acórdãos reais da base, que citam sempre com número.

2. **Genéricas**, que só aludem a uma fonte. **Ficam desligadas por
   padrão**: o gabarito oficial do Kaggle só anota as incompletas descritivas,
   então prevê-las vira falso positivo. Para ligar: `--genericas`.

   Quando ligadas, para contar como citação a
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

A base tem 5 súmulas e 13 artigos. Na versão atual, cada registro começa com
um título ("Súmula n. 83 do STJ", "Artigo 276 da Lei nº 4.737, de 15 de julho
de 1965"). O catálogo é montado **lendo esses títulos**: número, tribunal e
lei saem da própria base. A base original não tinha títulos; para ela,
`catalog.py` guarda uma lista de reserva que liga cada registro pelo começo
do texto.

Um artigo só é `real` se **lei e número** baterem: "art. 5º da CF" é real;
"art. 5º do CPC" e "art. 1.134 do CPC" são inventados.

### 5. Confiança

A métrica oficial dá um bônus de até 10% pelo Brier da confiança sobre as
citações pareadas: `score = s · (1 + 0,10 · (1 − Brier))`. O Brier é mínimo
quando a confiança é igual à taxa real de acerto.

Cada citação sai marcada com a **regra** que a classificou
(`processo_real`, `sumula_inventada`, `descricao_varios`...), e a confiança é
a taxa de acerto medida para aquela regra, encolhida em direção à taxa geral
do sistema (estimativa bayesiana empírica):

```text
confiança = (acertos + 2 · taxa_geral) / (total + 2)
```

Assim, uma regra com poucas amostras herda a taxa geral (99,7%), em vez de
cair para perto de 50% como aconteceria com a suavização de Laplace. A tabela
fica em `classification/confidence.py`, medida sobre 689 citações: o
gabarito oficial e dois lotes de teste na mesma política de anotação. Para
recalcular com outro conjunto:

```bash
python -m bracis_reader --txt PASTA --gold CSV --calibrar
```

---

## Como a avaliação funciona

`python main.py` imprime três blocos:

1. **Extração:** pareamento por IoU ≥ 0,5 (com `--exato`, só igualdade
   exata de início, fim e trecho).
2. **Classificação:** F1 por classe, com nível 2 pesando 2x.
3. **Nota oficial:** a mesma fórmula do `kaggle_metric.py` da organização,
   reimplementada em `evaluation/official.py` e conferida contra o script
   original, com resultado idêntico:
   - macro-F1 das classes por nível; a classe `real` só conta com o
     `id_canonico` aceito;
   - classe errada custa duas vezes (FN da esperada e FP da predita); id
     errado em `real` custa só FP;
   - predição sem par é FP, a menos que esteja ≥ 90% contida numa citação
     já pareada;
   - penalidade `s = macroF1 · (1 − 0,5 · τ)`, com τ = fração das
     inventadas preditas como real;
   - bônus de calibração de até 10% (Brier);
   - nota final `(N1 + 2 · N2) / 3`; o máximo é **1,1**.

---

## Resultado atual

`data/` guarda duas versões do conjunto de desenvolvimento:

- `data/txt` e `data/goldenset.csv`: os arquivos originais do repositório;
- `data/kaggle/`: a versão atual publicada no Kaggle, que é a usada pelo
  placar. Nela, 4 documentos foram corrigidos pela organização e o gabarito
  (`goldenset_offsets.csv`, 192 citações) não anota alusões genéricas.

A submissão do Kaggle deve ser gerada com `--kaggle`:

```bash
python main.py --kaggle --confianca-maxima
```

Resultados sobre `data/kaggle`, só com as regras (sem nenhum ajuste manual):

| Métrica | Resultado |
|---|---|
| Extração (IoU ≥ 0,5) | 192 / 192 |
| F1 `real` / `inventada` / `incompleta` | 1,00 / 1,00 / 1,00 |
| `tipo` (lei/jurisprudência) correto | 192 / 192 |
| **Nota oficial (máximo 1,1)** | **1,10000** |

Com a confiança calibrada, a nota exata fica um pouco abaixo de 1,1 (o bônus
depende de a confiança ser exatamente 1 nos acertos). Com `--confianca-maxima`,
chega a **1,1000000000**. No conjunto final a diferença entre as duas opções
é desprezível.

A base atual removeu 4 registros duplicados da versão original (`doc_0227`,
`doc_0461`, `doc_0657`, `doc_0662`). Com ela, o processo TSE
0606252-11.2018.6.26.0000 passa a ter um único registro, e a resposta das
regras coincide com o gabarito.

---

## Como evitamos sobreajuste ao goldenset

O conjunto final é cego, então acertar os 192 exemplos não basta.

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

**Lotes de documentos novos (fora do repositório):**

Foram gerados dois lotes de 30 documentos (15 N1 + 15 N2) no estilo do
desafio, com gabarito próprio: cabeçalho com distratores, citações reais
sorteadas da base, inventadas, descritivas e genéricas, e ruído no nível 2.

- **Lote A** expôs lacunas de redação: "proferido **pelo** STJ", "verbete nº
  331 da Súmula do TST", "Carta Magna", OCR "m→rn" na classificação. As
  regras foram corrigidas de forma genérica, sem copiar frases do lote.
- **Lote B** foi escrito **antes** dessas correções, com outra semente e
  outras redações, e rodado uma única vez no fim, como teste cego.

| | Extração F1 | Falsos positivos | Classificação F1 macro |
|---|---|---|---|
| Lote A, antes das correções | 0,9301 | 0 | 0,8583 |
| Lote A, depois | 0,9982 | 0 | 0,9978 |
| **Lote B (cego)** | **0,9947** | **0** | **0,9942** |

Com a política de anotação do gabarito oficial (sem alusões genéricas) e a
métrica oficial, o lote A fica em **1,0978** e o lote B em **1,0953**, de um
máximo de 1,1.

Os lotes foram escritos pela mesma pessoa que escreveu as regras, então
medem variações previstas por ela; um lote escrito por outra pessoa da
equipe seria um teste ainda mais independente.

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
A classificação precisa da base canônica (`refs/desafio1_bracis.db` ou, com
`--kaggle`, `data/kaggle/desafio1_bracis.db`). Confira se o arquivo foi
baixado com o repositório ou informe outro caminho com `--base`.
