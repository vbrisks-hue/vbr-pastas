"""
Um Drive de mentira, em memória, com a mesma cara da API do Google.

Serve para rodar o programa inteiro — criar, mover, renomear, etiquetar —
sem tocar no Drive de verdade. Não é um mock complacente: ele reproduz as
armadilhas que a migração de setembro encontrou. Em particular, deixa duas
pastas com o mesmo nome conviverem no mesmo pai, que é exatamente o que o
Drive faz e quase nenhum banco de dados faz.

Não vai para produção. Fica junto porque o teste vale mais quando mora ao
lado do código que ele testa.
"""

from __future__ import annotations

import re
from itertools import count

MIME_PASTA = "application/vnd.google-apps.folder"


class DriveFalso:
    def __init__(self):
        self.itens: dict[str, dict] = {
            "root": {
                "id": "root",
                "name": "Meu Drive",
                "mimeType": MIME_PASTA,
                "parents": [],
                "appProperties": {},
                "trashed": False,
            }
        }
        self._sequencia = count(1)
        self.chamadas: list[str] = []

    # -- helpers de teste ---------------------------------------------------

    def novo_id(self) -> str:
        return f"id{next(self._sequencia)}"

    def semear(self, caminho: str) -> str:
        """Cria um caminho inteiro e devolve o id da última pasta."""
        atual = "root"
        for parte in [p for p in caminho.split("/") if p]:
            achada = [
                i
                for i in self.itens.values()
                if i["name"] == parte and atual in i["parents"] and not i["trashed"]
            ]
            atual = achada[0]["id"] if achada else self._criar(parte, atual)
        return atual

    def _criar(self, nome, pai, mime=MIME_PASTA, props=None) -> str:
        novo = self.novo_id()
        self.itens[novo] = {
            "id": novo,
            "name": nome,
            "mimeType": mime,
            "parents": [pai] if pai else [],
            "appProperties": dict(props or {}),
            "trashed": False,
        }
        return novo

    def caminho_de(self, item_id: str) -> str:
        partes = []
        atual = item_id
        while atual and atual != "root":
            item = self.itens[atual]
            partes.append(item["name"])
            atual = item["parents"][0] if item["parents"] else None
        return "/".join(reversed(partes))

    def desenhar(self, raiz_id: str, nivel: int = 0) -> list[str]:
        linhas = []
        filhos = sorted(
            (i for i in self.itens.values() if raiz_id in i["parents"] and not i["trashed"]),
            key=lambda x: x["name"],
        )
        for f in filhos:
            marca = "" if f["mimeType"] == MIME_PASTA else "  (arquivo)"
            linhas.append("  " * nivel + f["name"] + marca)
            if f["mimeType"] == MIME_PASTA:
                linhas.extend(self.desenhar(f["id"], nivel + 1))
        return linhas

    def contar_pastas(self, raiz_id: str) -> int:
        total = 0
        for i in self.itens.values():
            if raiz_id in i["parents"] and not i["trashed"] and i["mimeType"] == MIME_PASTA:
                total += 1 + self.contar_pastas(i["id"])
        return total

    # -- a cara da API ------------------------------------------------------

    def files(self):
        return _Arquivos(self)


