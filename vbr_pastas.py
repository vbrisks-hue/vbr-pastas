#!/usr/bin/env python3
"""
vbr-pastas — monta e confere a árvore de pastas de clientes da VB Risk.

    python vbr_pastas.py originar  abre uma originação no funil
    python vbr_pastas.py funil     mostra o funil, com a idade de cada uma
    python vbr_pastas.py encerrar  originação que não fechou sai do funil
    python vbr_pastas.py reabrir   traz de volta do ZZ-ENCERRADAS
    python vbr_pastas.py promover  assinou: a originação entra no cliente
    python vbr_pastas.py novo      cria um cliente com mandato
    python vbr_pastas.py ativo     acrescenta um ativo a um cliente que já existe
    python vbr_pastas.py frente    abre uma frente num cliente que já existe
    python vbr_pastas.py ramo      abre um ramo de apólice
    python vbr_pastas.py auditar   confere um cliente, ou o funil, contra o modelo
    python vbr_pastas.py alinhar   põe uma frente atrás do modelo na forma certa
    python vbr_pastas.py config    vê e muda onde ficam os clientes e o funil
    python vbr_pastas.py modelo    mostra o modelo em vigor

Nada é criado, movido ou renomeado sem o plano aparecer na tela e você
confirmar. Os caminhos ficam no config.json, não no código.

Duas pastas, não uma: CLIENTES só tem quem assinou; quem ainda não assinou
mora em ORIGINACAO, ao lado. `promover` é o que faz a travessia.
"""

from __future__ import annotations

import sys

from datetime import date

import alinhar as alinhamento
import config
import drive
import modelo
from auditoria import auditar_cliente, auditar_funil, formatar


# ---------------------------------------------------------------------------
# Terminal
# ---------------------------------------------------------------------------


def perguntar(texto: str, padrao: str = "") -> str:
    sufixo = f" [{padrao}]" if padrao else ""
    resposta = input(f"{texto}{sufixo}: ").strip()
    return resposta or padrao


def perguntar_sim(texto: str, padrao: bool = True) -> bool:
    marca = "S/n" if padrao else "s/N"
    while True:
        resposta = input(f"{texto} [{marca}]: ").strip().lower()
        if not resposta:
            return padrao
        if resposta in ("s", "sim", "y"):
            return True
        if resposta in ("n", "nao", "não"):
            return False
        print("  responda s ou n.")


def perguntar_lista(texto: str) -> list[str]:
    """Lê vários itens, um por linha, até uma linha em branco."""
    print(f"{texto} (um por linha, linha vazia encerra)")
    itens = []
    while True:
        item = input("  > ").strip()
        if not item:
            return itens
        itens.append(item)


def escolher_tipo_frente() -> str:
    tipos = list(modelo.TIPOS_FRENTE)
    print("\n  Tipos de frente:")
    for i, tipo in enumerate(tipos, 1):
        spec = modelo.TIPOS_FRENTE[tipo]
        print(f"    {i}. {tipo:<14} {spec['descricao']}")
        print(f"       {'':14} usar quando: {spec['quando']}")
        print(f"       {'':14} {len(spec['subpastas'])} subpastas")
    while True:
        escolha = input(f"  tipo [1-{len(tipos)}]: ").strip()
        if escolha.isdigit() and 1 <= int(escolha) <= len(tipos):
            return tipos[int(escolha) - 1]
        if escolha.upper() in modelo.TIPOS_FRENTE:
            return escolha.upper()
        print("  escolha inválida.")


def coletar_frentes(onde: str) -> list[tuple[str, str]]:
    """Pergunta quantas frentes forem, devolve [(nome_montado, tipo)]."""
    frentes = []
    while perguntar_sim(f"\nAbrir uma frente em {onde}?", padrao=False):
        titulo = perguntar("  título da frente (ex.: Renovação RO)")
        if not titulo:
            continue
        competencia = perguntar(
            "  competência AAAA-MM (quando a frente começou)",
            modelo.competencia_de_hoje(),
        )
        tipo = escolher_tipo_frente()
        try:
            nome = modelo.nome_de_frente(competencia, titulo)
        except ValueError as erro:
            print(f"  {erro}")
            continue
        frentes.append((nome, tipo))
        print(f"  -> {nome}  ({tipo})")
    return frentes


def confirmar_plano(arvore: dict, destino: str) -> bool:
    print()
    print(f"Plano — será criado em {destino}:")
    print()
    for linha in modelo.desenhar(arvore):
        print("  " + linha)
    print()
    print(f"{modelo.contar(arvore)} pastas.")
    print()
    return perguntar_sim("Criar?", padrao=False)


# Âncora das etiquetas. É um prefixo fixo de propósito: se fosse o caminho da
# pasta raiz, renomear a raiz — o que já aconteceu uma vez, quando
# NOVA_CLIENTES virou CLIENTES — invalidaria a etiqueta de todas as pastas.
ANCORA = "vbr"


def executar(
    servico, arvore: dict, pai_id: str, ancora: str = ANCORA, resumo: bool = True
) -> tuple[int, int]:
    criadas = existentes = 0
    for profundidade, nome, _id, foi_criada in drive.criar_arvore(
        servico, arvore, pai_id, ancora
    ):
        marca = "+" if foi_criada else "="
        print(f"  {marca} {'  ' * profundidade}{nome}")
        if foi_criada:
            criadas += 1
        else:
            existentes += 1
    if resumo:
        print()
        print(f"{criadas} pasta(s) criada(s), {existentes} já existia(m).")
    return criadas, existentes


