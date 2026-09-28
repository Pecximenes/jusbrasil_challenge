"""Metadados das súmulas e dos dispositivos legais da base canônica.

A tabela ``documentos`` guarda o texto das 5 súmulas e dos 13 artigos, mas
não o *número* da súmula nem a *lei* a que o artigo pertence. Sem isso não
há como casar "Súmula 83 do STJ" ou "art. 373 do CPC" com um registro.

Como a base é congelada e pequena, o regulamento sugere carregar esses 18
registros em memória. Aqui eles são identificados pelo começo do texto (e
não pelo ``id``), e a correspondência é conferida ao carregar a base: se um
item não for encontrado, o carregamento falha em vez de classificar errado.

Quatro das cinco súmulas foram confirmadas automaticamente: nos acórdãos da
base, o enunciado transcrito aparece junto de "Súmula N". A Súmula 443 do STJ
não é transcrita em nenhum acórdão; seu número vem do enunciado oficial.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SumulaEntry:
    tribunal: str
    numero: int
    vinculante: bool
    inicio_do_texto: str


@dataclass(frozen=True)
class DispositivoEntry:
    lei: str
    artigo: int
    inicio_do_texto: str


SUMULAS = (
    SumulaEntry(
        "STJ", 83, False, "Não se conhece do recurso especial pela divergência"
    ),
    SumulaEntry("STJ", 211, False, "Inadmissível recurso especial quanto à questão"),
    SumulaEntry("STJ", 443, False, "O aumento na terceira fase de aplicação da pena"),
    SumulaEntry("STF", 10, True, "Viola a cláusula de reserva de plenário"),
    SumulaEntry("TST", 331, False, "CONTRATO DE PRESTAÇÃO DE SERVIÇOS. LEGALIDADE."),
)

# Siglas internas de cada diploma coberto pela base.
CPC, CC, CLT, CF, CPP, CPM, CDC, CE, LC64 = (
    "CPC", "CC", "CLT", "CF", "CPP", "CPM", "CDC", "CE", "LC64",
)  # fmt: skip

DISPOSITIVOS = (
    DispositivoEntry(CPC, 373, "Art. 373. O ônus da prova incumbe"),
    DispositivoEntry(CC, 186, "Art. 186. Aquele que, por ação ou omissão"),
    DispositivoEntry(CLT, 477, "Art. 477. Na extinção do contrato de trabalho"),
    DispositivoEntry(CLT, 818, "Art. 818. O ônus da prova incumbe"),
    DispositivoEntry(CLT, 896, "Art. 896 - Cabe Recurso de Revista"),
    DispositivoEntry(CF, 5, "Art. 5º Todos são iguais perante a lei"),
    DispositivoEntry(CF, 7, "Art. 7º São direitos dos trabalhadores"),
    DispositivoEntry(CF, 93, "Art. 93. Lei complementar, de iniciativa"),
    DispositivoEntry(CPP, 312, "Art. 312. A prisão preventiva"),
    DispositivoEntry(CPM, 290, "Art. 290. Receber, preparar, produzir"),
    DispositivoEntry(CDC, 14, "Art. 14. O fornecedor de serviços responde"),
    DispositivoEntry(CE, 276, "Art. 276. As decisões dos Tribunais Regionais"),
    DispositivoEntry(LC64, 1, "Art. 1º São inelegíveis"),
)

# Como cada diploma costuma ser citado. Aplicado ao texto sem acento e em
# minúsculas. "Lei Complementar 140/2011" não casa com LC 64, e um diploma
# fora da lista (ex.: Lei 9.504/1997) simplesmente não está na base.
LAW_PATTERNS: tuple[tuple[str, str], ...] = (
    (CPC, r"processo civil|\bn?cpc\b|13\.?105"),
    (CPP, r"processo penal|\bcpp\b|3\.?689"),
    (CPM, r"penal militar|\bcpm\b|decreto-lei\D{0,6}1\.?001\b"),
    (CDC, r"defesa do consumidor|\bcdc\b|8\.?078"),
    (CE, r"codigo eleitoral|4\.?737"),
    (LC64, r"complementar\D{0,8}\b64\b|\blc\D{0,4}\b64\b|inelegibilidades"),
    (CLT, r"consolidacao das leis do trabalho|\bclt\b|5\.?452"),
    (CF, r"constitui|\bcf\b|\bcrfb\b|carta (?:magna|da republica|politica)|lei maior"),
    (CC, r"codigo civil|\bcc\b|10\.?406"),
)
