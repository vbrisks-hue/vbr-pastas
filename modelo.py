"""
Modelo de pastas da VB Risk.

Este é o único arquivo que precisa mudar quando o modelo mudar.
Tudo que o programa cria e tudo que ele audita sai daqui.

Quatro espécies de árvore:
  ORIGINACAO  pré-mandato; mora no funil e, depois de assinado, no grupo
  FRENTE      trabalho temporário sob mandato e plano de trabalho
  ACERVO      permanente, do ativo
  APOLICES    permanente, por ramo -> VIGENTE / HISTORICO / SINISTROS

A frente mora no nível do seu escopo: frente de um ativo fica sob o ativo,
frente que atravessa ativos fica sob o cliente.

A originação mora fora de CLIENTES enquanto não há mandato, e muda de lugar
quando o contrato assina. Veja o bloco ORIGINAÇÃO logo abaixo.
"""

import re
import unicodedata
from datetime import date

# ---------------------------------------------------------------------------
# Grafia da casa: hífen, maiúsculas, sem acento.
# ---------------------------------------------------------------------------

# Trocas que precisam acontecer ANTES de tirar acento, porque o caractere
# não é uma letra acentuada e sim um símbolo.
TROCAS = {
    "&": "-",
    "/": "-",
    "\\": "-",
    "+": "-",
}


def normalizar(nome: str) -> str:
    """
    Converte um nome livre para a grafia da casa.

        'Renovação Apólices'  -> 'RENOVACAO-APOLICES'
        'D&O'                 -> 'D-O'
        '  Pecem I  '         -> 'PECEM-I'
        'RC Geral'            -> 'RC-GERAL'

    Espaço no começo ou no fim é o erro mais comum do Drive e some aqui.
    """
    if nome is None:
        return ""
    texto = nome.strip()
    for de, para in TROCAS.items():
        texto = texto.replace(de, para)
    # NFKD separa a letra do acento; o filtro joga o acento fora.
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = texto.upper()
    # Qualquer corrida de espaço, ponto ou underscore vira um hífen só.
    texto = re.sub(r"[\s._]+", "-", texto)
    # Sobra só letra, número e hífen.
    texto = re.sub(r"[^A-Z0-9-]", "", texto)
    # Hífens repetidos ou nas pontas somem.
    texto = re.sub(r"-{2,}", "-", texto).strip("-")
    return texto


def esta_na_grafia(nome: str) -> bool:
    """True se o nome já está exatamente na grafia da casa."""
    return nome == normalizar(nome)


# Nomes datados: AAAA-MM_TITULO. Vale para frente e para originação — nos dois
# casos a competência é quando o trabalho COMEÇOU, não quando a pasta foi
# criada. É o que faz a lista ordenar por idade sozinha.
PADRAO_DATADO = re.compile(r"^(\d{4})-(\d{2})_([A-Z0-9-]+)$")


def _nome_datado(competencia: str, titulo: str) -> str:
    competencia = competencia.strip()
    if not re.fullmatch(r"\d{4}-\d{2}", competencia):
        raise ValueError(
            f"competência inválida: {competencia!r} — use AAAA-MM, por exemplo 2026-07"
        )
    return f"{competencia}_{normalizar(titulo)}"


def titulo_de(nome_datado: str) -> str:
    """
    O título sem a data: '2026-03_CVCP' -> 'CVCP'.

    Um nome que não é datado volta normalizado, para o chamador não precisar
    saber de qual dos dois formatos veio.
    """
    casamento = PADRAO_DATADO.fullmatch(nome_datado.strip())
    return casamento.group(3) if casamento else normalizar(nome_datado)


