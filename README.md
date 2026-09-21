# Etapa 1 — Leitura dos documentos

Implementação simplificada da leitura e separação dos documentos do Challenge Jusbrasil × BRACIS 2026.

## Estrutura

```text
src/bracis_reader/
├── models.py
├── directory_loader.py
└── level_splitter.py
```

## Responsabilidades

### `TextDirectoryLoader`

- recebe o caminho da pasta `txt`;
- encontra todos os arquivos `.txt`;
- lê o conteúdo em UTF-8;
- utiliza o nome do arquivo como `documento_id`;
- devolve uma lista com todos os documentos.

### `DocumentLevelSplitter`

- recebe a lista carregada;
- identifica o nível pelo nome do arquivo;
- separa os documentos em duas listas;
- retorna primeiro N1 e depois N2.

## Utilização

```python
from bracis_reader import DocumentLevelSplitter, TextDirectoryLoader

loader = TextDirectoryLoader("data/txt")
documents = loader.load()

splitter = DocumentLevelSplitter()
documents_n1, documents_n2 = splitter.split(documents)
```

Resultado:

```python
documents_n1  # gen_n1_001, gen_n1_002, ...
documents_n2  # gen_n2_001, gen_n2_002, ...
```

## Fluxo

```text
Pasta txt
   ↓
TextDirectoryLoader.load()
   ↓
Lista com todos os documentos
   ↓
DocumentLevelSplitter.split()
   ↓
documents_n1 + documents_n2
```

## Instalação

```bash
python -m pip install -e ".[dev]"
```

## Execução

```bash
python main.py
```

## Testes e qualidade

```bash
pytest -q
ruff check .
ruff format --check .
```

O projeto continua seguindo PEP 8 e o princípio de responsabilidade única: uma classe carrega os arquivos e outra realiza a separação por nível.