class _Arquivos:
    def __init__(self, drive: DriveFalso):
        self.d = drive

    # Cada método devolve um objeto com .execute(), como a biblioteca do Google.

    def list(self, q="", fields="", pageSize=None, pageToken=None, **_):
        return _Resposta(lambda: self._list(q, fields))

    def create(self, body=None, fields="", media_body=None, **_):
        return _Resposta(lambda: self._create(body or {}, media_body))

    def update(self, fileId=None, body=None, addParents=None, removeParents=None, **_):
        return _Resposta(
            lambda: self._update(fileId, body or {}, addParents, removeParents)
        )

    def get(self, fileId=None, fields="", **_):
        return _Resposta(lambda: self._get(fileId, fields))

    # -- implementação ------------------------------------------------------

    def _visiveis(self):
        return [i for i in self.d.itens.values() if not i["trashed"]]

    def _list(self, q, fields):
        self.d.chamadas.append(f"list {q}")
        achados = self._visiveis()

        # Um pai só ('x' in parents) ou vários de uma vez, como a leitura por
        # nível pergunta: ('x' in parents or 'y' in parents or ...).
        pais = re.findall(r"'([^']+)' in parents", q)
        if pais:
            achados = [i for i in achados if any(p in i["parents"] for p in pais)]

        nome = re.search(r"name = '((?:[^'\\]|\\.)*)'", q)
        if nome:
            alvo = nome.group(1).replace("\\'", "'").replace("\\\\", "\\")
            achados = [i for i in achados if i["name"] == alvo]

        if f"mimeType = '{MIME_PASTA}'" in q:
            achados = [i for i in achados if i["mimeType"] == MIME_PASTA]

        prop = re.search(
            r"appProperties has \{ key='([^']+)' and value='((?:[^'\\]|\\.)*)' \}", q
        )
        if prop:
            chave = prop.group(1)
            valor = prop.group(2).replace("\\'", "'").replace("\\\\", "\\")
            achados = [i for i in achados if i["appProperties"].get(chave) == valor]

        saida = []
        for i in achados:
            item = {"id": i["id"], "name": i["name"], "mimeType": i["mimeType"]}
            if "appProperties" in fields:
                item["appProperties"] = dict(i["appProperties"])
            if "parents" in fields:
                item["parents"] = list(i["parents"])
            saida.append(item)
        return {"files": saida}

    def _create(self, body, media_body):
        mime = body.get("mimeType", "text/plain" if media_body is not None else MIME_PASTA)
        pais = body.get("parents") or []
        novo = self.d._criar(
            body.get("name", "sem nome"),
            pais[0] if pais else None,
            mime,
            body.get("appProperties"),
        )
        self.d.chamadas.append(f"create {body.get('name')}")
        return {"id": novo, "name": body.get("name")}

    def _update(self, file_id, body, add_parents, remove_parents):
        item = self.d.itens[file_id]
        if "name" in body:
            self.d.chamadas.append(f"renomear {item['name']} -> {body['name']}")
            item["name"] = body["name"]
        if "appProperties" in body:
            for chave, valor in body["appProperties"].items():
                if valor is None:
                    item["appProperties"].pop(chave, None)
                else:
                    item["appProperties"][chave] = valor
        if remove_parents:
            for pai in remove_parents.split(","):
                if pai in item["parents"]:
                    item["parents"].remove(pai)
        if add_parents:
            self.d.chamadas.append(f"mover {item['name']}")
            for pai in add_parents.split(","):
                if pai not in item["parents"]:
                    item["parents"].append(pai)
        return {
            "id": item["id"],
            "name": item["name"],
            "parents": list(item["parents"]),
        }

    def _get(self, file_id, fields):
        item = self.d.itens[file_id]
        saida = {"id": item["id"], "name": item["name"]}
        if "parents" in fields:
            saida["parents"] = list(item["parents"])
        if "appProperties" in fields:
            saida["appProperties"] = dict(item["appProperties"])
        return saida


class _Resposta:
    def __init__(self, funcao):
        self.funcao = funcao

    def execute(self):
        return self.funcao()


# ---------------------------------------------------------------------------
# O Drive de demonstração.
#
# É o que a tela mostra quando roda com --falso: um funil com três
# originações — uma delas parada há tempo demais —, uma encerrada com motivo,
# e um cliente com dois ativos. Serve para desenvolver e demonstrar a tela
# sem credencial nenhuma, e para os testes dela.
#
# As listas de subpastas vêm de modelo.py, não daqui: se o modelo mudar, o
# exemplo muda junto.
# ---------------------------------------------------------------------------