# ---------------------------------------------------------------------------
# ORIGINAÇÃO — o funil.
#
# Originação NÃO mora dentro de CLIENTES. Mora numa raiz própria, irmã dela:
#
#     GESTÃO DE RISCOS/
#     ├── CLIENTES/      só quem tem mandato
#     └── ORIGINACAO/    o funil, mais ZZ-ENCERRADAS
#
# O motivo é aritmético. No AVRA há 11 projetos em 'origination' contra 1
# 'active': se cada originação virasse pasta em CLIENTES, onze de doze pastas
# de cliente não seriam de cliente, e a palavra CLIENTES pararia de significar
# alguma coisa — para quem olha, para quem dá permissão e para qualquer
# contagem.
#
# Quando o contrato assina, a pasta MUDA DE LUGAR: sai de ORIGINACAO, entra
# na pasta do cliente e passa a se chamar 00-ORIGINACAO. Move, não copia — os
# ids, os compartilhamentos e o histórico do Drive continuam os mesmos. É
# assim que 'a originação não se mexe' deixa de ser promessa e vira operação.
# ---------------------------------------------------------------------------

# O nome que a originação tem DEPOIS de promovida, dentro do cliente.
ORIGINACAO = "00-ORIGINACAO"

# A pasta raiz do funil e o depósito de quem não fechou.
ENCERRADAS = "ZZ-ENCERRADAS"

# O bilhete que fica dentro de uma originação encerrada, dizendo quando e por
# quê. Fica lá para sempre, inclusive depois de reabrir e de promover.
BILHETE_DE_ENCERRAMENTO = "_ENCERRAMENTO.txt"

# As seis. O eixo é o mesmo da frente — insumo, trabalho, entrega — porque a
# originação também é um trabalho com começo e fim; só não é uma frente, que
# é trabalho SOB mandato. A proposta é a entrega da originação.
#
# O que a forma anterior de quatro não resolvia: o material que o prospecto
# manda (apólices vigentes, sinistralidade, cadastro de bens) e a análise que
# sustenta a proposta caíam os dois dentro de 02-PROPOSTAS, junto da proposta.
ORIGINACAO_SUBPASTAS = [
    "01-CADASTRO-DO-CLIENTE",
    "02-INSUMOS-RECEBIDOS",
    "03-TRABALHOS",
    "04-PROPOSTAS",
    "05-CONTRATOS-E-ADENDOS",
    "06-COMUNICACOES",
]

# A forma de quatro, de antes de 16/09/2026. A auditoria a reconhece e sugere
# a renumeração em vez de acusar quatro erros — GRUPO-DIAMANTE ainda está
# assim, e não há pressa nenhuma para mudar.
ORIGINACAO_SUBPASTAS_ANTERIOR = [
    "01-CADASTRO-DO-CLIENTE",
    "02-PROPOSTAS",
    "03-CONTRATOS-E-ADENDOS",
    "04-COMUNICACOES",
]

# De qual nome antigo para qual novo, para a auditoria dizer o que renomear.
ORIGINACAO_RENUMERACAO = {
    "02-PROPOSTAS": "04-PROPOSTAS",
    "03-CONTRATOS-E-ADENDOS": "05-CONTRATOS-E-ADENDOS",
    "04-COMUNICACOES": "06-COMUNICACOES",
}

# Subpastas que nascem dentro de uma subpasta da originação.
ORIGINACAO_NETOS = {
    "01-CADASTRO-DO-CLIENTE": ["LOGOS"],
}


# ---------------------------------------------------------------------------
# ACERVO — nível do ativo. As cinco estão travadas.
# ---------------------------------------------------------------------------

ACERVO = "ACERVO"

ACERVO_SUBPASTAS = [
    "DOCUMENTACAO-TECNICA",
    "ENGENHARIA-E-INSPECOES",
    "CADASTRO-DE-VALORES",
    "CONTRATOS-DO-ATIVO",
    "PLANTAS-E-IMAGENS",
]


# ---------------------------------------------------------------------------
# APÓLICES — nasce vazia nos dois níveis. Os ramos entram depois.
# ---------------------------------------------------------------------------

APOLICES = "APOLICES"

RAMO_SUBPASTAS = ["VIGENTE", "HISTORICO", "SINISTROS"]