def achar_raiz(servico, caminho_raiz: str):
    """
    Localiza a pasta de clientes. Se não achar, diz exatamente em que degrau
    o caminho quebrou e lista o que existe ali — mudou o nome da pasta, é
    isso que aparece, e o conserto é óbvio.
    """
    raiz, degrau, ultima = drive.achar_por_caminho_detalhado(servico, caminho_raiz)
    if raiz:
        return raiz

    print()
    print(f"não achei {caminho_raiz!r} no seu Drive.")
    print(f"  cheguei até {ultima['name']!r}, mas lá dentro não há {degrau!r}.")

    vizinhas = [
        f["name"]
        for f in drive.listar_filhos(servico, ultima["id"], so_pastas=True)
    ]
    if vizinhas:
        print(f"  o que existe em {ultima['name']!r}:")
        for nome in sorted(vizinhas)[:20]:
            print(f"    {nome}")
        if len(vizinhas) > 20:
            print(f"    ... e mais {len(vizinhas) - 20}")

    print()
    print("  conserte de um destes jeitos:")
    print("    vbr_pastas.py config            grava o caminho certo de vez")
    print("    --raiz 'CAMINHO/COM/BARRAS'     vale só desta vez")
    sys.exit(1)


def ancora_de(caminho: str, *extras: str) -> str:
    """
    Monta a âncora de etiqueta para uma subárvore, normalizando cada degrau.

        ancora_de('GRUPO-DIAMANTE/Pecem I', 'FRENTES')
        -> 'vbr/GRUPO-DIAMANTE/PECEM-I/FRENTES'
    """
    partes = [modelo.normalizar(x) for x in caminho.split("/") if x.strip()]
    return "/".join([ANCORA, *partes, *extras])


def ancora_originacao(nome: str, *extras: str) -> str:
    """
    A âncora de uma originação é o NOME dela, sem a data e sem onde ela está:

        ancora_originacao('2026-03_CVCP')  ->  'vbr/ORIGINACAO/CVCP'

    De propósito. Uma originação muda de nome (ganha e perde o prefixo de
    data), muda de lugar duas ou três vezes na vida — funil, encerradas,
    funil de novo, dentro do cliente — e continua sendo a mesma coisa. Se a
    etiqueta seguisse o caminho, cada mudança dessas a invalidaria e o
    programa criaria uma segunda pasta ao lado. Seguindo o nome, ela
    atravessa a vida inteira com uma identidade só.
    """
    return "/".join([ANCORA, "ORIGINACAO", modelo.titulo_de(nome), *extras])


def resolver_raiz(args) -> str:
    """O caminho em vigor: --raiz, VBR_RAIZ, config.json, ou a pergunta."""
    return config.raiz(getattr(args, "raiz", None), perguntar_se_faltar=perguntar)


def resolver_originacao(args, caminho_clientes: str) -> str:
    """O caminho do funil: --originacao, VBR_ORIGINACAO, config.json, ou a
    pasta irmã de CLIENTES chamada ORIGINACAO."""
    return config.raiz_originacao(
        getattr(args, "originacao", None), caminho_clientes
    )


def achar_raiz_do_funil(servico, caminho_funil: str):
    """
    Como achar_raiz, mas o funil pode legitimamente ainda não existir — é uma
    pasta nova no Drive de quem já tinha CLIENTES. Então, se o que falta é só
    o último degrau e o pai está lá, oferece criar em vez de mandar embora.
    """
    pasta, degrau, ultima = drive.achar_por_caminho_detalhado(servico, caminho_funil)
    if pasta:
        return pasta

    ultimo_degrau = [d for d in caminho_funil.split("/") if d][-1]
    if degrau == ultimo_degrau:
        print()
        print(f"a pasta do funil ainda não existe: {caminho_funil}")
        print(f"  o pai {ultima['name']!r} está lá; falta só {degrau!r}.")
        if perguntar_sim(f"Criar {degrau!r} agora?", padrao=True):
            nova, _ = drive.achar_ou_criar(servico, degrau, ultima["id"])
            print(f"  + {degrau}")
            return nova
        print("sem a pasta do funil não há o que fazer.")
        sys.exit(1)

    return achar_raiz(servico, caminho_funil)


# ---------------------------------------------------------------------------
# Comandos
# ---------------------------------------------------------------------------


