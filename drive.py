"""
Camada fina sobre a API do Google Drive.

Duas garantias que importam para este programa:

1. Criação é idempotente. Antes de criar, procura. Rodar duas vezes não
   gera 'PECEM-I' e 'PECEM-I 2' — que é exatamente o defeito que espalhou
   pacotes duplicados na pasta antiga.

2. Listagem devolve tudo, sem repetido. A paginação do Drive pode
   entregar a mesma entrada em duas páginas quando a pasta muda durante a
   varredura; aqui os ids passam por um conjunto antes de sair.
"""

from __future__ import annotations

import os
from pathlib import Path

ESCOPOS = ["https://www.googleapis.com/auth/drive"]
MIME_PASTA = "application/vnd.google-apps.folder"

# Onde ficam a credencial e o token. Dá para apontar para outro lugar
# com as variáveis de ambiente VBR_CREDENCIAL e VBR_TOKEN.
CREDENCIAL = Path(os.environ.get("VBR_CREDENCIAL", "credentials.json"))
TOKEN = Path(os.environ.get("VBR_TOKEN", "token.json"))


class DriveErro(RuntimeError):
    pass


def _bibliotecas():
    """
    Importa as bibliotecas do Google só quando alguém vai falar com o Drive.

    Assim `vbr_pastas.py modelo` funciona numa máquina sem nada instalado,
    e quem esquecer o pip install recebe uma instrução em vez de um traceback.
    """
    try:
        from google.auth.exceptions import RefreshError
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as erro:
        raise DriveErro(
            "faltam as bibliotecas do Google.\n"
            "  pip install -r requirements.txt\n"
            f"  (detalhe: {erro})"
        ) from erro
    return Request, Credentials, InstalledAppFlow, build, RefreshError


def conectar():
    """
    Autentica e devolve o serviço do Drive.

    Na primeira vez abre o navegador para você autorizar. Depois disso o
    token fica salvo e renova sozinho. Veja o README para gerar o
    credentials.json — é uma vez só.
    """
    Request, Credentials, InstalledAppFlow, build, RefreshError = _bibliotecas()

    cred = None
    if TOKEN.exists():
        cred = Credentials.from_authorized_user_file(str(TOKEN), ESCOPOS)
    if not cred or not cred.valid:
        if cred and cred.expired and cred.refresh_token:
            try:
                cred.refresh(Request())
            except RefreshError:
                # O Google não renova mais esta autorização ("invalid_grant"):
                # ela venceu ou foi revogada. Com o app em modo Teste no Google
                # Cloud, isso acontece a cada sete dias. Em vez de parar com um
                # traceback e mandar apagar o token.json à mão, volta ao
                # começo: abre o navegador para autorizar de novo, e o token
                # novo é gravado por cima do vencido.
                cred = None
        if not cred or not cred.valid:
            if not CREDENCIAL.exists():
                raise DriveErro(
                    f"não achei {CREDENCIAL}.\n"
                    "Gere a credencial OAuth no Google Cloud e salve aqui. "
                    "O passo a passo está no README."
                )
            fluxo = InstalledAppFlow.from_client_secrets_file(str(CREDENCIAL), ESCOPOS)
            cred = fluxo.run_local_server(port=0)
        TOKEN.write_text(cred.to_json())
    return build("drive", "v3", credentials=cred, cache_discovery=False)


def _escapar(nome: str) -> str:
    """A query do Drive usa aspas simples, então apóstrofo precisa de escape."""
    return nome.replace("\\", "\\\\").replace("'", "\\'")