# Os ramos que a casa usa. A lista serve de sugestão no terminal e de régua
# na auditoria — um ramo fora dela não é erro, só é sinalizado para conferência.
# Nomes que a casa já usou e trocou. A auditoria sugere o nome novo em vez
# de apenas dizer que o ramo é desconhecido.
RAMOS_RENOMEADOS = {
    "COMERCIAL": "EMPRESARIAL",   # compreensivo do escritório
    "D&O": "D-O",
    "GARANTIA": "GARANTIA-JUDICIAL ou GARANTIA-BID",
    "RC": "RCG",
    "RC-GERAL": "RCG",
    "RO": "RO-BI",
}

RAMOS_CONHECIDOS = [
    "RO-BI",            # riscos operacionais + lucros cessantes (a usina)
    "EMPRESARIAL",      # compreensivo do escritório
    "RCG",              # RC Geral, SUSEP 51
    "D-O",              # D&O
    "CYBER",
    "AMBIENTAL",
    "FROTA",
    "TRANSPORTES",
    "GARANTIA-JUDICIAL",  # ambiental, cível, trabalhista
    "GARANTIA-BID",       # bid bond de leilão
]


# ---------------------------------------------------------------------------
# FRENTES — o coração do pedido: cada necessidade tem sua forma de árvore.
#
# Para criar um tipo novo, acrescente uma entrada aqui. O terminal, a criação
# e a auditoria passam a conhecê-lo sem mais nenhuma alteração no código.
# ---------------------------------------------------------------------------

FRENTES = "FRENTES"

# As cinco formas do caderno v4 (14/09/2026). O começo é igual em todas —
# 01-INSUMOS, 02-TRABALHOS, 03-ENTREGAS — para preservar a memória muscular.
# O que é próprio do tipo entra depois. COMUNICACOES sempre fecha.
TIPOS_FRENTE = {
    "RENOVACAO": {
        "descricao": "renovação de apólice: cotar o mercado, comparar e emitir",
        "quando": "vencimento se aproximando, com cotação de mais de uma seguradora",
        "subpastas": [
            "01-INSUMOS",
            "02-TRABALHOS",
            "03-ENTREGAS",
            "04-COTACOES-RECEBIDAS",
            "05-ANALISE-COMPARATIVA",
            "06-DECISAO-E-EMISSAO",
            "07-COMUNICACOES",
        ],
    },
    "CONCORRENCIA": {
        "descricao": "seleção de fornecedor com propostas recebidas e avaliadas",
        "quando": "RFP de corretora, concorrência de seguradora",
        "subpastas": [
            "01-INSUMOS",
            "02-TRABALHOS",
            "03-ENTREGAS",
            "04-PROPOSTAS-RECEBIDAS",
            "05-ANALISE-COMPARATIVA",
            "06-DECISAO",
            "07-COMUNICACOES",
        ],
    },
    "ANALISE": {
        "descricao": "estudo ou diagnóstico que termina numa decisão",
        "quando": "remoção de apólice do quadro, unificação, diagnóstico de BI",
        "subpastas": [
            "01-INSUMOS",
            "02-TRABALHOS",
            "03-ENTREGAS",
            "04-DECISOES",
            "05-COMUNICACOES",
        ],
    },
    "VISITA-TECNICA": {
        "descricao": "visita de campo com relatório e recomendações",
        "quando": "vistoria de risco, visita técnica com as corretoras",
        # 04-REGISTRO-DE-CAMPO existe por um motivo concreto: o Form_Visita do
        # CTJL tem 59 vídeos e o do Pecém 29. Sem esse compartimento ficam
        # empilhados em 02-TRABALHOS junto com o roteiro e as listas de acesso.
        "subpastas": [
            "01-INSUMOS",
            "02-TRABALHOS",
            "03-ENTREGAS",
            "04-REGISTRO-DE-CAMPO",
            "05-RECOMENDACOES",
            "06-COMUNICACOES",
        ],
    },
    "SINISTRO": {
        "descricao": "condução de um sinistro, do aviso à indenização",
        "quando": "sinistro relevante que precisa de acompanhamento próprio",
        # A quantificação do prejuízo fica em 02-TRABALHOS, porque é trabalho
        # da casa. 04-REGULACAO é o que o regulador produz e pede.
        "subpastas": [
            "01-INSUMOS",
            "02-TRABALHOS",
            "03-ENTREGAS",
            "04-REGULACAO",
            "05-ENCERRAMENTO",
            "06-COMUNICACOES",
        ],
    },
}