def cmd_novo(args):
    """
    Cliente novo, com mandato. Quem não tem mandato não entra aqui: entra no
    funil, por `originar`.
    """
    caminho_raiz = resolver_raiz(args)
    print("Cliente novo")
    print("------------")
    nome = perguntar("Nome do cliente")
    if not nome:
        print("sem nome, nada a fazer.")
        return
    normalizado = modelo.normalizar(nome)
    if normalizado != nome:
        print(f"  na grafia da casa: {normalizado}")

    print()
    if not perguntar_sim("Já tem mandato assinado?", padrao=True):
        print()
        print("  Então não é cliente ainda, e a pasta não é aqui.")
        print("  Sem mandato não há acervo, apólice nem frente — frente é")
        print("  trabalho sob mandato. O lugar é o funil:")
        print()
        print("    vbr_pastas.py originar")
        print()
        print("  Quando o contrato assinar, `promover` traz a originação para")
        print("  dentro do cliente, inteira, com tudo que ela juntou.")
        return

    print()
    print("  Se já houve originação no funil, não crie o cliente por aqui:")
    print("  use `promover`, que move a originação para dentro e faz a árvore")
    print("  crescer de uma vez só.")
    print()
    ativos = perguntar_lista("Ativos do cliente")
    frentes_grupo = coletar_frentes("no nível do grupo (atravessa ativos)")

    frentes_ativo = {}
    for ativo in ativos:
        alvo = modelo.normalizar(ativo)
        frentes = coletar_frentes(f"no ativo {alvo}")
        if frentes:
            frentes_ativo[alvo] = frentes

    arvore = modelo.arvore_do_cliente(
        nome,
        ativos=ativos,
        frentes_do_grupo=frentes_grupo,
        frentes_por_ativo=frentes_ativo,
    )

    if not confirmar_plano(arvore, caminho_raiz):
        print("cancelado, nada foi criado.")
        return

    servico = drive.conectar()
    raiz = achar_raiz(servico, caminho_raiz)
    print()
    executar(servico, arvore, raiz["id"])


# ---------------------------------------------------------------------------
# O funil
# ---------------------------------------------------------------------------


def achar_originacao(servico, funil_id: str, nome: str) -> tuple[dict | None, bool]:
    """
    Procura uma originação no funil, pelo nome que o usuário digitou —
    'CVCP', '2026-03_CVCP' ou 'cvcp' têm que achar a mesma pasta.

    Devolve (pasta, estava_encerrada). Procura primeiro pela etiqueta, que é
    o caminho curto e funciona mesmo que alguém tenha renomeado a pasta à mão.
    """
    marcada = drive.achar_por_etiqueta(servico, ancora_originacao(nome))
    if marcada:
        # A etiqueta acha em qualquer lugar do Drive, então ainda falta saber
        # se ela está no funil ou já no arquivo morto.
        encerradas = drive.achar_pasta(servico, modelo.ENCERRADAS, funil_id)
        if encerradas:
            irmas = {
                f["id"]
                for f in drive.listar_filhos(servico, encerradas["id"], so_pastas=True)
            }
            return marcada, marcada["id"] in irmas
        return marcada, False

    alvo = modelo.titulo_de(nome)
    for onde, encerrada in ((funil_id, False), (None, True)):
        if onde is None:
            pasta_enc = drive.achar_pasta(servico, modelo.ENCERRADAS, funil_id)
            if not pasta_enc:
                continue
            onde = pasta_enc["id"]
        for f in drive.listar_filhos(servico, onde, so_pastas=True):
            if f["name"] == modelo.ENCERRADAS:
                continue
            if modelo.titulo_de(f["name"]) == alvo:
                return f, encerrada
    return None, False


def cmd_originar(args):
    """Abre uma originação no funil. É a única porta de entrada de quem ainda
    não assinou."""
    caminho_raiz = resolver_raiz(args)
    caminho_funil = resolver_originacao(args, caminho_raiz)

    print("Originação nova")
    print("---------------")
    print(f"  o funil fica em {caminho_funil}")
    print()
    nome = args.nome or perguntar("Nome do prospecto")
    if not nome:
        print("sem nome, nada a fazer.")
        return

    competencia = perguntar(
        "Competência AAAA-MM (quando a conversa começou)",
        modelo.competencia_de_hoje(),
    )
    try:
        pasta_nome = modelo.nome_de_originacao(competencia, nome)
    except ValueError as erro:
        print(erro)
        return

    arvore = {pasta_nome: modelo.arvore_de_originacao()}
    if not confirmar_plano(arvore, caminho_funil):
        print("cancelado, nada foi criado.")
        return

    servico = drive.conectar()
    funil = achar_raiz_do_funil(servico, caminho_funil)

    ja_existe, encerrada = achar_originacao(servico, funil["id"], pasta_nome)
    if ja_existe:
        onde = "em ZZ-ENCERRADAS" if encerrada else "no funil"
        print(f"\njá existe uma originação com esse nome {onde}: {ja_existe['name']}")
        if encerrada:
            print("  para trazer de volta: vbr_pastas.py reabrir " + modelo.titulo_de(nome))
        return

    # A pasta de cima é criada à parte porque a etiqueta dela não segue o
    # nome da pasta: segue o nome da originação, sem a data. Veja
    # ancora_originacao.
    etiqueta = ancora_originacao(pasta_nome)
    print()
    raiz_orig, criada = drive.achar_ou_criar(
        servico, pasta_nome, funil["id"], etiqueta
    )
    print(f"  {'+' if criada else '='} {pasta_nome}")
    executar(servico, modelo.arvore_de_originacao(), raiz_orig["id"], etiqueta)
    print()
    print("Enquanto não houver mandato, é só isto: nem acervo, nem apólice,")
    print("nem frente. Quando assinar: vbr_pastas.py promover " + modelo.titulo_de(nome))