def listar_filhos(
    servico, pasta_id: str, so_pastas: bool = False, com_propriedades: bool = False
) -> list[dict]:
    """
    Todos os filhos diretos de uma pasta, sem repetidos.

    Devolve dicionários com id, name, mimeType e size. Com
    `com_propriedades`, traz também appProperties — é assim que o funil lê o
    motivo do encerramento sem precisar abrir pasta por pasta.
    """
    consulta = f"'{pasta_id}' in parents and trashed = false"
    if so_pastas:
        consulta += f" and mimeType = '{MIME_PASTA}'"

    campos = "id, name, mimeType, size"
    if com_propriedades:
        campos += ", appProperties"

    achados: dict[str, dict] = {}
    token = None
    while True:
        resposta = (
            servico.files()
            .list(
                q=consulta,
                spaces="drive",
                fields=f"nextPageToken, files({campos})",
                pageSize=1000,
                pageToken=token,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )
        for arquivo in resposta.get("files", []):
            achados[arquivo["id"]] = arquivo  # o id como chave elimina repetido
        token = resposta.get("nextPageToken")
        if not token:
            break
    return list(achados.values())


def achar_pasta(servico, nome: str, pai_id: str) -> dict | None:
    """Procura uma pasta pelo nome exato dentro de um pai. None se não houver."""
    consulta = (
        f"name = '{_escapar(nome)}' and '{pai_id}' in parents "
        f"and mimeType = '{MIME_PASTA}' and trashed = false"
    )
    resposta = (
        servico.files()
        .list(
            q=consulta,
            spaces="drive",
            fields="files(id, name)",
            pageSize=10,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        )
        .execute()
    )
    achados = resposta.get("files", [])
    return achados[0] if achados else None


def criar_pasta(servico, nome: str, pai_id: str) -> dict:
    """Cria a pasta sem procurar antes. Use achar_ou_criar no lugar."""
    corpo = {"name": nome, "mimeType": MIME_PASTA, "parents": [pai_id]}
    return (
        servico.files()
        .create(body=corpo, fields="id, name", supportsAllDrives=True)
        .execute()
    )


def renomear(servico, pasta_id: str, novo_nome: str) -> dict:
    """Troca o nome. Id, conteúdo, compartilhamento e histórico continuam."""
    return (
        servico.files()
        .update(
            fileId=pasta_id,
            body={"name": novo_nome},
            fields="id, name",
            supportsAllDrives=True,
        )
        .execute()
    )


def mover(servico, pasta_id: str, novo_pai_id: str) -> dict:
    """
    Muda a pasta de lugar, com tudo que há dentro.

    Mover não é copiar: o id é o mesmo, os links que alguém já tem continuam
    valendo, o compartilhamento não se perde e o histórico do Drive não se
    parte em dois. É por isso que a promoção de uma originação move em vez de
    copiar — copiar deixaria duas verdades convivendo, que foi exatamente o
    que a migração de setembro passou três dias desfazendo.
    """
    atual = (
        servico.files()
        .get(fileId=pasta_id, fields="parents", supportsAllDrives=True)
        .execute()
    )
    pais_antigos = ",".join(atual.get("parents", []))
    if pais_antigos == novo_pai_id:
        return (
            servico.files()
            .get(fileId=pasta_id, fields="id, name, parents", supportsAllDrives=True)
            .execute()
        )
    return (
        servico.files()
        .update(
            fileId=pasta_id,
            addParents=novo_pai_id,
            removeParents=pais_antigos,
            fields="id, name, parents",
            supportsAllDrives=True,
        )
        .execute()
    )


def criar_texto(servico, nome: str, pai_id: str, conteudo: str) -> dict:
    """
    Escreve um arquivo de texto pequeno. Serve para o bilhete que fica junto
    de uma originação encerrada, dizendo quando e por quê — a etiqueta
    invisível guarda o mesmo dado para a máquina, este arquivo é para quem
    abre a pasta daqui a dois anos e quer entender o que aconteceu.
    """
    try:
        from googleapiclient.http import MediaInMemoryUpload
    except ImportError as erro:  # pragma: no cover
        raise DriveErro(f"faltam as bibliotecas do Google ({erro})") from erro

    midia = MediaInMemoryUpload(
        conteudo.encode("utf-8"), mimetype="text/plain", resumable=False
    )
    return (
        servico.files()
        .create(
            body={"name": nome, "parents": [pai_id]},
            media_body=midia,
            fields="id, name",
            supportsAllDrives=True,
        )
        .execute()
    )


# ---------------------------------------------------------------------------
# A etiqueta invisível.
#
# Cada pasta criada recebe uma marca gravada nela mesma, que o Drive não
# mostra na tela. Na execução seguinte o programa procura primeiro pela
# etiqueta e só depois pelo nome — então a pasta continua sendo encontrada
# mesmo que alguém a renomeie ou mova à mão.
#
# A etiqueta é o CAMINHO INTEIRO, não a espécie. Uma versão anterior deste
# programa etiquetava a espécie, e o segundo cliente casava com a etiqueta do
# primeiro: a árvore inteira caía dentro dele. O caminho torna cada etiqueta
# única por instância.
#
# Ressalva: appProperties é privado do cliente OAuth que gravou. Se a
# credencial for regerada com outro client_id, as etiquetas antigas ficam
# invisíveis e o programa volta a casar por nome — que continua funcionando.
# ---------------------------------------------------------------------------

CHAVE_ETIQUETA = "vbr"


def achar_por_etiqueta(servico, etiqueta: str) -> dict | None:
    """
    Procura pela etiqueta, em qualquer lugar do Drive. De propósito não filtra
    por pai: é isso que faz a pasta sobreviver a renomear e a mover.
    """
    consulta = (
        f"appProperties has {{ key='{CHAVE_ETIQUETA}' "
        f"and value='{_escapar(etiqueta)}' }} and trashed = false"
    )
    try:
        resposta = (
            servico.files()
            .list(
                q=consulta,
                spaces="drive",
                fields="files(id, name)",
                pageSize=10,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )
    except Exception:
        # Busca por appProperties pode não estar disponível em alguns
        # contextos. Cair para a busca por nome é degradação aceitável.
        return None
    achados = resposta.get("files", [])
    return achados[0] if achados else None


def etiquetar(servico, pasta_id: str, etiqueta: str) -> None:
    """Grava a etiqueta numa pasta que já existe."""
    servico.files().update(
        fileId=pasta_id,
        body={"appProperties": {CHAVE_ETIQUETA: etiqueta}},
        supportsAllDrives=True,
    ).execute()


# Onde fica registrado o encerramento de uma originação: data e motivo, numa
# propriedade invisível da própria pasta. Sobrevive a renomear e a mover, e
# volta atrás sozinha quando a originação é reaberta.
CHAVE_ENCERRAMENTO = "vbr_encerrada"


def anotar(servico, pasta_id: str, **valores: str | None) -> None:
    """
    Grava ou apaga propriedades invisíveis. Valor None apaga a propriedade —
    é assim que a API do Drive remove uma appProperty.
    """
    servico.files().update(
        fileId=pasta_id,
        body={"appProperties": dict(valores)},
        supportsAllDrives=True,
    ).execute()


def ler_anotacoes(servico, pasta_id: str) -> dict:
    """As propriedades invisíveis de uma pasta. Dicionário vazio se não houver."""
    dados = (
        servico.files()
        .get(fileId=pasta_id, fields="appProperties", supportsAllDrives=True)
        .execute()
    )
    return dados.get("appProperties") or {}


def achar_ou_criar(
    servico, nome: str, pai_id: str, etiqueta: str | None = None
) -> tuple[dict, bool]:
    """
    Devolve (pasta, foi_criada). Se já existia, devolve a que existe.
    É o que torna seguro rodar o programa duas vezes no mesmo cliente.

    Com etiqueta, a ordem de busca é: etiqueta, depois nome. Pasta antiga
    encontrada pelo nome recebe a etiqueta na hora — é assim que a árvore que
    já existe passa a ser rastreável, sem precisar de migração à parte.
    """
    if etiqueta:
        marcada = achar_por_etiqueta(servico, etiqueta)
        if marcada:
            return marcada, False

    existente = achar_pasta(servico, nome, pai_id)
    if existente:
        if etiqueta:
            try:
                etiquetar(servico, existente["id"], etiqueta)
            except Exception:
                pass  # etiquetar é melhoria, não pode derrubar a execução
        return existente, False

    corpo = {"name": nome, "mimeType": MIME_PASTA, "parents": [pai_id]}
    if etiqueta:
        corpo["appProperties"] = {CHAVE_ETIQUETA: etiqueta}
    nova = (
        servico.files()
        .create(body=corpo, fields="id, name", supportsAllDrives=True)
        .execute()
    )
    return nova, True


def criar_arvore(
    servico,
    arvore: dict,
    pai_id: str,
    prefixo_etiqueta: str = "",
    _profundidade: int = 0,
):
    """
    Cria a árvore inteira sob o pai, de cima para baixo.

    `prefixo_etiqueta` é o caminho já percorrido; a etiqueta de cada pasta é
    esse prefixo mais o próprio nome. Passe vazio para não etiquetar.

    Gera cada passo em vez de devolver no fim, para o terminal poder mostrar o
    progresso numa árvore grande. Cada passo:
    (profundidade, nome, id, foi_criada).
    """
    for nome, filhos in arvore.items():
        etiqueta = f"{prefixo_etiqueta}/{nome}" if prefixo_etiqueta else None
        pasta, criada = achar_ou_criar(servico, nome, pai_id, etiqueta)
        yield _profundidade, nome, pasta["id"], criada
        if filhos:
            yield from criar_arvore(
                servico, filhos, pasta["id"], etiqueta or "", _profundidade + 1
            )


def achar_por_caminho(servico, caminho: str, raiz_id: str = "root") -> dict | None:
    """
    Desce um caminho separado por barras a partir de uma raiz.

        achar_por_caminho(s, 'GESTÃO DE RISCOS/CLIENTES/GRUPO-DIAMANTE')

    Devolve a pasta final, ou None se algum degrau não existir.
    """
    achada, _falhou, _onde = achar_por_caminho_detalhado(servico, caminho, raiz_id)
    return achada


def achar_por_caminho_detalhado(
    servico, caminho: str, raiz_id: str = "root"
) -> tuple[dict | None, str | None, dict]:
    """
    Como achar_por_caminho, mas diz ONDE o caminho quebrou.

    Devolve (pasta, degrau_que_faltou, ultima_pasta_valida). Serve para o
    programa dizer 'achei GESTÃO DE RISCOS, mas não achei CLIENTES dentro
    dela — o que existe ali é isto' em vez de só 'não achei'.
    """
    atual = {"id": raiz_id, "name": "Meu Drive"}
    for parte in [p for p in caminho.split("/") if p]:
        achada = achar_pasta(servico, parte, atual["id"])
        if not achada:
            return None, parte, atual
        atual = achada
    return atual, None, atual


# Quantos pais entram numa consulta só. A consulta do Drive tem limite de
# tamanho, e estourar dá um erro difícil de ler; 25 ids cabem com folga.
PAIS_POR_CONSULTA = 25


def listar_filhos_de_varios(servico, pais: list[str]) -> dict[str, list[dict]]:
    """
    Os filhos diretos de várias pastas numa consulta só, agrupados pelo pai.

    É o que permite ler uma árvore por nível em vez de pasta por pasta.
    GRUPO-DIAMANTE tem 440 pastas: lê-las uma a uma custava 440 chamadas e
    minutos de espera; por nível, com 25 pais por chamada, custa umas vinte.

    Devolve {id_do_pai: [filhos]}. Pai sem filho não aparece. Cada filho traz
    também `parents`, porque é por ele que se sabe de quem é.

    Sem repetidos dentro de cada lote: a paginação do Drive devolve a mesma
    entrada em duas páginas quando a pasta muda durante a varredura. O
    conjunto é por lote, e não por chamada inteira, porque um arquivo com dois
    pais em lotes diferentes tem de aparecer sob os dois.
    """
    por_pai: dict[str, list[dict]] = {}
    for inicio in range(0, len(pais), PAIS_POR_CONSULTA):
        lote = pais[inicio : inicio + PAIS_POR_CONSULTA]
        no_lote = set(lote)
        consulta = (
            "(" + " or ".join(f"'{_escapar(p)}' in parents" for p in lote) + ")"
            " and trashed = false"
        )
        vistos: set[str] = set()
        token = None
        while True:
            resposta = (
                servico.files()
                .list(
                    q=consulta,
                    spaces="drive",
                    fields="nextPageToken, files(id, name, mimeType, size, parents)",
                    pageSize=1000,
                    pageToken=token,
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True,
                )
                .execute()
            )
            for arquivo in resposta.get("files", []):
                if arquivo["id"] in vistos:
                    continue
                vistos.add(arquivo["id"])
                for pai in arquivo.get("parents", []):
                    if pai in no_lote:
                        por_pai.setdefault(pai, []).append(arquivo)
            token = resposta.get("nextPageToken")
            if not token:
                break
    return por_pai


def ler_arvore(servico, pasta_id: str, incluir_arquivos: bool = False) -> dict:
    """
    Lê a árvore que existe no Drive e devolve na mesma forma que modelo.py
    produz, para as duas poderem ser comparadas.

    Com incluir_arquivos, cada pasta ganha uma chave '__arquivos__' com a
    lista de nomes dos arquivos diretos. A auditoria usa isso para achar
    arquivo solto onde o modelo só espera pasta.

    Lê por nível, não pasta por pasta: todos os pais de um nível vão juntos
    numa consulta (ver listar_filhos_de_varios). A saída é a mesma de antes,
    chave por chave e na mesma ordem — '__arquivos__' primeiro, depois as
    pastas em ordem de nome, e nome repetido fica com a última — para a
    auditoria não mudar em nada.
    """
    raiz: dict = {}
    nos = {pasta_id: raiz}
    nivel = [pasta_id]
    while nivel:
        filhos_por_pai = listar_filhos_de_varios(servico, nivel)
        proximo: list[str] = []
        for pai_id in nivel:
            no = nos[pai_id]
            filhos = filhos_por_pai.get(pai_id, [])
            arquivos = [f for f in filhos if f["mimeType"] != MIME_PASTA]
            pastas = [f for f in filhos if f["mimeType"] == MIME_PASTA]

            if incluir_arquivos:
                no["__arquivos__"] = [a["name"] for a in arquivos]

            for pasta in sorted(pastas, key=lambda p: p["name"]):
                filho: dict = {}
                no[pasta["name"]] = filho
                nos[pasta["id"]] = filho
                proximo.append(pasta["id"])
        nivel = proximo
    return raiz


def contar_arquivos(servico, pasta_id: str) -> int:
    """Quantos arquivos há na pasta e em tudo abaixo dela."""
    total = 0
    for filho in listar_filhos(servico, pasta_id):
        if filho["mimeType"] == MIME_PASTA:
            total += contar_arquivos(servico, filho["id"])
        else:
            total += 1
    return total