def _semear_arvore(d: DriveFalso, arvore: dict, pai: str) -> None:
    for nome, filhos in arvore.items():
        novo = d._criar(nome, pai)
        _semear_arvore(d, filhos, novo)


def com_exemplo() -> DriveFalso:
    import modelo

    d = DriveFalso()
    clientes = d.semear("GESTAO DE RISCOS/CLIENTES")
    funil = d.semear("GESTAO DE RISCOS/ORIGINACAO")

    # O funil: aberta há meses, aberta há pouco, e uma que passou da paciência.
    for nome in ("2026-03_CVCP", "2026-08_XPTO", "2023-01_ANTIGA"):
        pasta = d._criar(nome, funil, props={"vbr": "vbr/ORIGINACAO/" + modelo.titulo_de(nome)})
        _semear_arvore(d, modelo.arvore_de_originacao(), pasta)

    # Uma que não fechou: fica em ZZ-ENCERRADAS com data, motivo e o bilhete.
    encerradas = d._criar(modelo.ENCERRADAS, funil)
    fulano = d._criar(
        "2025-11_FULANO",
        encerradas,
        props={
            "vbr": "vbr/ORIGINACAO/FULANO",
            drive_chave_encerramento(): "2025-11-20|ficou com a corretora atual",
        },
    )
    _semear_arvore(d, modelo.arvore_de_originacao(), fulano)
    d._criar(modelo.BILHETE_DE_ENCERRAMENTO, fulano, mime="text/plain")

    # Um cliente com mandato: originação no modelo anterior (de quatro), uma
    # frente no grupo e dois ativos com acervo, um ramo e uma frente cada.
    grupo = d._criar("GRUPO-DIAMANTE", clientes, props={"vbr": "vbr/GRUPO-DIAMANTE"})
    orig = d._criar(modelo.ORIGINACAO, grupo)
    for sub in modelo.ORIGINACAO_SUBPASTAS_ANTERIOR:
        d._criar(sub, orig)
    _semear_arvore(
        d,
        modelo.arvore_de_promocao(
            ativos=["CTJL", "PECEM-I"],
            frentes_do_grupo=[("2026-07_RFP-CORRETORA", "CONCORRENCIA")],
            frentes_por_ativo={
                "CTJL": [("2026-05_VISITA-TECNICA-CTJL", "VISITA-TECNICA")],
                "PECEM-I": [("2026-07_RENOVACAO-RO", "RENOVACAO")],
            },
        ),
        grupo,
    )
    for ativo in ("CTJL", "PECEM-I"):
        apolices = d.semear(f"GESTAO DE RISCOS/CLIENTES/GRUPO-DIAMANTE/{ativo}/APOLICES")
        _semear_arvore(d, modelo.arvore_do_ramo("RO-BI"), apolices)

    # Uma frente da migração de 14/09, atrás do caderno v4 — como as seis de
    # verdade: 06 com o nome antigo e sem a COMUNICACOES. É o que o Alinhar
    # conserta, e a demonstração precisa de uma para mostrar.
    frentes_grupo = d.semear("GESTAO DE RISCOS/CLIENTES/GRUPO-DIAMANTE/FRENTES")
    velha = d._criar("2026-06_UNIFICACAO-D-O", frentes_grupo)
    for sub in ("01-INSUMOS", "02-TRABALHOS", "03-ENTREGAS", "04-COTACOES-RECEBIDAS",
                "05-ANALISE-COMPARATIVA", "06-DECISAO-EMISSAO"):
        pasta = d._criar(sub, velha)
        if sub == "06-DECISAO-EMISSAO":
            d._criar("apolice D-O emitida.pdf", pasta, mime="application/pdf")

    d.chamadas.clear()
    return d


def drive_chave_encerramento() -> str:
    """A chave da propriedade de encerramento é do drive.py; importada tarde
    para o Drive falso continuar não dependendo dele fora do exemplo."""
    import drive

    return drive.CHAVE_ENCERRAMENTO