def cmd_funil(args):
    """
    O funil inteiro numa tela: o que está aberto, há quanto tempo, e o que
    foi encerrado e por quê.
    """
    caminho_raiz = resolver_raiz(args)
    caminho_funil = resolver_originacao(args, caminho_raiz)

    servico = drive.conectar()
    funil = achar_raiz_do_funil(servico, caminho_funil)

    abertas, encerradas = [], []
    for f in drive.listar_filhos(servico, funil["id"], so_pastas=True,
                                 com_propriedades=True):
        if f["name"] == modelo.ENCERRADAS:
            encerradas = drive.listar_filhos(
                servico, f["id"], so_pastas=True, com_propriedades=True
            )
        else:
            abertas.append(f)

    hoje = date.today()

    def idade(nome: str) -> int | None:
        casamento = modelo.PADRAO_DATADO.fullmatch(nome.strip())
        if not casamento:
            return None
        ano, mes = int(casamento.group(1)), int(casamento.group(2))
        return (hoje.year - ano) * 12 + (hoje.month - mes)

    print(f"Funil — {caminho_funil}")
    print("=" * (8 + len(caminho_funil)))
    print()

    if not abertas:
        print("  nenhuma originação aberta.")
    else:
        print(f"ABERTAS ({len(abertas)})")
        print("-------")
        for f in sorted(abertas, key=lambda x: x["name"]):
            meses = idade(f["name"])
            tempo = "?" if meses is None else f"{meses} mes(es)"
            marca = "!" if (meses or 0) >= args.paciencia else " "
            print(f"  {marca} {f['name']:<34} aberta há {tempo}")
        if any((idade(f["name"]) or 0) >= args.paciencia for f in abertas):
            print()
            print(f"  ! passou de {args.paciencia} meses. Fechar ou encerrar —")
            print("    o funil só serve enquanto é verdade.")

    if encerradas:
        print()
        print(f"ENCERRADAS ({len(encerradas)})")
        print("----------")
        for f in sorted(encerradas, key=lambda x: x["name"], reverse=True):
            registro = (f.get("appProperties") or {}).get(drive.CHAVE_ENCERRAMENTO, "")
            quando, _, motivo = registro.partition("|")
            print(f"    {f['name']:<34} {quando or '(sem data)'}  {motivo}")
        print()
        print("  para trazer uma de volta: vbr_pastas.py reabrir NOME")


def cmd_encerrar(args):
    """
    Originação que não fechou sai do funil, mas não some. Vai para
    ZZ-ENCERRADAS com data e motivo — em papel, num arquivo dentro dela, e
    numa propriedade invisível que o `funil` lê.

    Não se apaga porque prospecto volta. Saber quem disse não, quando e por
    quê é metade do trabalho da próxima vez que o nome aparecer.
    """
    caminho_raiz = resolver_raiz(args)
    caminho_funil = resolver_originacao(args, caminho_raiz)

    print("Encerrar originação")
    print("-------------------")
    nome = args.nome or perguntar("Qual originação")
    if not nome:
        return
    motivo = args.motivo or perguntar("Motivo (uma linha)")
    if not motivo:
        print("sem motivo, não encerro — o motivo é o que dá valor ao registro.")
        return

    servico = drive.conectar()
    funil = achar_raiz_do_funil(servico, caminho_funil)
    pasta, ja_encerrada = achar_originacao(servico, funil["id"], nome)
    if not pasta:
        print(f"não achei {nome!r} no funil.")
        return
    if ja_encerrada:
        print(f"{pasta['name']} já está em {modelo.ENCERRADAS}.")
        return

    quando = date.today().isoformat()
    print()
    print(f"  {pasta['name']}")
    print(f"    vai para {modelo.ENCERRADAS}/")
    print(f"    registro: {quando} — {motivo}")
    print()
    if not perguntar_sim("Encerrar?", padrao=False):
        print("cancelado.")
        return

    encerradas, criada = drive.achar_ou_criar(servico, modelo.ENCERRADAS, funil["id"])
    if criada:
        print(f"  + {modelo.ENCERRADAS}  (não existia)")

    drive.anotar(servico, pasta["id"], **{drive.CHAVE_ENCERRAMENTO: f"{quando}|{motivo}"})
    drive.mover(servico, pasta["id"], encerradas["id"])
    try:
        drive.criar_texto(
            servico,
            modelo.BILHETE_DE_ENCERRAMENTO,
            pasta["id"],
            f"Originação encerrada em {quando}.\n\nMotivo: {motivo}\n\n"
            "Encerrada não é apagada: se o nome voltar, use\n"
            f"  vbr_pastas.py reabrir {modelo.titulo_de(pasta['name'])}\n",
        )
    except Exception as erro:  # o bilhete é conforto, não pode derrubar nada
        print(f"  (não consegui escrever o bilhete: {erro})")

    print(f"\n{pasta['name']} -> {modelo.ENCERRADAS}/")


def cmd_reabrir(args):
    """Prospecto voltou. Tira de ZZ-ENCERRADAS e devolve ao funil."""
    caminho_raiz = resolver_raiz(args)
    caminho_funil = resolver_originacao(args, caminho_raiz)

    print("Reabrir originação")
    print("------------------")
    nome = args.nome or perguntar("Qual originação")
    if not nome:
        return

    servico = drive.conectar()
    funil = achar_raiz_do_funil(servico, caminho_funil)
    pasta, encerrada = achar_originacao(servico, funil["id"], nome)
    if not pasta:
        print(f"não achei {nome!r} nem no funil nem em {modelo.ENCERRADAS}.")
        return
    if not encerrada:
        print(f"{pasta['name']} já está aberta no funil.")
        return

    print(f"\n  {pasta['name']}  ->  volta para o funil")
    if not perguntar_sim("Reabrir?", padrao=True):
        print("cancelado.")
        return

    drive.mover(servico, pasta["id"], funil["id"])
    drive.anotar(servico, pasta["id"], **{drive.CHAVE_ENCERRAMENTO: None})
    print(f"\n{pasta['name']} está no funil de novo.")
    print("  o _ENCERRAMENTO.txt fica: é a memória de por que parou da outra vez.")


