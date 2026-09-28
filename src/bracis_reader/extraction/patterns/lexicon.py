"""Vocabulário jurídico usado pelos padrões.

Tudo aqui é conhecimento de domínio (nomes de classes processuais, tribunais,
UFs, códigos), e não trechos copiados do goldenset. Para ampliar a cobertura,
basta acrescentar itens às listas.
"""

# Unidades da federação — sufixo usual dos números de processo ("/SP").
UFS = (
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG",
    "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE",
    "TO",
)  # fmt: skip

# Tribunais por sigla.
COURT_ACRONYMS = (
    "STF", "STJ", "TST", "TSE", "STM", "TNU", "CNJ",
    r"TRF\s?\d", r"TRT\s?\d{1,2}", r"TRE-?[A-Z]{2}", r"TJ[A-Z]{2}", "TJDFT",
)  # fmt: skip

# Tribunais por extenso e referências a órgãos julgadores.
COURT_NAMES = (
    "Supremo Tribunal Federal",
    "Superior Tribunal de Justiça",
    "Tribunal Superior do Trabalho",
    "Tribunal Superior Eleitoral",
    "Superior Tribunal Militar",
    "tribunais superiores",
    "Corte Superior",
    "Corte Especial",
    "Corte",
    "Casa",
    "Tribunal",
    "Plenário",
    "Pleno",
    "Seção",
    "Turma",
    "Câmara",
    "Primeira Turma",
    "Segunda Turma",
    "Terceira Turma",
    "Quarta Turma",
    "Quinta Turma",
    "Sexta Turma",
    "Primeira Seção",
    "Segunda Seção",
    "Terceira Seção",
    "Subseção",
    "SBDI-1",
    "SBDI-2",
    "SDI-1",
    "SDI-2",
)

# Classes processuais por extenso (tabela processual unificada do CNJ e
# nomenclatura usual dos tribunais superiores).
CLASS_NAMES = (
    "Recurso Especial Eleitoral",
    "Recurso Especial",
    "Recurso Extraordinário",
    "Recurso Ordinário Eleitoral",
    "Recurso Ordinário Trabalhista",
    "Recurso Ordinário",
    "Recurso em Habeas Corpus",
    "Recurso em Mandado de Segurança",
    "Recurso em Sentido Estrito",
    "Recurso de Revista",
    "Recurso de Embargos",
    "Recurso Inominado",
    "Agravo Interno",
    "Agravo Regimental",
    "Agravo de Instrumento",
    "Agravo em Recurso Especial",
    "Agravo em Recurso Extraordinário",
    "Agravo em Recurso Especial Eleitoral",
    "Agravo",
    "Embargos de Declaração",
    "Embargos de Divergência",
    "Embargos Infringentes e de Nulidade",
    "Embargos Infringentes",
    "Embargos",
    "Habeas Corpus",
    "Mandado de Segurança",
    "Mandado de Injunção",
    "Reclamação",
    "Apelação Criminal",
    "Apelação Cível",
    "Apelação",
    "Ação Rescisória",
    "Ação Direta de Inconstitucionalidade",
    "Ação Declaratória de Constitucionalidade",
    "Arguição de Descumprimento de Preceito Fundamental",
    "Ação Cautelar",
    "Ação Penal",
    "Cautelar Inominada Criminal",
    "Conflito de Competência",
    "Conflito de Jurisdição",
    "Suspensão de Liminar e de Sentença",
    "Suspensão de Liminar",
    "Suspensão de Segurança",
    "Tutela Cautelar Antecedente",
    "Revisão Criminal",
    "Correição Parcial",
    "Petição",
    "Questão de Ordem",
    "Inquérito",
    "Representação",
    "Ação de Investigação Judicial Eleitoral",
    "Ação de Impugnação de Mandato Eletivo",
    "Recurso contra Expedição de Diploma",
    "Registro de Candidatura",
    "Consulta",
    "Prestação de Contas",
)

# Siglas de classes processuais. As com até duas letras são tratadas com
# distinção de maiúsculas para não casar palavras comuns ("re", "ao").
CLASS_ACRONYMS = (
    "REsp", "RE", "AREsp", "ARE", "EREsp", "EAREsp", "REspe", "REspEl",
    "AREspE", "AREspEl", "AREspEI", "RESPE", "AgInt", "AgRg", "AgR", "AgReg",
    "Ag", "AI", "AIRR", "AgAIRR", "ARR", "AgARR", "RR", "RRAg", "RO", "ROT", "ReeNec",
    "EDcl", "ED", "EDs", "EDiv", "EI", "EInf", "E", "HC", "RHC", "MS", "RMS",
    "MI", "Rcl", "Recl", "RCL", "APL", "Ap", "ApCrim", "AR", "ADI", "ADC",
    "ADO", "ADPF", "AC", "AP", "CC", "CJ", "SLS", "SL", "SS", "Pet", "QO",
    "RSE", "Rp", "R-Rp", "RvC", "Inq", "TutCautAnt", "PExt",
)  # fmt: skip

# Nomes usuais de decisões, para citações descritivas ("julgado do STF").
DECISION_NOUNS = (
    "julgado",
    "julgados",
    "acórdão",
    "acórdãos",
    "aresto",
    "arestos",
    "precedente",
    "precedentes",
    "decisão",
    "decisão monocrática",
)

# Códigos e diplomas citados por sigla ("art. 373 do CPC").
LAW_ACRONYMS = (
    "CPC", "CPC/2015", "CPC/15", "CPC/73", "CPP", "CPM", "CPPM", "CLT", "CDC",
    "CTN", "CC", "CC/2002", "CF", "CF/88", "CF/1988", "ECA", "LINDB", "LEP",
    "CTB",
)  # fmt: skip
