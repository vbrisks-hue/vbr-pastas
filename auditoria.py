"""
Auditoria: compara a árvore que existe no Drive com o modelo da casa.

As regras aqui saíram de defeitos reais encontrados na migração de setembro
de 2026 — cada uma existe porque alguma coisa deu errado daquele jeito.

Nada aqui escreve no Drive. A auditoria só lê e relata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from modelo import (
    ACERVO,
    ACERVO_SUBPASTAS,
    APOLICES,
    BILHETE_DE_ENCERRAMENTO,
    ENCERRADAS,
    FRENTES,
    ORIGINACAO,
    ORIGINACAO_RENUMERACAO,
    ORIGINACAO_SUBPASTAS,
    ORIGINACAO_SUBPASTAS_ANTERIOR,
    PADRAO_NOME_FRENTE,
    RAMO_SUBPASTAS,
    RAMOS_CONHECIDOS,
    RAMOS_RENOMEADOS,
    TIPOS_FRENTE,
    esta_na_grafia,
    normalizar,
    tipo_mais_proximo,
    tipo_por_subpastas,
)

# Gravidade: ERRO foge do modelo, AVISO merece um olhar, NOTA é informação.
ERRO, AVISO, NOTA = "ERRO", "AVISO", "NOTA"

# Pastas que existem por convenção e não devem ser cobradas pelo modelo.
IGNORAR = {"__arquivos__"}


@dataclass
class Achado:
    gravidade: str
    caminho: str
    mensagem: str
    sugestao: str = ""


@dataclass
class Relatorio:
    achados: list[Achado] = field(default_factory=list)

    def add(self, gravidade, caminho, mensagem, sugestao=""):
        self.achados.append(Achado(gravidade, caminho, mensagem, sugestao))

    def por_gravidade(self, gravidade):
        return [a for a in self.achados if a.gravidade == gravidade]

    @property
    def erros(self):
        return self.por_gravidade(ERRO)

    @property
    def avisos(self):
        return self.por_gravidade(AVISO)

    @property
    def notas(self):
        return self.por_gravidade(NOTA)

    def limpo(self) -> bool:
        return not self.erros and not self.avisos


def _subpastas(no: dict) -> list[str]:
    return [k for k in no.keys() if k not in IGNORAR]


def _arquivos(no: dict) -> list[str]:
    return no.get("__arquivos__", [])


# ---------------------------------------------------------------------------
# Regras de nome
# ---------------------------------------------------------------------------


def checar_nome(rel: Relatorio, caminho: str, nome: str, eh_frente: bool = False):
    """
    Espaço no fim é invisível na tela do Drive e quebra qualquer busca por
    nome exato. Foi o que fez a pasta 'FRENTE CESSÃO BANCO ' e a '05-ANALISE '
    passarem despercebidas por meses.
    """
    if nome != nome.strip():
        rel.add(
            ERRO,
            caminho,
            f"nome com espaço no começo ou no fim: {nome!r}",
            f"renomear para {nome.strip()!r}",
        )
    if "  " in nome:
        rel.add(
            AVISO,
            caminho,
            f"nome com espaço duplo: {nome!r}",
            "reduzir para um espaço só",
        )
    # Frentes têm padrão próprio (AAAA-MM_TITULO), então a grafia da casa
    # só vale para a parte do título e é checada em checar_frente.
    if not eh_frente and not esta_na_grafia(nome):
        rel.add(
            AVISO,
            caminho,
            f"fora da grafia da casa: {nome!r}",
            f"a grafia seria {normalizar(nome)!r}",
        )


# ---------------------------------------------------------------------------
# Regras por espécie
# ---------------------------------------------------------------------------


def checar_conjunto(
    rel: Relatorio, caminho: str, presentes: list[str], esperadas: list[str], especie: str
):
    faltando = [e for e in esperadas if e not in presentes]
    sobrando = [p for p in presentes if p not in esperadas]
    for f in faltando:
        rel.add(ERRO, caminho, f"{especie} sem a subpasta {f}", f"criar {f}")
    for s in sobrando:
        rel.add(
            AVISO,
            caminho,
            f"{especie} com subpasta fora do modelo: {s}",
            "conferir se é conteúdo legado ou engano",
        )


def checar_originacao(rel: Relatorio, caminho: str, no: dict):
    presentes = _subpastas(no)

    # A forma de quatro é o modelo de antes de 16/09/2026, não um defeito.
    # Acusar quatro erros numa originação que está exatamente como foi
    # desenhada faria a auditoria perder a autoridade — o relatório só serve
    # enquanto tudo que está lá dentro merece ser lido.
    if set(presentes) == set(ORIGINACAO_SUBPASTAS_ANTERIOR):
        renomes = ", ".join(f"{de} -> {para}" for de, para in ORIGINACAO_RENUMERACAO.items())
        rel.add(
            NOTA,
            caminho,
            "originação no modelo anterior, de quatro subpastas",
            f"quando for conveniente: {renomes}; e criar 02-INSUMOS-RECEBIDOS "
            "e 03-TRABALHOS",
        )
    else:
        checar_conjunto(rel, caminho, presentes, ORIGINACAO_SUBPASTAS, "originação")

    # O bilhete de encerramento é posto aqui pelo próprio programa, e continua
    # aqui depois de reabrir e de promover — é a memória de por que a conversa
    # parou da outra vez. Uma regra que acusa a saída do próprio programa é
    # defeito da regra.
    soltos = [a for a in _arquivos(no) if a != BILHETE_DE_ENCERRAMENTO]
    if soltos:
        rel.add(
            AVISO,
            caminho,
            f"{len(soltos)} arquivo(s) solto(s) na raiz da originação",
            "mover para a subpasta numerada certa",
        )


def checar_acervo(rel: Relatorio, caminho: str, no: dict):
    checar_conjunto(rel, caminho, _subpastas(no), ACERVO_SUBPASTAS, "acervo")
    if _arquivos(no):
        rel.add(
            AVISO,
            caminho,
            f"{len(_arquivos(no))} arquivo(s) solto(s) na raiz do acervo",
            "mover para uma das cinco subpastas",
        )


def checar_apolices(rel: Relatorio, caminho: str, no: dict):
    """
    APOLICES pode estar vazia — nasce assim de propósito. O que se checa é
    cada ramo que exista: tem que ter as três subpastas, e nada mais.
    """
    if _arquivos(no):
        rel.add(
            AVISO,
            caminho,
            f"{len(_arquivos(no))} arquivo(s) solto(s) na raiz de APOLICES",
            "uma apólice mora em [RAMO]/VIGENTE, não na raiz",
        )
    for ramo in _subpastas(no):
        cam_ramo = f"{caminho}/{ramo}"
        checar_nome(rel, cam_ramo, ramo)
        if ramo not in RAMOS_CONHECIDOS:
            novo = RAMOS_RENOMEADOS.get(normalizar(ramo))
            if novo:
                rel.add(
                    ERRO,
                    cam_ramo,
                    f"ramo com o nome antigo: {ramo}",
                    f"a casa passou a chamar de {novo}",
                )
            else:
                rel.add(
                    NOTA,
                    cam_ramo,
                    f"ramo fora da lista da casa: {ramo}",
                    "conferir se é ramo novo ou nome divergente",
                )
        checar_conjunto(
            rel, cam_ramo, _subpastas(no[ramo]), RAMO_SUBPASTAS, f"ramo {ramo}"
        )
        if _arquivos(no[ramo]):
            rel.add(
                AVISO,
                cam_ramo,
                f"{len(_arquivos(no[ramo]))} arquivo(s) solto(s) na raiz do ramo",
                "mover para VIGENTE, HISTORICO ou SINISTROS",
            )


def checar_frente(rel: Relatorio, caminho: str, nome: str, no: dict):
    """
    Duas coisas: o nome segue AAAA-MM_TITULO, e as subpastas batem com algum
    tipo conhecido. Frente que não bate com tipo nenhum é o sintoma de
    estrutura montada à mão.
    """
    cam = f"{caminho}/{nome}"
    checar_nome(rel, cam, nome, eh_frente=True)

    casamento = PADRAO_NOME_FRENTE.fullmatch(nome.strip())
    if not casamento:
        rel.add(
            ERRO,
            cam,
            f"nome de frente fora do padrão: {nome!r}",
            "usar AAAA-MM_TITULO, por exemplo 2026-07_RENOVACAO-RO",
        )
    else:
        mes = int(casamento.group(2))
        if not 1 <= mes <= 12:
            rel.add(ERRO, cam, f"mês inválido no nome da frente: {mes:02d}")

    presentes = _subpastas(no)
    if not presentes:
        rel.add(NOTA, cam, "frente sem nenhuma subpasta", "conferir se foi criada agora")
        return

    tipo = tipo_por_subpastas(presentes)
    if tipo:
        rel.add(NOTA, cam, f"frente do tipo {tipo}")
    else:
        proximo, faltam, sobram = tipo_mais_proximo(presentes)
        detalhe = []
        if faltam:
            detalhe.append("falta " + ", ".join(sorted(faltam)))
        if sobram:
            detalhe.append("sobra " + ", ".join(sorted(sobram)))
        rel.add(
            AVISO,
            cam,
            f"frente não bate com nenhum tipo; mais próxima de {proximo} ({'; '.join(detalhe)})",
            f"alinhar com {proximo} ou registrar um tipo novo em modelo.py",
        )

    if _arquivos(no):
        rel.add(
            AVISO,
            cam,
            f"{len(_arquivos(no))} arquivo(s) solto(s) na raiz da frente",
            "mover para a subpasta numerada certa",
        )


def checar_frentes(rel: Relatorio, caminho: str, no: dict):
    for nome in _subpastas(no):
        checar_frente(rel, caminho, nome, no[nome])


def checar_ativo(rel: Relatorio, caminho: str, nome: str, no: dict):
    cam = f"{caminho}/{nome}"
    checar_nome(rel, cam, nome)

    presentes = _subpastas(no)
    for esperada in (ACERVO, APOLICES, FRENTES):
        if esperada not in presentes:
            rel.add(ERRO, cam, f"ativo sem a pasta {esperada}", f"criar {esperada}")

    if ACERVO in no:
        checar_acervo(rel, f"{cam}/{ACERVO}", no[ACERVO])
    if APOLICES in no:
        checar_apolices(rel, f"{cam}/{APOLICES}", no[APOLICES])
    if FRENTES in no:
        checar_frentes(rel, f"{cam}/{FRENTES}", no[FRENTES])

    # Compara normalizado: '00_ORIGINACAO', '00 Originação' e '00-ORIGINACAO'
    # são a mesma coisa para efeito desta regra.
    originacao_no_ativo = [
        p for p in presentes if normalizar(p) == normalizar(ORIGINACAO)
    ]
    for p in originacao_no_ativo:
        rel.add(
            ERRO,
            f"{cam}/{p}",
            "ativo com pasta de originação",
            "originação é do grupo, não do ativo — mover o conteúdo para cima",
        )

    for extra in presentes:
        if extra in (ACERVO, APOLICES, FRENTES) or extra in originacao_no_ativo:
            continue
        rel.add(AVISO, cam, f"pasta fora do modelo do ativo: {extra}")


# ---------------------------------------------------------------------------
# Duplicatas
# ---------------------------------------------------------------------------


def checar_duplicatas(rel: Relatorio, caminho: str, no: dict):
    """
    Dois filhos com o mesmo nome na mesma pasta. O Drive permite, e foi assim
    que quatro cópias do mesmo pacote de entrega conviveram lado a lado.
    """
    for lista, rotulo in ((_subpastas(no), "pasta"), (_arquivos(no), "arquivo")):
        vistos, repetidos = set(), set()
        for nome in lista:
            if nome in vistos:
                repetidos.add(nome)
            vistos.add(nome)
        for nome in sorted(repetidos):
            rel.add(
                AVISO,
                caminho,
                f"{rotulo} com nome repetido na mesma pasta: {nome!r}",
                "conferir qual é a boa antes de apagar a outra",
            )

    # Nome terminado em ' 2', ' 3'… é a assinatura de upload duplicado do Drive.
    for nome in _subpastas(no):
        partes = nome.rsplit(" ", 1)
        if len(partes) == 2 and partes[1].isdigit() and 2 <= int(partes[1]) <= 9:
            if partes[0] in _subpastas(no):
                rel.add(
                    AVISO,
                    f"{caminho}/{nome}",
                    f"parece cópia automática de {partes[0]!r}",
                    "o Drive numera assim ao subir o mesmo nome duas vezes; "
                    "a de número maior costuma ser a mais recente",
                )


def percorrer_duplicatas(rel: Relatorio, caminho: str, no: dict):
    checar_duplicatas(rel, caminho, no)
    for nome in _subpastas(no):
        percorrer_duplicatas(rel, f"{caminho}/{nome}", no[nome])


# ---------------------------------------------------------------------------
# Entrada
# ---------------------------------------------------------------------------


def auditar_cliente(nome_cliente: str, arvore: dict) -> Relatorio:
    """
    Audita a árvore de um cliente. `arvore` é o que drive.ler_arvore devolve
    para a pasta do cliente — isto é, o conteúdo dela, não ela mesma.
    """
    rel = Relatorio()
    cam = nome_cliente
    checar_nome(rel, cam, nome_cliente)

    presentes = _subpastas(arvore)

    # Pasta em CLIENTES que só tem originação é uma originação no lugar
    # errado: não há mandato, logo não há cliente. O lugar dela é o funil.
    # Um diagnóstico só, em vez dos três achados soltos que sairiam daqui
    # para baixo (sem APOLICES, sem FRENTES, sem ativo).
    if presentes and set(presentes) <= {ORIGINACAO}:
        rel.add(
            ERRO,
            cam,
            "pasta de cliente que só tem originação — não há mandato aqui",
            "mover para a raiz do funil; quando o contrato assinar, "
            "vbr_pastas.py promover traz de volta",
        )
        checar_originacao(rel, f"{cam}/{ORIGINACAO}", arvore[ORIGINACAO])
        percorrer_duplicatas(rel, cam, arvore)
        return rel

    if ORIGINACAO not in presentes:
        rel.add(
            AVISO,
            cam,
            "cliente sem pasta de originação",
            "normal só se o cliente veio de antes do modelo",
        )
    else:
        checar_originacao(rel, f"{cam}/{ORIGINACAO}", arvore[ORIGINACAO])

    if APOLICES not in presentes:
        rel.add(ERRO, cam, "cliente sem pasta APOLICES", "criar APOLICES")
    else:
        checar_apolices(rel, f"{cam}/{APOLICES}", arvore[APOLICES])

    if FRENTES not in presentes:
        rel.add(ERRO, cam, "cliente sem pasta FRENTES", "criar FRENTES")
    else:
        checar_frentes(rel, f"{cam}/{FRENTES}", arvore[FRENTES])

    # O que sobra no nível do cliente é ativo.
    ativos = [p for p in presentes if p not in (ORIGINACAO, APOLICES, FRENTES)]
    if not ativos:
        rel.add(
            NOTA,
            cam,
            "cliente sem ativo",
            "normal em mandato que não é por ativo; conferir se falta cadastrar",
        )
    for ativo in ativos:
        checar_ativo(rel, cam, ativo, arvore[ativo])

    if _arquivos(arvore):
        rel.add(
            AVISO,
            cam,
            f"{len(_arquivos(arvore))} arquivo(s) solto(s) na raiz do cliente",
            "a raiz do cliente só tem pastas",
        )

    percorrer_duplicatas(rel, cam, arvore)
    return rel


def auditar_funil(arvore: dict, meses_de_paciencia: int = 12) -> Relatorio:
    """
    Audita a raiz do funil. `arvore` é o que drive.ler_arvore devolve para a
    pasta ORIGINACAO — isto é, o conteúdo dela.

    O que se checa aqui é diferente do cliente. Não há apólice nem ativo para
    cobrar; o que importa é que cada originação tenha nome datado, tenha a
    forma certa, e que nenhuma esteja parada há tempo demais. Originação
    parada não é erro de pasta: é uma decisão que ninguém tomou.
    """
    rel = Relatorio()
    hoje = date.today()

    for nome in _subpastas(arvore):
        if nome == ENCERRADAS:
            for encerrada in _subpastas(arvore[nome]):
                rel.add(NOTA, f"{ENCERRADAS}/{encerrada}", "encerrada")
            continue

        cam = nome
        checar_nome(rel, cam, nome, eh_frente=True)  # nome datado, mesmo padrão

        casamento = PADRAO_NOME_FRENTE.fullmatch(nome.strip())
        if not casamento:
            rel.add(
                ERRO,
                cam,
                f"nome de originação fora do padrão: {nome!r}",
                "usar AAAA-MM_NOME, por exemplo 2026-03_CVCP",
            )
        else:
            ano, mes = int(casamento.group(1)), int(casamento.group(2))
            if not 1 <= mes <= 12:
                rel.add(ERRO, cam, f"mês inválido no nome: {mes:02d}")
            else:
                meses = (hoje.year - ano) * 12 + (hoje.month - mes)
                if meses >= meses_de_paciencia:
                    rel.add(
                        AVISO,
                        cam,
                        f"aberta há {meses} meses",
                        "fechar ou encerrar — o funil só serve enquanto é verdade",
                    )

        checar_originacao(rel, cam, arvore[nome])

    if _arquivos(arvore):
        rel.add(
            AVISO,
            "(raiz do funil)",
            f"{len(_arquivos(arvore))} arquivo(s) solto(s) na raiz do funil",
            "cada originação tem pasta própria",
        )

    percorrer_duplicatas(rel, "(funil)", arvore)
    return rel


def formatar(rel: Relatorio, nome_cliente: str) -> str:
    """Monta o relatório em texto para o terminal."""
    linhas = [f"Auditoria de {nome_cliente}", "=" * (13 + len(nome_cliente)), ""]

    if rel.limpo():
        linhas.append("Nenhum erro nem aviso. A árvore está no modelo.")
    else:
        for gravidade, titulo in ((ERRO, "ERROS"), (AVISO, "AVISOS")):
            achados = rel.por_gravidade(gravidade)
            if not achados:
                continue
            linhas.append(f"{titulo} ({len(achados)})")
            linhas.append("-" * len(titulo))
            for a in achados:
                linhas.append(f"  {a.caminho}")
                linhas.append(f"    {a.mensagem}")
                if a.sugestao:
                    linhas.append(f"    -> {a.sugestao}")
            linhas.append("")

    notas = rel.notas
    if notas:
        linhas.append(f"NOTAS ({len(notas)})")
        linhas.append("-----")
        for a in notas:
            linhas.append(f"  {a.caminho}: {a.mensagem}")
        linhas.append("")

    linhas.append(
        f"Resumo: {len(rel.erros)} erro(s), {len(rel.avisos)} aviso(s), {len(notas)} nota(s)."
    )
    return "\n".join(linhas)