def cmd_promover(args):
    """
    Assinou o mandato. A originação atravessa: sai do funil, entra na pasta
    do cliente e passa a se chamar 00-ORIGINACAO. Depois a árvore cresce.

    Move, não copia. É a diferença entre a originação continuar sendo a mesma
    coisa e passarem a existir duas versões dela — que foi o defeito que a
    migração de setembro levou três dias desfazendo.
    """
    caminho_raiz = resolver_raiz(args)
    caminho_funil = resolver_originacao(args, caminho_raiz)

    print("Promover: a originação vira cliente com mandato")
    print("----------------------------------------------")
    nome = args.cliente or perguntar("Qual originação")
    if not nome:
        return

    servico = drive.conectar()
    funil = achar_raiz_do_funil(servico, caminho_funil)
    origem, encerrada = achar_originacao(servico, funil["id"], nome)

    if origem and encerrada:
        print(f"\n{origem['name']} está em {modelo.ENCERRADAS}.")
        print(f"  reabra primeiro: vbr_pastas.py reabrir {modelo.titulo_de(nome)}")
        return

    if origem:
        print(f"\n  achei no funil: {origem['name']}")
        titulo = modelo.titulo_de(origem["name"])
    else:
        print(f"\n  não achei {nome!r} no funil.")
        print("  sigo assim mesmo: o cliente nasce com uma originação vazia.")
        if not perguntar_sim("  Continuar?", padrao=False):
            return
        titulo = modelo.normalizar(nome)

    nome_cliente = perguntar("Nome do cliente (pasta em CLIENTES)", titulo)
    nome_cliente = modelo.normalizar(nome_cliente)

    print()
    ativos = perguntar_lista("Ativos que o mandato cobre")
    frentes_grupo = coletar_frentes("no nível do grupo (atravessa ativos)")

    frentes_ativo = {}
    for ativo in ativos:
        alvo = modelo.normalizar(ativo)
        frentes = coletar_frentes(f"no ativo {alvo}")
        if frentes:
            frentes_ativo[alvo] = frentes

    arvore = modelo.arvore_de_promocao(
        ativos=ativos,
        frentes_do_grupo=frentes_grupo,
        frentes_por_ativo=frentes_ativo,
    )

    destino = f"{caminho_raiz}/{nome_cliente}"
    print()
    print(f"Plano — {destino}:")
    print()
    if origem:
        print(f"  mover   {caminho_funil}/{origem['name']}")
        print(f"       -> {destino}/{modelo.ORIGINACAO}   (com tudo dentro)")
    else:
        print(f"  criar   {destino}/{modelo.ORIGINACAO}   (vazia)")
    print("  criar:")
    for linha in modelo.desenhar(arvore):
        print("    " + linha)
    print()
    print(f"{modelo.contar(arvore)} pasta(s) nova(s)"
          + (", mais a originação que muda de lugar." if origem else "."))
    print()
    if not perguntar_sim("Promover?", padrao=False):
        print("cancelado, nada foi mexido.")
        return

    raiz = achar_raiz(servico, caminho_raiz)
    pasta_cliente, criada = drive.achar_ou_criar(
        servico, nome_cliente, raiz["id"], ancora_de(nome_cliente)
    )
    print()
    print(f"  {'+' if criada else '='} {nome_cliente}")

    if origem:
        drive.mover(servico, origem["id"], pasta_cliente["id"])
        drive.renomear(servico, origem["id"], modelo.ORIGINACAO)
        print(f"  > {modelo.ORIGINACAO}   (veio do funil, inteira)")
    else:
        executar(
            servico,
            {modelo.ORIGINACAO: modelo.arvore_de_originacao()},
            pasta_cliente["id"],
            ancora_de(nome_cliente),
            resumo=False,
        )

    executar(servico, arvore, pasta_cliente["id"], ancora_de(nome_cliente))
    print()
    print(f"O funil tem uma originação a menos. Confira: vbr_pastas.py funil")


def cmd_ativo(args):
    """
    Um ativo novo em cliente que já existe: o mandato ganhou uma usina. Só
    cria a árvore do ativo — ACERVO, APOLICES, FRENTES — e não toca em nada
    do que o cliente já tem. `novo` com o nome de um cliente existente não
    serve para isto: ele completaria também a originação.
    """
    caminho_raiz = resolver_raiz(args)
    print("Ativo novo em cliente existente")
    print("-------------------------------")
    cliente = perguntar("Cliente (nome da pasta em CLIENTES)")
    if not cliente:
        return
    nome = perguntar("Nome do ativo")
    ativo = modelo.normalizar(nome)
    if not ativo:
        print("sem nome, nada a fazer.")
        return
    if ativo != nome:
        print(f"  na grafia da casa: {ativo}")

    print("\n  Ramos da casa: " + ", ".join(modelo.RAMOS_CONHECIDOS))
    ramos = perguntar_lista("Ramos a criar já (pode deixar vazio)")
    frentes = coletar_frentes(f"no ativo {ativo}")

    arvore_ativo = modelo.arvore_de_promocao(
        ativos=[ativo], frentes_por_ativo={ativo: frentes})[ativo]
    for ramo in ramos:
        arvore_ativo[modelo.APOLICES].update(modelo.arvore_do_ramo(ramo))
    arvore = {ativo: arvore_ativo}

    if not confirmar_plano(arvore, f"{caminho_raiz}/{cliente}"):
        print("cancelado, nada foi criado.")
        return

    servico = drive.conectar()
    raiz = achar_raiz(servico, caminho_raiz)
    dono = drive.achar_por_caminho(servico, cliente, raiz["id"])
    if not dono:
        print(f"não achei o cliente {cliente!r} em {caminho_raiz}.")
        return
    if drive.achar_pasta(servico, ativo, dono["id"]):
        print(f"já existe {ativo} em {cliente}. para frente ou ramo nele: `frente` e `ramo`.")
        return
    print()
    executar(servico, arvore, dono["id"], ancora_de(cliente))