def nome_de_frente(competencia: str, titulo: str) -> str:
    """
    Monta o nome da frente no padrão da casa: AAAA-MM_TITULO.

        ('2026-07', 'RFP Corretora') -> '2026-07_RFP-CORRETORA'

    A competência é quando a frente começou, não quando a pasta foi criada.
    """
    return _nome_datado(competencia, titulo)


PADRAO_NOME_FRENTE = PADRAO_DATADO


def competencia_de_hoje() -> str:
    hoje = date.today()
    return f"{hoje.year:04d}-{hoje.month:02d}"


def tipo_por_subpastas(subpastas: list[str]) -> str | None:
    """
    Descobre o tipo de uma frente existente olhando as subpastas que ela tem.
    Usado pela auditoria para achar frente fora de qualquer modelo.
    Devolve o nome do tipo, ou None se não bater com nenhum.
    """
    presentes = {s for s in subpastas}
    for tipo, spec in TIPOS_FRENTE.items():
        if set(spec["subpastas"]) == presentes:
            return tipo
    return None


def tipo_mais_proximo(subpastas: list[str]) -> tuple[str, set[str], set[str]]:
    """
    Para uma frente que não bate com nenhum tipo, devolve o tipo mais parecido
    e o que falta e o que sobra em relação a ele. Serve para a auditoria dizer
    'isto quase é uma RENOVACAO, só falta 04-COTACOES-RECEBIDAS'.
    """
    presentes = set(subpastas)
    # Começa em -infinito: uma frente sem nenhuma subpasta em comum com
    # tipo nenhum tira nota negativa em todos, e ainda assim precisa de
    # um vencedor para o relatório ter o que sugerir.
    melhor, melhor_nota = None, float("-inf")
    for tipo, spec in TIPOS_FRENTE.items():
        esperadas = set(spec["subpastas"])
        nota = len(presentes & esperadas) - len(presentes ^ esperadas) * 0.5
        if nota > melhor_nota:
            melhor, melhor_nota = tipo, nota
    esperadas = set(TIPOS_FRENTE[melhor]["subpastas"])
    return melhor, esperadas - presentes, presentes - esperadas


# ---------------------------------------------------------------------------
# Montagem da árvore: o plano que a criação executa e a auditoria confere.
# ---------------------------------------------------------------------------


def arvore_do_cliente(
    nome_cliente: str,
    ativos: list[str] | None = None,
    frentes_do_grupo: list[tuple[str, str]] | None = None,
    frentes_por_ativo: dict[str, list[tuple[str, str]]] | None = None,
    com_originacao: bool = True,
) -> dict:
    """
    Devolve a árvore inteira como dicionário aninhado {nome: {filhos}}.

    ativos              nomes livres, normalizados aqui dentro
    frentes_do_grupo    lista de (nome_da_frente_ja_montado, tipo)
    frentes_por_ativo   {nome_do_ativo_normalizado: [(nome_frente, tipo), ...]}

    Só existe cliente com mandato. Quem ainda não assinou não tem pasta aqui:
    tem pasta no funil, em ORIGINACAO. Passe com_originacao=False quando a
    originação vier de lá — nesse caso ela é MOVIDA para dentro, não criada.

    Nada aqui toca o Drive. É só a forma pretendida — o que permite
    imprimir o plano e conferir antes de criar qualquer coisa.
    """
    ativos = ativos or []
    frentes_do_grupo = frentes_do_grupo or []
    frentes_por_ativo = frentes_por_ativo or {}

    raiz: dict = {}

    if com_originacao:
        raiz[ORIGINACAO] = arvore_de_originacao()

    # APOLICES do grupo nasce vazia: os ramos entram quando houver apólice.
    raiz[APOLICES] = {}

    raiz[FRENTES] = {
        nome: {sub: {} for sub in TIPOS_FRENTE[tipo]["subpastas"]}
        for nome, tipo in frentes_do_grupo
    }

    for ativo_livre in ativos:
        ativo = normalizar(ativo_livre)
        raiz[ativo] = {
            ACERVO: {sub: {} for sub in ACERVO_SUBPASTAS},
            APOLICES: {},
            FRENTES: {
                nome: {sub: {} for sub in TIPOS_FRENTE[tipo]["subpastas"]}
                for nome, tipo in frentes_por_ativo.get(ativo, [])
            },
        }

    return {normalizar(nome_cliente): raiz}