def cmd_frente(args):
    caminho_raiz = resolver_raiz(args)
    print("Frente nova em cliente existente")
    print("--------------------------------")
    caminho = perguntar(
        "Caminho da pasta que recebe a frente, a partir da raiz\n"
        "  (ex.: GRUPO-DIAMANTE  ou  GRUPO-DIAMANTE/PECEM-I)"
    )
    if not caminho:
        return

    titulo = perguntar("Título da frente")
    competencia = perguntar("Competência AAAA-MM", modelo.competencia_de_hoje())
    tipo = escolher_tipo_frente()
    try:
        nome = modelo.nome_de_frente(competencia, titulo)
    except ValueError as erro:
        print(erro)
        return

    arvore = {nome: {sub: {} for sub in modelo.TIPOS_FRENTE[tipo]["subpastas"]}}
    destino = f"{caminho_raiz}/{caminho}/{modelo.FRENTES}"
    if not confirmar_plano(arvore, destino):
        print("cancelado.")
        return

    servico = drive.conectar()
    raiz = achar_raiz(servico, caminho_raiz)
    dono = drive.achar_por_caminho(servico, caminho, raiz["id"])
    if not dono:
        print(f"não achei {caminho!r} dentro de {caminho_raiz}.")
        return
    pasta_frentes, criada = drive.achar_ou_criar(servico, modelo.FRENTES, dono["id"])
    if criada:
        print(f"  + {modelo.FRENTES}  (não existia)")
    print()
    executar(servico, arvore, pasta_frentes["id"],
             ancora_de(caminho, modelo.FRENTES))


def cmd_ramo(args):
    caminho_raiz = resolver_raiz(args)
    print("Ramo de apólice novo")
    print("--------------------")
    caminho = perguntar(
        "Caminho do cliente ou ativo, a partir da raiz\n"
        "  (ex.: GRUPO-DIAMANTE/PECEM-I)"
    )
    if not caminho:
        return

    print("\n  Ramos da casa: " + ", ".join(modelo.RAMOS_CONHECIDOS))
    ramos = perguntar_lista("\nRamos a criar")
    if not ramos:
        return

    arvore = {}
    for ramo in ramos:
        arvore.update(modelo.arvore_do_ramo(ramo))

    destino = f"{caminho_raiz}/{caminho}/{modelo.APOLICES}"
    if not confirmar_plano(arvore, destino):
        print("cancelado.")
        return

    servico = drive.conectar()
    raiz = achar_raiz(servico, caminho_raiz)
    dono = drive.achar_por_caminho(servico, caminho, raiz["id"])
    if not dono:
        print(f"não achei {caminho!r} dentro de {caminho_raiz}.")
        return
    pasta_apolices, criada = drive.achar_ou_criar(servico, modelo.APOLICES, dono["id"])
    if criada:
        print(f"  + {modelo.APOLICES}  (não existia)")
    print()
    executar(servico, arvore, pasta_apolices["id"],
             ancora_de(caminho, modelo.APOLICES))


def cmd_auditar(args):
    caminho_raiz = resolver_raiz(args)

    if args.funil:
        caminho_funil = resolver_originacao(args, caminho_raiz)
        print(f"lendo {caminho_funil} ...")
        servico = drive.conectar()
        funil = achar_raiz_do_funil(servico, caminho_funil)
        arvore = drive.ler_arvore(servico, funil["id"], incluir_arquivos=True)
        relatorio = auditar_funil(arvore)
        print()
        print(formatar(relatorio, "funil"))
        if args.saida:
            with open(args.saida, "w", encoding="utf-8") as arquivo:
                arquivo.write(formatar(relatorio, "funil"))
            print(f"\nrelatório salvo em {args.saida}")
        sys.exit(1 if relatorio.erros else 0)

    cliente = args.cliente or perguntar("Cliente a auditar (nome da pasta)")
    if not cliente:
        return

    print(f"\nlendo {caminho_raiz}/{cliente} ...")
    servico = drive.conectar()
    raiz = achar_raiz(servico, caminho_raiz)
    pasta = drive.achar_por_caminho(servico, cliente, raiz["id"])
    if not pasta:
        print(f"não achei o cliente {cliente!r} em {caminho_raiz}.")
        return

    arvore = drive.ler_arvore(servico, pasta["id"], incluir_arquivos=True)
    relatorio = auditar_cliente(pasta["name"], arvore)

    print()
    print(formatar(relatorio, pasta["name"]))

    if args.saida:
        with open(args.saida, "w", encoding="utf-8") as arquivo:
            arquivo.write(formatar(relatorio, pasta["name"]))
        print(f"\nrelatório salvo em {args.saida}")

    sys.exit(1 if relatorio.erros else 0)


def cmd_alinhar(args):
    """
    Uma frente criada antes do caderno v4 ganha a forma do modelo: renomeia
    as subpastas que têm par pelo número e cria as que faltam. Nunca apaga,
    nunca move arquivo. A lógica está em alinhar.py; a tela usa a mesma.
    """
    caminho_raiz = resolver_raiz(args)
    print("Alinhar frente com o modelo")
    print("---------------------------")
    caminho = args.frente or perguntar(
        "Caminho da frente, a partir da raiz\n"
        "  (ex.: GRUPO-DIAMANTE/FRENTES/2026-07_RFP-CORRETORA)"
    )
    if not caminho or f"/{modelo.FRENTES}/" not in f"/{caminho.strip('/')}/":
        print("o caminho tem de passar por FRENTES.")
        return

    servico = drive.conectar()
    raiz = achar_raiz(servico, caminho_raiz)
    pasta = drive.achar_por_caminho(servico, caminho, raiz["id"])
    if not pasta:
        print(f"não achei {caminho!r} dentro de {caminho_raiz}.")
        return
    filhos = {f["name"]: f for f in drive.listar_filhos(servico, pasta["id"], so_pastas=True)}

    try:
        plano = alinhamento.planejar(list(filhos), args.tipo)
    except ValueError as erro:
        print(erro)
        return
    if plano.ja_estava:
        print(f"a frente já está na forma {plano.tipo}. nada a fazer.")
        return
    renomear, criar, avisos = alinhamento.linhas_do_plano(plano)
    if plano.vazio():
        print(f"nada a renomear nem a criar para a forma {plano.tipo}.")
        for a in avisos:
            print("  " + a)
        return

    print()
    print(f"Plano — {caminho_raiz}/{caminho}, forma {plano.tipo}:")
    if renomear:
        print("  renomear:")
        for linha in renomear:
            print("    " + linha)
    if criar:
        print("  criar:")
        for linha in criar:
            print("    " + linha)
    for a in avisos:
        print("  aviso: " + a)
    print()
    print("Nada é apagado nem movido.")
    if not perguntar_sim("Alinhar?", padrao=False):
        print("cancelado, nada foi mexido.")
        return

    partes = caminho.strip("/").split("/")
    dono = "/".join(partes[:partes.index(modelo.FRENTES)])
    ancora = ancora_de(dono, modelo.FRENTES, partes[-1])
    print()
    for de, para in plano.renomear:
        drive.renomear(servico, filhos[de]["id"], para)
        try:
            drive.etiquetar(servico, filhos[de]["id"], f"{ancora}/{para}")
        except Exception:
            pass
        print(f"  ~ {de}  ->  {para}")
    for nome in plano.criar:
        _nova, criada = drive.achar_ou_criar(servico, nome, pasta["id"], f"{ancora}/{nome}")
        print(f"  {'+' if criada else '='} {nome}")
    print(f"\nA frente está na forma {plano.tipo}. Confira: vbr_pastas.py auditar {partes[0]}")


def cmd_config(args):
    """Mostra e muda onde ficam os clientes e o funil, sem abrir o código."""
    import os

    dados = config.ler()
    atual = dados.get("raiz")
    print("Configuração")
    print("------------")
    print(f"arquivo: {config.ARQUIVO.resolve()}")
    print(f"clientes:  {atual or '(nenhum ainda)'}")

    gravado_funil = dados.get("originacao")
    deduzido = config.irma_de(atual or config.RAIZ_SUGERIDA)
    print(
        f"funil:     {gravado_funil or deduzido}"
        + ("" if gravado_funil else "   (deduzido: a pasta irmã de CLIENTES)")
    )

    for variavel in ("VBR_RAIZ", "VBR_ORIGINACAO"):
        do_ambiente = os.environ.get(variavel)
        if do_ambiente:
            print(f"{variavel} no ambiente: {do_ambiente}  (vence o arquivo)")

    if args.definir:
        config.definir_raiz(args.definir)
        print(f"\ngravado (clientes): {args.definir}")
        return
    if args.definir_funil:
        config.definir_raiz_originacao(args.definir_funil)
        print(f"\ngravado (funil): {args.definir_funil}")
        return

    print()
    if not perguntar_sim("Mudar o caminho dos clientes?", padrao=False):
        return
    novo = perguntar("Novo caminho", atual or config.RAIZ_SUGERIDA)
    config.definir_raiz(novo)
    print(f"gravado: {novo.strip('/')}")
    print(f"o funil passa a ser deduzido como {config.irma_de(novo)}")
    if perguntar_sim("Mudar também o caminho do funil?", padrao=False):
        novo_funil = perguntar("Caminho do funil", config.irma_de(novo))
        config.definir_raiz_originacao(novo_funil)
        print(f"gravado: {novo_funil.strip('/')}")

    if perguntar_sim("Conferir agora se essa pasta existe no Drive?", padrao=True):
        servico = drive.conectar()
        pasta = achar_raiz(servico, novo.strip("/"))
        filhos = drive.listar_filhos(servico, pasta["id"], so_pastas=True)
        print(f"\nachei. {len(filhos)} pasta(s) de cliente lá dentro:")
        for f in sorted(filhos, key=lambda x: x["name"]):
            print(f"  {f['name']}")