def arvore_de_promocao(
    ativos: list[str] | None = None,
    frentes_do_grupo: list[tuple[str, str]] | None = None,
    frentes_por_ativo: dict[str, list[tuple[str, str]]] | None = None,
) -> dict:
    """
    O que falta acrescentar quando um prospecto vira cliente com mandato.

    Devolve só a parte que cresce — APOLICES e FRENTES do grupo, e cada ativo
    com seu acervo. A originação que já existe fica intacta: ela é o registro
    histórico do que houve antes do contrato, e permanece.
    """
    ativos = ativos or []
    frentes_do_grupo = frentes_do_grupo or []
    frentes_por_ativo = frentes_por_ativo or {}

    novo: dict = {
        APOLICES: {},
        FRENTES: {
            nome: {sub: {} for sub in TIPOS_FRENTE[tipo]["subpastas"]}
            for nome, tipo in frentes_do_grupo
        },
    }

    for ativo_livre in ativos:
        ativo = normalizar(ativo_livre)
        novo[ativo] = {
            ACERVO: {sub: {} for sub in ACERVO_SUBPASTAS},
            APOLICES: {},
            FRENTES: {
                nome: {sub: {} for sub in TIPOS_FRENTE[tipo]["subpastas"]}
                for nome, tipo in frentes_por_ativo.get(ativo, [])
            },
        }

    return novo


def nome_de_originacao(competencia: str, nome: str) -> str:
    """
    O nome da pasta no funil: AAAA-MM_NOME.

        ('2026-03', 'CVCP') -> '2026-03_CVCP'

    A competência é quando a conversa começou. Com ela no nome, a lista do
    funil ordena por idade sem nenhum trabalho — e uma originação parada há
    dezoito meses se denuncia sozinha.
    """
    return _nome_datado(competencia, nome)


def arvore_de_originacao() -> dict:
    """As subpastas de uma originação. Sem a pasta de cima: quem chama decide
    se o nome é '2026-03_CVCP' (no funil) ou '00-ORIGINACAO' (dentro do
    cliente, depois de promovida)."""
    return {
        sub: {neto: {} for neto in ORIGINACAO_NETOS.get(sub, [])}
        for sub in ORIGINACAO_SUBPASTAS
    }


def arvore_do_ramo(ramo: str) -> dict:
    """Um ramo de apólice e suas três subpastas."""
    return {normalizar(ramo): {sub: {} for sub in RAMO_SUBPASTAS}}


def contar(arvore: dict) -> int:
    """Quantas pastas esta árvore tem, contando todos os níveis."""
    return sum(1 + contar(filhos) for filhos in arvore.values())


def desenhar(arvore: dict, prefixo: str = "") -> list[str]:
    """Desenha a árvore em linhas, para imprimir o plano no terminal."""
    linhas = []
    itens = list(arvore.items())
    for i, (nome, filhos) in enumerate(itens):
        ultimo = i == len(itens) - 1
        linhas.append(f"{prefixo}{'└── ' if ultimo else '├── '}{nome}")
        linhas.extend(desenhar(filhos, prefixo + ("    " if ultimo else "│   ")))
    return linhas