def cmd_modelo(args):
    print("Modelo de pastas da VB Risk")
    print("===========================\n")

    print("ORIGINAÇÃO — mora no funil enquanto não há mandato")
    print("  antes de assinar:  ORIGINACAO/AAAA-MM_NOME")
    print(f"  depois de assinar: CLIENTES/NOME/{modelo.ORIGINACAO}  (a mesma pasta, movida)")
    print(f"  não fechou:        ORIGINACAO/{modelo.ENCERRADAS}/AAAA-MM_NOME")
    print()
    for sub in modelo.ORIGINACAO_SUBPASTAS:
        print(f"  {sub}")
        for neto in modelo.ORIGINACAO_NETOS.get(sub, []):
            print(f"    {neto}")

    print(f"\nACERVO — {modelo.ACERVO} (no ativo)")
    for sub in modelo.ACERVO_SUBPASTAS:
        print(f"  {sub}")

    print(f"\nAPÓLICES — {modelo.APOLICES} (nasce vazia nos dois níveis)")
    print("  cada ramo tem: " + ", ".join(modelo.RAMO_SUBPASTAS))
    print("  ramos da casa: " + ", ".join(modelo.RAMOS_CONHECIDOS))

    print(f"\nFRENTES — {modelo.FRENTES} (nome AAAA-MM_TITULO)")
    for tipo, spec in modelo.TIPOS_FRENTE.items():
        print(f"\n  {tipo} — {spec['descricao']}")
        print(f"    usar quando: {spec['quando']}")
        for sub in spec["subpastas"]:
            print(f"      {sub}")

    print("\nGrafia: hífen, maiúscula, sem acento. Exemplos:")
    for exemplo in ("Renovação Apólices", "D&O", "  Pecem I  ", "RC Geral"):
        print(f"  {exemplo!r:24} -> {modelo.normalizar(exemplo)!r}")


# ---------------------------------------------------------------------------


def main():
    import argparse

    p = argparse.ArgumentParser(
        prog="vbr-pastas",
        description="Monta e confere a árvore de pastas de clientes da VB Risk.",
    )
    p.add_argument(
        "--raiz",
        default=None,
        help="caminho da pasta de clientes no Drive, só desta vez "
             "(o padrão vem do config.json)",
    )
    p.add_argument(
        "--originacao",
        default=None,
        help="caminho da pasta do funil no Drive, só desta vez "
             "(o padrão é a pasta irmã de CLIENTES chamada ORIGINACAO)",
    )
    sub = p.add_subparsers(dest="comando", required=True)

    o = sub.add_parser("originar", help="abre uma originação no funil")
    o.add_argument("nome", nargs="?", help="nome do prospecto")
    o.set_defaults(func=cmd_originar)

    fu = sub.add_parser("funil", help="mostra o funil, com a idade de cada originação")
    fu.add_argument(
        "--paciencia",
        type=int,
        default=12,
        help="a partir de quantos meses uma originação aberta é sinalizada (padrão 12)",
    )
    fu.set_defaults(func=cmd_funil)

    en = sub.add_parser("encerrar", help="originação que não fechou sai do funil")
    en.add_argument("nome", nargs="?", help="nome da originação")
    en.add_argument("--motivo", help="por que não fechou — uma linha")
    en.set_defaults(func=cmd_encerrar)

    re_ = sub.add_parser("reabrir", help="traz uma originação de volta ao funil")
    re_.add_argument("nome", nargs="?", help="nome da originação")
    re_.set_defaults(func=cmd_reabrir)

    pr = sub.add_parser(
        "promover", help="assinou: a originação sai do funil e entra no cliente"
    )
    pr.add_argument("cliente", nargs="?", help="nome da originação")
    pr.set_defaults(func=cmd_promover)

    sub.add_parser("novo", help="cria um cliente com mandato").set_defaults(
        func=cmd_novo
    )
    sub.add_parser("ativo", help="acrescenta um ativo a um cliente existente").set_defaults(
        func=cmd_ativo
    )
    sub.add_parser("frente", help="abre uma frente num cliente existente").set_defaults(
        func=cmd_frente
    )
    sub.add_parser("ramo", help="abre um ramo de apólice").set_defaults(func=cmd_ramo)

    a = sub.add_parser("auditar", help="confere um cliente, ou o funil, contra o modelo")
    a.add_argument("cliente", nargs="?", help="nome da pasta do cliente")
    a.add_argument("--funil", action="store_true", help="audita o funil em vez de um cliente")
    a.add_argument("--saida", help="salva o relatório neste arquivo")
    a.set_defaults(func=cmd_auditar)

    al = sub.add_parser("alinhar", help="põe uma frente atrás do modelo na forma certa")
    al.add_argument("frente", nargs="?", help="caminho da frente, a partir da raiz (…/FRENTES/AAAA-MM_TITULO)")
    al.add_argument("--tipo", help="a forma a usar; sem isto, a mais parecida")
    al.set_defaults(func=cmd_alinhar)

    c = sub.add_parser("config", help="vê e muda onde ficam os clientes e o funil")
    c.add_argument("--definir", help="grava este caminho de clientes e sai")
    c.add_argument("--definir-funil", help="grava este caminho de funil e sai")
    c.set_defaults(func=cmd_config)

    sub.add_parser("modelo", help="mostra o modelo em vigor").set_defaults(
        func=cmd_modelo
    )

    args = p.parse_args()
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\ncancelado.")
        sys.exit(130)
    except drive.DriveErro as erro:
        print(f"\n{erro}")
        sys.exit(1)


if __name__ == "__main__":
    main()
