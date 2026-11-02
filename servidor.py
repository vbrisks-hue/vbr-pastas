#!/usr/bin/env python3
"""
A tela do vbr-pastas: um servidor local, em Python puro, que serve uma
página e chama os módulos que já existem.

    python3 servidor.py            abre a tela contra o Drive de verdade
    python3 servidor.py --falso    abre a tela contra um Drive de demonstração,
                                   em memória, sem credencial nenhuma

Nada aqui reimplementa o programa. O modelo continua em modelo.py, o Drive
em drive.py, o comportamento de cada operação em vbr_pastas.py. O servidor
só traduz: JSON para dentro, JSON para fora.

Três garantias que a página não pode contornar, porque moram aqui:

  1. Toda escrita passa por um plano. O plano recebe uma senha de uso único,
     e é o plano guardado — não o que a página mandar depois — que se
     executa. A página não consegue executar o que não mostrou.
  2. Só a própria página fala com este servidor: escrita com Origin de outro
     site é recusada. Qualquer aba aberta no navegador alcança 127.0.0.1.
  3. Escuta só em 127.0.0.1. Ninguém na rede alcança.
"""

from __future__ import annotations

import argparse
import errno
import json
import os
import secrets
import sys
import threading
import time
import traceback
import urllib.request
import webbrowser
from datetime import date
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import config
import drive
import modelo
import vbr_pastas
import alinhar as alinhamento
from lancador import Lancador
from auditoria import AVISO, ERRO, NOTA, auditar_cliente, auditar_funil

ENDERECO = "127.0.0.1"
PORTA_PADRAO = 8765  # longe das do MAMP: 8888, 8889, 3306
# A demonstração tem porta própria: com o programa de fundo sempre no ar na
# 8765, `--falso` na mesma porta abriria a tela de verdade achando que era
# a de mentira.
PORTA_DEMO = 8766
PAGINA = Path(__file__).with_name("pagina.html")
ATALHO = Path(__file__).with_name("VBR Pastas.command")

# Um plano que ficou meia hora na tela pode não descrever mais o Drive.
VALIDADE_DO_PLANO = 30 * 60


class ErroDaTela(Exception):
    """Um erro que o usuário entende e resolve. A frase vai para a página."""


# ---------------------------------------------------------------------------
# A aplicação — sem HTTP. Recebe e devolve dicionários, para ser testável
# sem servidor e para o servidor ficar magro.
# ---------------------------------------------------------------------------


class Tela:
    def __init__(self, conectar, modo: str, caminho_raiz: str, caminho_funil: str,
                 paciencia: int = 12, lancador: Lancador | None = None):
        self._conectar = conectar
        self.lancador = lancador
        self._servico = None
        self.modo = modo  # "falso" ou "drive"
        self.caminho_raiz = caminho_raiz.strip("/")
        self.caminho_funil = caminho_funil.strip("/")
        self.paciencia = paciencia
        # Uma conversa com o Drive por vez: duas escritas simultâneas na mesma
        # pasta é como nascem as duplicatas.
        self._tranca = threading.RLock()
        self._planos: dict[str, dict] = {}

    # -- infraestrutura -----------------------------------------------------

    def servico(self):
        """Conecta na primeira vez que alguém precisa, não ao subir: a página
        tem de abrir mesmo que a autorização do Google ainda esteja por fazer."""
        if self._servico is None:
            self._servico = self._conectar()
        return self._servico

    def estado(self) -> dict:
        return {
            "modo": self.modo,
            "raiz": self.caminho_raiz,
            "funil": self.caminho_funil,
            "paciencia": self.paciencia,
            "competencia_hoje": modelo.competencia_de_hoje(),
            "hoje": date.today().isoformat(),
            "atalho_executavel": os.access(ATALHO, os.X_OK) if ATALHO.exists() else None,
        }

    def modelo_json(self) -> dict:
        """O modelo, como está em modelo.py. A página não sabe nada disto de cor."""
        return {
            "tipos_frente": [
                {"codigo": tipo, "descricao": spec["descricao"], "quando": spec["quando"],
                 "subpastas": list(spec["subpastas"])}
                for tipo, spec in modelo.TIPOS_FRENTE.items()
            ],
            "originacao": {
                "nome_no_cliente": modelo.ORIGINACAO,
                "subpastas": list(modelo.ORIGINACAO_SUBPASTAS),
                "netos": {k: list(v) for k, v in modelo.ORIGINACAO_NETOS.items()},
            },
            "encerradas": modelo.ENCERRADAS,
            "bilhete": modelo.BILHETE_DE_ENCERRAMENTO,
            "acervo": {"nome": modelo.ACERVO, "subpastas": list(modelo.ACERVO_SUBPASTAS)},
            "apolices": {"nome": modelo.APOLICES, "ramo_subpastas": list(modelo.RAMO_SUBPASTAS),
                         "ramos_conhecidos": list(modelo.RAMOS_CONHECIDOS),
                         "ramos_renomeados": dict(modelo.RAMOS_RENOMEADOS)},
            "funil": FUNIL,
            "frentes": modelo.FRENTES,
        }

    def grafia(self, nome: str, competencia: str | None) -> dict:
        """A grafia da casa, para a página mostrar enquanto o usuário digita."""
        saida = {"grafia": modelo.normalizar(nome), "pasta": None, "erro": None}
        if competencia:
            try:
                saida["pasta"] = modelo.nome_de_originacao(competencia, nome)
            except ValueError as erro:
                saida["erro"] = str(erro)
        return saida

    # -- leitura --------------------------------------------------------------

    def _funil_ou_falta(self, servico):
        """
        Devolve (pasta_do_funil, None) se ela existe; (None, pai) se falta só
        o último degrau — o funil é pasta nova no Drive de quem já tinha
        CLIENTES, e criá-la faz parte da primeira originação. Qualquer outra
        quebra no caminho é erro, com a explicação de onde parou.
        """
        pasta, degrau, ultima = drive.achar_por_caminho_detalhado(servico, self.caminho_funil)
        if pasta:
            return pasta, None
        ultimo = [d for d in self.caminho_funil.split("/") if d][-1]
        if degrau == ultimo:
            return None, ultima
        raise ErroDaTela(self._frase_caminho_quebrado(servico, self.caminho_funil, degrau, ultima))

    def _funil(self, servico, passos: list | None = None):
        """O funil, criando a pasta se faltar só ela. Quem cria registra o passo."""
        pasta, pai = self._funil_ou_falta(servico)
        if pasta:
            return pasta
        nome = [d for d in self.caminho_funil.split("/") if d][-1]
        pasta, criada = drive.achar_ou_criar(servico, nome, pai["id"])
        if passos is not None:
            passos.append(_passo("+" if criada else "=", 0, f"{nome}   (a pasta do funil)"))
        return pasta

    def _raiz_clientes(self, servico):
        raiz, degrau, ultima = drive.achar_por_caminho_detalhado(servico, self.caminho_raiz)
        if raiz:
            return raiz
        raise ErroDaTela(self._frase_caminho_quebrado(servico, self.caminho_raiz, degrau, ultima))

    def _frase_caminho_quebrado(self, servico, caminho, degrau, ultima) -> str:
        vizinhas = sorted(
            f["name"] for f in drive.listar_filhos(servico, ultima["id"], so_pastas=True)
        )
        lista = ", ".join(vizinhas[:12]) + (" …" if len(vizinhas) > 12 else "")
        return (
            f"Não achei “{caminho}” no Drive. Cheguei até “{ultima['name']}”, mas lá "
            f"dentro não há “{degrau}”. O que existe ali: {lista or 'nada'}. "
            "Confira o caminho gravado na configuração do programa."
        )

    def funil(self) -> dict:
        with self._tranca:
            servico = self.servico()
            pasta, _pai = self._funil_ou_falta(servico)
            if not pasta:
                return {"existe": False, "caminho": self.caminho_funil, "abertas": [],
                        "encerradas": [], "paciencia": self.paciencia}

            abertas, encerradas = [], []
            for f in drive.listar_filhos(servico, pasta["id"], so_pastas=True, com_propriedades=True):
                if f["name"] == modelo.ENCERRADAS:
                    encerradas = drive.listar_filhos(servico, f["id"], so_pastas=True,
                                                     com_propriedades=True)
                else:
                    abertas.append(f)

        hoje = date.today()

        def idade(nome: str) -> int | None:
            casamento = modelo.PADRAO_DATADO.fullmatch(nome.strip())
            if not casamento:
                return None
            ano, mes = int(casamento.group(1)), int(casamento.group(2))
            return (hoje.year - ano) * 12 + (hoje.month - mes)

        saida_abertas = []
        for f in sorted(abertas, key=lambda x: x["name"]):
            meses = idade(f["name"])
            saida_abertas.append({
                "nome": f["name"], "titulo": modelo.titulo_de(f["name"]), "meses": meses,
                "parada": (meses or 0) >= self.paciencia,
            })
        saida_encerradas = []
        for f in sorted(encerradas, key=lambda x: x["name"], reverse=True):
            registro = (f.get("appProperties") or {}).get(drive.CHAVE_ENCERRAMENTO, "")
            quando, _, motivo = registro.partition("|")
            saida_encerradas.append({
                "nome": f["name"], "titulo": modelo.titulo_de(f["name"]),
                "quando": quando or None, "motivo": motivo,
            })
        return {"existe": True, "caminho": self.caminho_funil, "abertas": saida_abertas,
                "encerradas": saida_encerradas, "paciencia": self.paciencia}

    # -- planos ---------------------------------------------------------------

    def _guardar(self, tipo: str, dados: dict, plano: dict) -> str:
        """Guarda o plano e devolve a senha de uso único que o executa."""
        senha = secrets.token_urlsafe(18)
        with self._tranca:
            agora = time.time()
            for chave in [k for k, v in self._planos.items()
                          if agora - v["hora"] > VALIDADE_DO_PLANO]:
                del self._planos[chave]
            self._planos[senha] = {"tipo": tipo, "dados": dados, "plano": plano, "hora": agora}
        return senha

    def plano_originar(self, d: dict) -> dict:
        nome = (d.get("nome") or "").strip()
        if not nome:
            raise ErroDaTela("Dê um nome ao prospecto.")
        competencia = (d.get("competencia") or modelo.competencia_de_hoje()).strip()
        try:
            pasta_nome = modelo.nome_de_originacao(competencia, nome)
        except ValueError as erro:
            raise ErroDaTela(str(erro))
        if not modelo.titulo_de(pasta_nome):
            raise ErroDaTela("Esse nome não deixa nada aproveitável na grafia da casa.")

        avisos = []
        with self._tranca:
            servico = self.servico()
            funil, _pai = self._funil_ou_falta(servico)
            if funil:
                ja, encerrada = vbr_pastas.achar_originacao(servico, funil["id"], pasta_nome)
                if ja:
                    onde = f"em {modelo.ENCERRADAS}" if encerrada else "no funil"
                    raise ErroDaTela(
                        f"Já existe uma originação com esse nome {onde}: {ja['name']}."
                        + (" Para trazer de volta, use Reabrir." if encerrada else "")
                    )
            else:
                avisos.append(f"A pasta do funil ainda não existe ({self.caminho_funil}). "
                              "Ela será criada junto.")

        arvore = {pasta_nome: modelo.arvore_de_originacao()}
        plano = {
            "titulo": "Nova originação",
            "destino": self.caminho_funil,
            "partes": [{"rotulo": "CRIAR", "linhas": modelo.desenhar(arvore),
                        "total": modelo.contar(arvore)}],
            "avisos": avisos,
            "resumo": f"{modelo.contar(arvore)} pastas novas.",
        }
        return {"plano": plano, "senha": self._guardar("originar", {"pasta_nome": pasta_nome}, plano)}

    def plano_encerrar(self, d: dict) -> dict:
        nome = (d.get("nome") or "").strip()
        motivo = (d.get("motivo") or "").strip()
        if not nome:
            raise ErroDaTela("Qual originação?")
        if not motivo:
            raise ErroDaTela("Sem motivo, não encerro — o motivo é o que dá valor ao "
                             "registro quando o nome voltar.")
        with self._tranca:
            servico = self.servico()
            funil, _ = self._funil_ou_falta(servico)
            if not funil:
                raise ErroDaTela("A pasta do funil ainda não existe; não há o que encerrar.")
            pasta, ja_encerrada = vbr_pastas.achar_originacao(servico, funil["id"], nome)
            if not pasta:
                raise ErroDaTela(f"Não achei “{nome}” no funil.")
            if ja_encerrada:
                raise ErroDaTela(f"{pasta['name']} já está em {modelo.ENCERRADAS}.")

        quando = date.today().isoformat()
        plano = {
            "titulo": "Encerrar originação",
            "destino": f"{self.caminho_funil}/{modelo.ENCERRADAS}",
            "partes": [
                {"rotulo": "MOVER", "linhas": [
                    f"{self.caminho_funil}/{pasta['name']}",
                    f"  →  {self.caminho_funil}/{modelo.ENCERRADAS}/{pasta['name']}   (com tudo dentro)",
                ]},
                {"rotulo": "REGISTRAR", "linhas": [
                    f"{quando} — {motivo}",
                    f"no bilhete {modelo.BILHETE_DE_ENCERRAMENTO}, dentro da pasta, e numa "
                    "etiqueta invisível que o funil lê",
                ]},
            ],
            "avisos": ["Encerrada não é apagada. Se o nome voltar, Reabrir traz de volta."],
            "resumo": "Nenhuma pasta nova; uma muda de lugar.",
        }
        dados = {"pasta": pasta, "motivo": motivo, "quando": quando}
        return {"plano": plano, "senha": self._guardar("encerrar", dados, plano)}

    def plano_reabrir(self, d: dict) -> dict:
        nome = (d.get("nome") or "").strip()
        if not nome:
            raise ErroDaTela("Qual originação?")
        with self._tranca:
            servico = self.servico()
            funil, _ = self._funil_ou_falta(servico)
            if not funil:
                raise ErroDaTela("A pasta do funil ainda não existe; não há o que reabrir.")
            pasta, encerrada = vbr_pastas.achar_originacao(servico, funil["id"], nome)
            if not pasta:
                raise ErroDaTela(f"Não achei “{nome}” nem no funil nem em {modelo.ENCERRADAS}.")
            if not encerrada:
                raise ErroDaTela(f"{pasta['name']} já está aberta no funil.")
        plano = {
            "titulo": "Reabrir originação",
            "destino": self.caminho_funil,
            "partes": [{"rotulo": "MOVER", "linhas": [
                f"{self.caminho_funil}/{modelo.ENCERRADAS}/{pasta['name']}",
                f"  →  {self.caminho_funil}/{pasta['name']}",
            ]}],
            "avisos": [f"O {modelo.BILHETE_DE_ENCERRAMENTO} fica dentro da pasta: é a memória "
                       "de por que parou da outra vez."],
            "resumo": "Nenhuma pasta nova; uma volta ao funil.",
        }
        return {"plano": plano, "senha": self._guardar("reabrir", {"pasta": pasta}, plano)}

    def _ativos_e_frentes(self, d: dict):
        """
        Lê ativos e frentes do pedido da página, na forma que modelo.py espera.
        Serve à promoção e ao cliente novo, que pedem as mesmas coisas.
        """
        ativos, vistos = [], set()
        for livre in d.get("ativos") or []:
            if not str(livre).strip():
                continue
            ativo = modelo.normalizar(livre)
            if not ativo:
                raise ErroDaTela(f"O ativo “{livre}” não deixa nada aproveitável na grafia da casa.")
            if ativo not in vistos:
                vistos.add(ativo)
                ativos.append(ativo)

        frentes_grupo: list[tuple[str, str]] = []
        frentes_ativo: dict[str, list[tuple[str, str]]] = {}
        for i, fr in enumerate(d.get("frentes") or [], 1):
            titulo = (fr.get("titulo") or "").strip()
            if not titulo:
                raise ErroDaTela(f"A frente {i} está sem título.")
            tipo = (fr.get("tipo") or "").strip().upper()
            if tipo not in modelo.TIPOS_FRENTE:
                raise ErroDaTela(f"A frente “{titulo}” está sem tipo.")
            try:
                nome_frente = modelo.nome_de_frente(
                    (fr.get("competencia") or modelo.competencia_de_hoje()).strip(), titulo)
            except ValueError as erro:
                raise ErroDaTela(f"Frente “{titulo}”: {erro}")
            onde = modelo.normalizar(fr.get("onde") or "")
            if not onde:
                frentes_grupo.append((nome_frente, tipo))
            elif onde in vistos:
                frentes_ativo.setdefault(onde, []).append((nome_frente, tipo))
            else:
                raise ErroDaTela(f"A frente “{titulo}” aponta para o ativo “{onde}”, "
                                 "que não está na lista de ativos.")
        return ativos, frentes_grupo, frentes_ativo

    def plano_promover(self, d: dict) -> dict:
        nome = (d.get("nome") or "").strip()
        if not nome:
            raise ErroDaTela("Qual originação?")
        nome_cliente = modelo.normalizar(d.get("cliente") or "")
        if not nome_cliente:
            raise ErroDaTela("Dê o nome do cliente — é o nome da pasta em CLIENTES.")
        ativos, frentes_grupo, frentes_ativo = self._ativos_e_frentes(d)

        with self._tranca:
            servico = self.servico()
            funil, _ = self._funil_ou_falta(servico)
            origem, encerrada = (None, False)
            if funil:
                origem, encerrada = vbr_pastas.achar_originacao(servico, funil["id"], nome)
            if origem and encerrada:
                raise ErroDaTela(f"{origem['name']} está em {modelo.ENCERRADAS}. "
                                 "Reabra primeiro, depois promova.")

        arvore = modelo.arvore_de_promocao(
            ativos=ativos, frentes_do_grupo=frentes_grupo, frentes_por_ativo=frentes_ativo)
        destino = f"{self.caminho_raiz}/{nome_cliente}"
        avisos = []
        if origem:
            mover = {"rotulo": "MOVER", "linhas": [
                f"{self.caminho_funil}/{origem['name']}",
                f"  →  {destino}/{modelo.ORIGINACAO}   (com tudo dentro)",
            ]}
        else:
            # O terminal pergunta "continuar?" e segue com uma originação
            # vazia; aqui a pergunta é a própria confirmação do plano.
            avisos.append(f"Não achei “{nome}” no funil. Se confirmar, o cliente nasce com "
                          f"uma originação vazia em {modelo.ORIGINACAO}.")
            mover = {"rotulo": "CRIAR", "linhas": [f"{destino}/{modelo.ORIGINACAO}   (vazia)"]}
        criar = {"rotulo": "CRIAR", "linhas": [nome_cliente] +
                 ["    " + l for l in modelo.desenhar(arvore)],
                 "total": modelo.contar(arvore)}
        plano = {
            "titulo": "Promover: a originação vira cliente com mandato",
            "destino": destino,
            "partes": [mover, criar],
            "avisos": avisos,
            "resumo": f"{modelo.contar(arvore)} pastas novas"
                      + (", mais a originação que muda de lugar." if origem else "."),
        }
        dados = {"origem": origem, "nome_cliente": nome_cliente, "arvore": arvore}
        return {"plano": plano, "senha": self._guardar("promover", dados, plano)}

    # -- etapa 2: clientes, frentes, ramos ------------------------------------

    def destinos(self) -> dict:
        """
        Onde uma frente ou um ramo pode morar: cada cliente e cada ativo, lidos
        do Drive agora. A lista substitui o caminho digitado do terminal —
        metade dos avisos da primeira auditoria foi frente montada à mão.
        """
        fixas = {modelo.ORIGINACAO, modelo.APOLICES, modelo.FRENTES}
        with self._tranca:
            servico = self.servico()
            raiz = self._raiz_clientes(servico)
            clientes = sorted(drive.listar_filhos(servico, raiz["id"], so_pastas=True),
                              key=lambda c: c["name"])
            filhos = drive.listar_filhos_de_varios(servico, [c["id"] for c in clientes])
        lista = []
        for c in clientes:
            lista.append({"caminho": c["name"], "cliente": c["name"], "nome": c["name"], "nivel": "grupo"})
            for f in sorted(filhos.get(c["id"], []), key=lambda x: x["name"]):
                if f["mimeType"] != drive.MIME_PASTA or f["name"] in fixas:
                    continue
                lista.append({"caminho": f"{c['name']}/{f['name']}", "cliente": c["name"],
                              "nome": f["name"], "nivel": "ativo"})
        return {"raiz": self.caminho_raiz, "destinos": lista}

    def _destino(self, servico, caminho: str | None):
        """A pasta do cliente ou do ativo, resolvida pelo caminho agora — id
        guardado de memória não é confiável (armadilha 6)."""
        caminho = "/".join(p.strip() for p in (caminho or "").split("/") if p.strip())
        if not caminho:
            raise ErroDaTela("Escolha o cliente ou o ativo.")
        raiz = self._raiz_clientes(servico)
        dono = drive.achar_por_caminho(servico, caminho, raiz["id"])
        if not dono:
            raise ErroDaTela(f"Não achei “{caminho}” dentro de {self.caminho_raiz}. "
                             "Recarregue a lista de clientes.")
        return caminho, dono

    def plano_frente(self, d: dict) -> dict:
        titulo = (d.get("titulo") or "").strip()
        if not titulo:
            raise ErroDaTela("Dê um título à frente.")
        tipo = (d.get("tipo") or "").strip().upper()
        if tipo not in modelo.TIPOS_FRENTE:
            raise ErroDaTela("Escolha o tipo da frente.")
        try:
            nome = modelo.nome_de_frente((d.get("competencia") or modelo.competencia_de_hoje()).strip(), titulo)
        except ValueError as erro:
            raise ErroDaTela(str(erro))
        if not modelo.titulo_de(nome):
            raise ErroDaTela("Esse título não deixa nada aproveitável na grafia da casa.")

        with self._tranca:
            servico = self.servico()
            caminho, dono = self._destino(servico, d.get("caminho"))
            tem_frentes = drive.achar_pasta(servico, modelo.FRENTES, dono["id"]) is not None
            ja = None
            if tem_frentes:
                pasta_frentes = drive.achar_pasta(servico, modelo.FRENTES, dono["id"])
                ja = drive.achar_pasta(servico, nome, pasta_frentes["id"])

        arvore = {nome: {sub: {} for sub in modelo.TIPOS_FRENTE[tipo]["subpastas"]}}
        avisos = []
        if not tem_frentes:
            avisos.append(f"A pasta {modelo.FRENTES} ainda não existe em {caminho}. Será criada junto.")
        if ja:
            avisos.append(f"Já existe {nome} ali. O que já existir é reaproveitado; nada é duplicado.")
        plano = {
            "titulo": "Nova frente",
            "destino": f"{self.caminho_raiz}/{caminho}/{modelo.FRENTES}",
            "partes": [{"rotulo": "CRIAR", "linhas": modelo.desenhar(arvore), "total": modelo.contar(arvore)}],
            "avisos": avisos,
            "resumo": f"{modelo.contar(arvore)} pastas novas, na forma {tipo}.",
        }
        return {"plano": plano, "senha": self._guardar("frente", {"caminho": caminho, "arvore": arvore}, plano)}

    def _executar_frente(self, servico, dados: dict) -> dict:
        caminho, dono = self._destino(servico, dados["caminho"])
        passos: list = []
        pasta_frentes, criada = drive.achar_ou_criar(servico, modelo.FRENTES, dono["id"])
        if criada:
            passos.append(_passo("+", 0, f"{modelo.FRENTES}   (não existia)"))
        c, e = self._criar(servico, dados["arvore"], pasta_frentes["id"],
                           vbr_pastas.ancora_de(caminho, modelo.FRENTES), passos)
        return {"passos": passos, "resumo": f"{c} pasta(s) criada(s), {e} já existia(m).",
                "mensagem": f"A frente está em {caminho}/{modelo.FRENTES}."}

    def _ramos(self, d: dict) -> list[str]:
        """Os ramos do pedido, na grafia da casa, sem repetido e sem nome antigo."""
        ramos, vistos = [], set()
        for livre in d.get("ramos") or []:
            if not str(livre).strip():
                continue
            ramo = modelo.normalizar(livre)
            if not ramo:
                raise ErroDaTela(f"O ramo “{livre}” não deixa nada aproveitável na grafia da casa.")
            novo = modelo.RAMOS_RENOMEADOS.get(ramo)
            if novo:
                raise ErroDaTela(f"“{ramo}” é o nome antigo: a casa passou a chamar de {novo}.")
            if ramo not in vistos:
                vistos.add(ramo)
                ramos.append(ramo)
        return ramos

    def plano_ramo(self, d: dict) -> dict:
        ramos = self._ramos(d)
        if not ramos:
            raise ErroDaTela("Diga pelo menos um ramo.")

        with self._tranca:
            servico = self.servico()
            caminho, dono = self._destino(servico, d.get("caminho"))
            tem_apolices = drive.achar_pasta(servico, modelo.APOLICES, dono["id"]) is not None

        arvore: dict = {}
        for ramo in ramos:
            arvore.update(modelo.arvore_do_ramo(ramo))
        avisos = []
        if not tem_apolices:
            avisos.append(f"A pasta {modelo.APOLICES} ainda não existe em {caminho}. Será criada junto.")
        for ramo in ramos:
            if ramo not in modelo.RAMOS_CONHECIDOS:
                avisos.append(f"“{ramo}” não está na lista de ramos da casa. Pode ser ramo novo; "
                              "a auditoria vai apontar como nota, para conferência.")
        plano = {
            "titulo": "Novo ramo de apólice",
            "destino": f"{self.caminho_raiz}/{caminho}/{modelo.APOLICES}",
            "partes": [{"rotulo": "CRIAR", "linhas": modelo.desenhar(arvore), "total": modelo.contar(arvore)}],
            "avisos": avisos,
            "resumo": f"{modelo.contar(arvore)} pastas novas: {len(ramos)} ramo(s), cada um com "
                      + ", ".join(modelo.RAMO_SUBPASTAS) + ".",
        }
        return {"plano": plano, "senha": self._guardar("ramo", {"caminho": caminho, "arvore": arvore}, plano)}

    def _executar_ramo(self, servico, dados: dict) -> dict:
        caminho, dono = self._destino(servico, dados["caminho"])
        passos: list = []
        pasta_apolices, criada = drive.achar_ou_criar(servico, modelo.APOLICES, dono["id"])
        if criada:
            passos.append(_passo("+", 0, f"{modelo.APOLICES}   (não existia)"))
        c, e = self._criar(servico, dados["arvore"], pasta_apolices["id"],
                           vbr_pastas.ancora_de(caminho, modelo.APOLICES), passos)
        return {"passos": passos, "resumo": f"{c} pasta(s) criada(s), {e} já existia(m).",
                "mensagem": "A apólice mora em VIGENTE; a que venceu vai para HISTORICO."}

    def plano_ativo(self, d: dict) -> dict:
        """
        Um ativo novo em cliente que já existe. Até aqui ativo só nascia no
        Promover e no cliente novo; um mandato que ganha uma usina não tinha
        por onde entrar. A árvore é a que o modelo já define para ativo —
        pedida a ele, não escrita aqui.
        """
        cliente = "/".join(p.strip() for p in (d.get("cliente") or "").split("/") if p.strip())
        if not cliente:
            raise ErroDaTela("Escolha o cliente.")
        if "/" in cliente:
            raise ErroDaTela("Ativo mora no cliente, não dentro de outro ativo.")
        ativo = modelo.normalizar(d.get("nome") or "")
        if not ativo:
            raise ErroDaTela("Dê o nome do ativo.")
        if ativo in (modelo.ORIGINACAO, modelo.APOLICES, modelo.FRENTES, modelo.ACERVO):
            raise ErroDaTela(f"“{ativo}” é nome de pasta do modelo; não serve para ativo.")
        ramos = self._ramos(d)
        frentes = [dict(fr, onde=ativo) for fr in (d.get("frentes") or [])]
        _ativos, _grupo, frentes_ativo = self._ativos_e_frentes({"ativos": [ativo], "frentes": frentes})

        with self._tranca:
            servico = self.servico()
            cliente, dono = self._destino(servico, cliente)
            if drive.achar_pasta(servico, ativo, dono["id"]):
                raise ErroDaTela(f"Já existe {ativo} em {cliente}. Para abrir frente ou ramo nele, "
                                 "use os botões da linha dele.")

        # A parte do ativo na árvore que o modelo monta para uma promoção.
        arvore_ativo = modelo.arvore_de_promocao(ativos=[ativo], frentes_por_ativo=frentes_ativo)[ativo]
        for ramo in ramos:
            arvore_ativo[modelo.APOLICES].update(modelo.arvore_do_ramo(ramo))
        arvore = {ativo: arvore_ativo}
        avisos = [f"“{r}” não está na lista de ramos da casa. Pode ser ramo novo; a auditoria vai "
                  "apontar como nota." for r in ramos if r not in modelo.RAMOS_CONHECIDOS]
        plano = {
            "titulo": "Ativo novo",
            "destino": f"{self.caminho_raiz}/{cliente}",
            "partes": [{"rotulo": "CRIAR", "linhas": modelo.desenhar(arvore), "total": modelo.contar(arvore)}],
            "avisos": avisos,
            "resumo": f"{modelo.contar(arvore)} pastas novas. Nada do que já existe em {cliente} é tocado.",
        }
        return {"plano": plano, "senha": self._guardar("ativo", {"cliente": cliente, "arvore": arvore}, plano)}

    def _executar_ativo(self, servico, dados: dict) -> dict:
        cliente, dono = self._destino(servico, dados["cliente"])
        passos: list = []
        c, e = self._criar(servico, dados["arvore"], dono["id"], vbr_pastas.ancora_de(cliente), passos)
        return {"passos": passos, "resumo": f"{c} pasta(s) criada(s), {e} já existia(m).",
                "mensagem": "O ativo já aparece na lista de Clientes, com Frente e Ramo."}

    def plano_cliente(self, d: dict) -> dict:
        """Cliente novo, com mandato. Sem mandato é originação, e o lugar é o funil."""
        if not d.get("mandato"):
            raise ErroDaTela("Sem mandato assinado não é cliente ainda: é originação, e o lugar dela "
                             "é o funil. Use “+ Nova originação”.")
        nome = modelo.normalizar(d.get("nome") or "")
        if not nome:
            raise ErroDaTela("Dê o nome do cliente — é o nome da pasta em CLIENTES.")
        ativos, frentes_grupo, frentes_ativo = self._ativos_e_frentes(d)

        with self._tranca:
            servico = self.servico()
            raiz = self._raiz_clientes(servico)
            existente = drive.achar_pasta(servico, nome, raiz["id"])

        arvore = modelo.arvore_do_cliente(nome, ativos=ativos, frentes_do_grupo=frentes_grupo,
                                          frentes_por_ativo=frentes_ativo)
        avisos = []
        if existente:
            avisos.append(f"Já existe uma pasta {nome} em CLIENTES. O que já existir é reaproveitado; "
                          "nada é duplicado.")
        plano = {
            "titulo": "Cliente novo, com mandato",
            "destino": self.caminho_raiz,
            "partes": [{"rotulo": "CRIAR", "linhas": modelo.desenhar(arvore), "total": modelo.contar(arvore)}],
            "avisos": avisos,
            "resumo": f"{modelo.contar(arvore)} pastas novas.",
        }
        return {"plano": plano, "senha": self._guardar("cliente", {"arvore": arvore}, plano)}

    def _executar_cliente(self, servico, dados: dict) -> dict:
        raiz = self._raiz_clientes(servico)
        passos: list = []
        c, e = self._criar(servico, dados["arvore"], raiz["id"], vbr_pastas.ANCORA, passos)
        return {"passos": passos, "resumo": f"{c} pasta(s) criada(s), {e} já existia(m).",
                "mensagem": "Frente se abre quando o trabalho começa; ramo, quando há apólice."}

    # -- etapa 2: auditoria ---------------------------------------------------

    def auditoria(self, alvo: str | None) -> dict:
        """
        A auditoria de um cliente ou do funil, com os achados agrupados por
        família em vez da lista corrida do terminal. Só lê.
        """
        alvo = (alvo or "").strip()
        if not alvo:
            raise ErroDaTela("Escolha o que conferir: um cliente ou o funil.")
        with self._tranca:
            servico = self.servico()
            if alvo == FUNIL:
                funil, _ = self._funil_ou_falta(servico)
                if not funil:
                    raise ErroDaTela("A pasta do funil ainda não existe; não há o que conferir.")
                arvore = drive.ler_arvore(servico, funil["id"], incluir_arquivos=True)
                relatorio = auditar_funil(arvore, self.paciencia)
                nome = "o funil"
            else:
                raiz = self._raiz_clientes(servico)
                pasta = drive.achar_por_caminho(servico, alvo, raiz["id"])
                if not pasta:
                    raise ErroDaTela(f"Não achei o cliente “{alvo}” em {self.caminho_raiz}.")
                arvore = drive.ler_arvore(servico, pasta["id"], incluir_arquivos=True)
                relatorio = auditar_cliente(pasta["name"], arvore)
                nome = pasta["name"]

        def no_da_arvore(caminho: str) -> dict | None:
            """Desce a árvore lida pelo caminho do achado (que começa no cliente)."""
            no = arvore
            for parte in caminho.split("/")[1:]:
                no = no.get(parte) if isinstance(no, dict) else None
                if no is None:
                    return None
            return no

        gravidades = []
        for gravidade, titulo in ((ERRO, "Erros"), (AVISO, "Avisos"), (NOTA, "Notas")):
            achados = relatorio.por_gravidade(gravidade)
            familias: dict[str, dict] = {}
            for a in achados:
                familia, conhecida = familia_de(a.mensagem)
                grupo = familias.setdefault(familia, {"nome": familia, "conhecida": conhecida, "itens": []})
                item = {"caminho": a.caminho, "mensagem": a.mensagem, "sugestao": a.sugestao}
                # Frente fora de qualquer tipo é o que o Alinhar conserta: a
                # página ganha, junto do achado, o que precisa para oferecer.
                if alvo != FUNIL and "não bate com nenhum tipo" in a.mensagem:
                    no = no_da_arvore(a.caminho)
                    presentes = [k for k in (no or {}) if k != "__arquivos__"]
                    if presentes:
                        item["alinhar"] = {"caminho": a.caminho, "presentes": presentes,
                                           "tipo_proximo": modelo.tipo_mais_proximo(presentes)[0]}
                grupo["itens"].append(item)
            gravidades.append({"gravidade": gravidade, "titulo": titulo, "total": len(achados),
                               "familias": list(familias.values())})
        return {
            "alvo": nome,
            "titulo": "Auditoria do funil" if alvo == FUNIL else f"Auditoria de {nome}",
            "limpo": relatorio.limpo(),
            "resumo": f"{len(relatorio.erros)} erro(s), {len(relatorio.avisos)} aviso(s), "
                      f"{len(relatorio.notas)} nota(s).",
            "gravidades": gravidades,
        }

    # -- etapa 3: o programa de fundo -----------------------------------------

    def sistema(self) -> dict:
        """O que a aba Sistema mostra: o programa, e o agente que o sobe com o Mac."""
        saida = self.estado()
        saida["python"] = sys.executable
        saida["pasta"] = str(Path(__file__).parent.resolve())
        saida["fundo"] = FUNDO
        saida["agente"] = self.lancador.situacao() if self.lancador else None
        return saida

    def plano_instalar(self, _d: dict) -> dict:
        if not self.lancador:
            raise ErroDaTela("Este servidor subiu sem o lançador; instale pelo Terminal: "
                             "python3 servidor.py --instalar")
        sit = self.lancador.situacao()
        avisos = []
        if sit["instalado"]:
            avisos.append("O agente já está instalado; será regravado com este Python e esta porta.")
        if not FUNDO:
            avisos.append("Este servidor foi aberto pelo atalho, e fica com a porta. O programa de "
                          "fundo sobe agora, espera, e assume assim que você fechar a janela do Terminal.")
        plano = {
            "titulo": "Subir com o Mac",
            "destino": str(self.lancador.plist),
            "partes": [{"rotulo": "GRAVAR E CARREGAR", "linhas": self.lancador.plano_de_instalacao()}],
            "avisos": avisos,
            "resumo": "Nada muda no Drive. Muda só o que sobe com a sua conta neste Mac.",
        }
        return {"plano": plano, "senha": self._guardar("instalar", {}, plano)}

    def _executar_instalar(self, _servico, _dados: dict) -> dict:
        try:
            passos = self.lancador.instalar()
        except RuntimeError as erro:
            raise ErroDaTela(str(erro))
        return {"passos": [_passo(p[0], 0, p[2:]) for p in passos],
                "resumo": "O VBR Pastas passa a subir com o Mac.",
                "mensagem": f"Daqui em diante, para abrir a tela: duplo clique em “{self.lancador.atalho_web.name}”, "
                            f"ou {self.lancador.endereco} no navegador. Pode fechar a janela do Terminal."}

    def plano_desinstalar(self, _d: dict) -> dict:
        if not self.lancador:
            raise ErroDaTela("Este servidor subiu sem o lançador; remova pelo Terminal: "
                             "python3 servidor.py --desinstalar")
        sit = self.lancador.situacao()
        if not sit["instalado"]:
            raise ErroDaTela("O agente não está instalado; não há o que remover.")
        avisos = []
        if FUNDO:
            avisos.append("Este servidor é o próprio programa de fundo: ao confirmar, ele para, e esta "
                          "página deixa de responder. Para abrir de novo, use o atalho “VBR Pastas.command”.")
        plano = {
            "titulo": "Deixar de subir com o Mac",
            "destino": str(self.lancador.plist),
            "partes": [{"rotulo": "DESCARREGAR E APAGAR", "linhas": [
                f"pedir ao launchd que descarregue {self.lancador.plist.stem}",
                f"apagar  {self.lancador.plist}",
                f"apagar  {self.lancador.atalho_web}",
            ]}],
            "avisos": avisos,
            "resumo": "Nada muda no Drive, nem no programa: só deixa de subir sozinho.",
        }
        return {"plano": plano, "senha": self._guardar("desinstalar", {}, plano)}

    def _executar_desinstalar(self, _servico, _dados: dict) -> dict:
        passos = self.lancador.desinstalar()
        return {"passos": [_passo(p[0], 0, p[2:]) for p in passos],
                "resumo": "O VBR Pastas deixa de subir com o Mac.",
                "mensagem": "O programa e as pastas continuam como estão."}

    # -- alinhar: uma frente atrás do modelo ---------------------------------

    def _frente(self, servico, caminho: str | None):
        """A pasta da frente, resolvida pelo caminho do achado (começa no cliente)."""
        caminho = "/".join(p.strip() for p in (caminho or "").split("/") if p.strip())
        if not caminho or f"/{modelo.FRENTES}/" not in f"/{caminho}/":
            raise ErroDaTela("Escolha uma frente: o caminho tem de passar por FRENTES.")
        raiz = self._raiz_clientes(servico)
        pasta = drive.achar_por_caminho(servico, caminho, raiz["id"])
        if not pasta:
            raise ErroDaTela(f"Não achei a frente “{caminho}” em {self.caminho_raiz}. Confira de novo.")
        return caminho, pasta

    def plano_alinhar(self, d: dict) -> dict:
        tipo = (d.get("tipo") or "").strip().upper() or None
        if tipo and tipo not in modelo.TIPOS_FRENTE:
            raise ErroDaTela("Escolha a forma da frente.")
        with self._tranca:
            servico = self.servico()
            caminho, pasta = self._frente(servico, d.get("caminho"))
            presentes = [f["name"] for f in drive.listar_filhos(servico, pasta["id"], so_pastas=True)]
        plano_a = alinhamento.planejar(presentes, tipo)
        if plano_a.ja_estava:
            raise ErroDaTela(f"A frente já está na forma {plano_a.tipo}. Nada a fazer.")
        if plano_a.vazio():
            raise ErroDaTela(f"Nada a renomear nem a criar para a forma {plano_a.tipo}: as pastas fora "
                             "do modelo não têm par pelo número, e decidir o que fazer com elas é de gente.")
        renomear, criar, avisos = alinhamento.linhas_do_plano(plano_a)
        partes = []
        if renomear:
            partes.append({"rotulo": "RENOMEAR", "linhas": renomear})
        if criar:
            partes.append({"rotulo": "CRIAR", "linhas": criar, "total": len(criar)})
        plano = {
            "titulo": f"Alinhar com a forma {plano_a.tipo}",
            "destino": f"{self.caminho_raiz}/{caminho}",
            "partes": partes,
            "avisos": avisos + ["Nada é apagado nem movido: pasta renomeada fica com tudo que tem dentro."],
            "resumo": f"{len(renomear)} renome(s), {len(criar)} pasta(s) nova(s).",
        }
        dados = {"caminho": caminho, "tipo": plano_a.tipo, "renomear": plano_a.renomear, "criar": plano_a.criar}
        return {"plano": plano, "senha": self._guardar("alinhar", dados, plano)}

    def _executar_alinhar(self, servico, dados: dict) -> dict:
        caminho, pasta = self._frente(servico, dados["caminho"])
        filhos = {f["name"]: f for f in drive.listar_filhos(servico, pasta["id"], so_pastas=True)}
        passos: list = []
        partes = caminho.split("/")
        dono = "/".join(partes[:partes.index(modelo.FRENTES)])
        nome_frente = partes[-1]
        # A etiqueta segue a mesma forma que criar_arvore daria a essa pasta.
        ancora = vbr_pastas.ancora_de(dono, modelo.FRENTES, nome_frente)
        for de, para in dados["renomear"]:
            # O Drive pode ter mudado entre o plano e a confirmação: cada
            # renome é conferido de novo, e o que não bate é pulado, não forçado.
            if de not in filhos:
                passos.append(_passo("!", 0, f"{de} não está mais aí; não renomeei"))
                continue
            if para in filhos:
                passos.append(_passo("!", 0, f"{para} já existe agora; deixei {de} como estava"))
                continue
            drive.renomear(servico, filhos[de]["id"], para)
            try:
                drive.etiquetar(servico, filhos[de]["id"], f"{ancora}/{para}")
            except Exception:
                pass  # etiquetar é melhoria, não pode derrubar a execução
            passos.append(_passo("~", 0, f"{de}  →  {para}"))
        for nome in dados["criar"]:
            _nova, criada = drive.achar_ou_criar(servico, nome, pasta["id"], f"{ancora}/{nome}")
            passos.append(_passo("+" if criada else "=", 0, nome))
        return {"passos": passos,
                "resumo": f"A frente está na forma {dados['tipo']}.",
                "mensagem": "Nada foi apagado nem movido. Rode a auditoria de novo para conferir."}

    # -- execução -------------------------------------------------------------

    def executar(self, senha: str | None) -> dict:
        with self._tranca:
            guardado = self._planos.pop(senha or "", None)
            if not guardado:
                raise ErroDaTela("Este plano não está mais valendo. Peça o plano de novo "
                                 "e confira antes de confirmar.")
            if time.time() - guardado["hora"] > VALIDADE_DO_PLANO:
                raise ErroDaTela("O plano envelheceu: ficou mais de meia hora na tela. "
                                 "Peça de novo, porque o Drive pode ter mudado.")
            executor = getattr(self, "_executar_" + guardado["tipo"])
            # Instalar e desinstalar não tocam o Drive: não conectar à toa.
            servico = None if guardado["tipo"] in ("instalar", "desinstalar") else self.servico()
            return executor(servico, guardado["dados"])

    def _criar(self, servico, arvore: dict, pai_id: str, ancora: str,
               passos: list, nivel_base: int = 0) -> tuple[int, int]:
        """O mesmo passo a passo de vbr_pastas.executar, só que anotando em vez
        de imprimir."""
        criadas = existentes = 0
        for profundidade, nome, _id, foi_criada in drive.criar_arvore(servico, arvore, pai_id, ancora):
            passos.append(_passo("+" if foi_criada else "=", nivel_base + profundidade, nome))
            if foi_criada:
                criadas += 1
            else:
                existentes += 1
        return criadas, existentes

    def _executar_originar(self, servico, dados: dict) -> dict:
        pasta_nome = dados["pasta_nome"]
        passos: list = []
        funil = self._funil(servico, passos)
        ja, encerrada = vbr_pastas.achar_originacao(servico, funil["id"], pasta_nome)
        if ja:
            raise ErroDaTela(f"Nesse meio-tempo apareceu uma originação com esse nome: {ja['name']}. "
                             "Nada foi criado.")
        etiqueta = vbr_pastas.ancora_originacao(pasta_nome)
        raiz_orig, criada = drive.achar_ou_criar(servico, pasta_nome, funil["id"], etiqueta)
        passos.append(_passo("+" if criada else "=", 0, pasta_nome))
        c, e = self._criar(servico, modelo.arvore_de_originacao(), raiz_orig["id"], etiqueta, passos, 1)
        return {
            "passos": passos,
            "resumo": f"{c + (1 if criada else 0)} pasta(s) criada(s), {e + (0 if criada else 1)} já existia(m).",
            "mensagem": "Enquanto não houver mandato, é só isto: nem acervo, nem apólice, "
                        "nem frente. Quando o contrato assinar, use Promover.",
        }

    def _executar_encerrar(self, servico, dados: dict) -> dict:
        pasta, motivo, quando = dados["pasta"], dados["motivo"], dados["quando"]
        funil = self._funil(servico)
        passos: list = []
        encerradas, criada = drive.achar_ou_criar(servico, modelo.ENCERRADAS, funil["id"])
        if criada:
            passos.append(_passo("+", 0, f"{modelo.ENCERRADAS}   (não existia)"))
        drive.anotar(servico, pasta["id"], **{drive.CHAVE_ENCERRAMENTO: f"{quando}|{motivo}"})
        drive.mover(servico, pasta["id"], encerradas["id"])
        passos.append(_passo(">", 0, f"{pasta['name']}  →  {modelo.ENCERRADAS}/"))
        try:
            drive.criar_texto(
                servico, modelo.BILHETE_DE_ENCERRAMENTO, pasta["id"],
                f"Originação encerrada em {quando}.\n\nMotivo: {motivo}\n\n"
                "Encerrada não é apagada: se o nome voltar, use\n"
                f"  vbr_pastas.py reabrir {modelo.titulo_de(pasta['name'])}\n",
            )
            passos.append(_passo("+", 1, modelo.BILHETE_DE_ENCERRAMENTO))
        except Exception as erro:  # o bilhete é conforto, não pode derrubar nada
            passos.append(_passo("!", 1, f"não consegui escrever o bilhete: {erro}"))
        return {"passos": passos, "resumo": f"{pasta['name']} está em {modelo.ENCERRADAS}.",
                "mensagem": "Data e motivo ficaram gravados. Nada foi apagado."}

    def _executar_reabrir(self, servico, dados: dict) -> dict:
        pasta = dados["pasta"]
        funil = self._funil(servico)
        drive.mover(servico, pasta["id"], funil["id"])
        drive.anotar(servico, pasta["id"], **{drive.CHAVE_ENCERRAMENTO: None})
        return {"passos": [_passo(">", 0, f"{pasta['name']}  →  funil")],
                "resumo": f"{pasta['name']} está no funil de novo.",
                "mensagem": f"O {modelo.BILHETE_DE_ENCERRAMENTO} fica: é a memória de por que "
                            "parou da outra vez."}

    def _executar_promover(self, servico, dados: dict) -> dict:
        origem, nome_cliente, arvore = dados["origem"], dados["nome_cliente"], dados["arvore"]
        passos: list = []
        raiz = self._raiz_clientes(servico)
        pasta_cliente, criada = drive.achar_ou_criar(
            servico, nome_cliente, raiz["id"], vbr_pastas.ancora_de(nome_cliente))
        passos.append(_passo("+" if criada else "=", 0, nome_cliente))

        if origem:
            drive.mover(servico, origem["id"], pasta_cliente["id"])
            drive.renomear(servico, origem["id"], modelo.ORIGINACAO)
            passos.append(_passo(">", 1, f"{modelo.ORIGINACAO}   (veio do funil, inteira)"))
        else:
            self._criar(servico, {modelo.ORIGINACAO: modelo.arvore_de_originacao()},
                        pasta_cliente["id"], vbr_pastas.ancora_de(nome_cliente), passos, 1)

        c, e = self._criar(servico, arvore, pasta_cliente["id"],
                           vbr_pastas.ancora_de(nome_cliente), passos, 1)
        return {"passos": passos,
                "resumo": f"{c} pasta(s) criada(s), {e} já existia(m).",
                "mensagem": "O funil tem uma originação a menos." if origem else
                            "O cliente nasceu com uma originação vazia."}


# O alvo que a página manda quando quer conferir o funil e não um cliente.
FUNIL = "__funil__"

# True quando este processo é o programa de fundo, lançado pelo launchd
# (--fundo). A aba Sistema e os planos de instalação mudam de fala com isso.
FUNDO = False

# As famílias de achado, para a tela agrupar o que o terminal lista corrido.
# Cada regra da auditoria escreve a mensagem de um jeito; o trecho fixo dela
# é o que identifica a família. Mensagem que não casa com nenhum trecho vira
# família própria, com o texto dela — o teste acusa quando isso acontece.
FAMILIAS = [
    ("espaço no começo ou no fim", "Espaço no nome"),
    ("espaço duplo", "Espaço no nome"),
    ("fora da grafia da casa", "Fora da grafia da casa"),
    ("só tem originação", "Prospecto dentro de CLIENTES"),
    ("modelo anterior", "Originação no modelo anterior"),
    ("aberta há", "Originação parada"),
    ("sem a subpasta", "Subpasta faltando"),
    ("subpasta fora do modelo", "Subpasta fora do modelo"),
    ("sem pasta de originação", "Pasta obrigatória faltando"),
    ("sem pasta APOLICES", "Pasta obrigatória faltando"),
    ("sem pasta FRENTES", "Pasta obrigatória faltando"),
    ("sem a pasta", "Pasta obrigatória faltando"),
    ("pasta fora do modelo do ativo", "Pasta fora do modelo"),
    ("ativo com pasta de originação", "Originação dentro do ativo"),
    ("ramo com o nome antigo", "Ramo com nome antigo"),
    ("ramo fora da lista", "Ramo fora da lista da casa"),
    ("não bate com nenhum tipo", "Frente fora de qualquer tipo"),
    ("nome de frente fora do padrão", "Nome fora do padrão"),
    ("nome de originação fora do padrão", "Nome fora do padrão"),
    ("mês inválido", "Nome fora do padrão"),
    ("frente sem nenhuma subpasta", "Frente vazia"),
    ("frente do tipo", "Tipo de cada frente"),
    ("arquivo(s) solto(s)", "Arquivos soltos"),
    ("nome repetido", "Duplicatas"),
    ("parece cópia automática", "Duplicatas"),
    ("cliente sem ativo", "Cliente sem ativo"),
    ("encerrada", "Encerradas"),
]


def familia_de(mensagem: str) -> tuple[str, bool]:
    for trecho, nome in FAMILIAS:
        if trecho in mensagem:
            return nome, True
    return mensagem, False


def _passo(marca: str, nivel: int, texto: str) -> dict:
    return {"marca": marca, "nivel": nivel, "texto": texto}


# ---------------------------------------------------------------------------
# Erros: uma frase para a página, o traceback para o terminal.
# ---------------------------------------------------------------------------


def frase_de_erro(erro: Exception) -> str:
    if isinstance(erro, (ErroDaTela, drive.DriveErro)):
        return str(erro)
    nome = type(erro).__name__
    if nome == "RefreshError" or "invalid_grant" in str(erro):
        return ("A autorização do Google venceu e não deu para renovar pelo navegador. Feche esta "
                "janela, apague o token.json da pasta do programa e abra de novo para autorizar. "
                "Para não vencer a cada sete dias: no Google Cloud, publique o app (Tela de "
                "consentimento OAuth → Publicar).")
    status = getattr(erro, "status_code", None) or getattr(getattr(erro, "resp", None), "status", None)
    if nome == "HttpError" or status:
        if status in (401, 403):
            return ("O Google recusou o acesso. A autorização pode ter vencido: feche esta "
                    "janela, apague o token.json e abra de novo para autorizar.")
        if status == 404:
            return "O Drive não achou uma pasta que a página esperava. Recarregue e tente de novo."
        if status == 429:
            return "O Drive pediu para ir mais devagar. Espere um minuto e tente de novo."
        return f"O Drive respondeu com um erro ({status}). O detalhe está na janela do terminal."
    if isinstance(erro, (ConnectionError, TimeoutError, OSError)) or "ServerNotFound" in nome:
        return "Sem conexão com o Drive. Confira a internet e tente de novo."
    return "Algo deu errado do lado do programa. O detalhe está na janela do terminal."


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------


class Manipulador(BaseHTTPRequestHandler):
    tela: Tela
    origens_permitidas: set[str] = set()

    def log_message(self, *_args):
        """Silêncio: o terminal mostra uma linha ao subir e os erros, mais nada."""

    # -- utilidades -----------------------------------------------------------

    def _json(self, dados, status: int = HTTPStatus.OK):
        corpo = json.dumps(dados, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(corpo)

    def _pagina(self):
        try:
            corpo = PAGINA.read_bytes()
        except OSError:
            return self._json({"erro": f"não achei {PAGINA.name} ao lado do servidor."},
                              HTTPStatus.INTERNAL_SERVER_ERROR)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        # A página não carrega nada de fora, e o navegador é instruído a
        # recusar se um dia alguém tentar.
        self.send_header("Content-Security-Policy",
                         "default-src 'self'; style-src 'self' 'unsafe-inline'; "
                         "script-src 'self' 'unsafe-inline'; img-src 'self' data:")
        self.end_headers()
        self.wfile.write(corpo)

    def _responder(self, funcao):
        try:
            self._json(funcao())
        except ErroDaTela as erro:
            self._json({"erro": str(erro)}, HTTPStatus.BAD_REQUEST)
        except Exception as erro:  # noqa: BLE001 — a página recebe a frase, o terminal o resto
            traceback.print_exc()
            self._json({"erro": frase_de_erro(erro)}, HTTPStatus.BAD_GATEWAY)

    def _ler_json(self) -> dict:
        tipo = self.headers.get("Content-Type", "")
        if not tipo.startswith("application/json"):
            raise ErroDaTela("A página mandou algo que o servidor não entende.")
        tamanho = int(self.headers.get("Content-Length") or 0)
        if tamanho > 1_000_000:
            raise ErroDaTela("Pedido grande demais.")
        try:
            dados = json.loads(self.rfile.read(tamanho) or b"{}")
        except json.JSONDecodeError:
            raise ErroDaTela("A página mandou algo que o servidor não entende.")
        return dados if isinstance(dados, dict) else {}

    def _origem_ok(self) -> bool:
        """
        Só a própria página pode escrever. Qualquer site aberto em outra aba
        alcança 127.0.0.1, e sem esta conferência poderia pedir um plano e
        executá-lo em nome do usuário.
        """
        origem = self.headers.get("Origin")
        if origem and origem not in self.origens_permitidas:
            return False
        host = self.headers.get("Host", "")
        return host.split(":")[0] in (ENDERECO, "localhost")

    # -- rotas ----------------------------------------------------------------

    def do_GET(self):
        url = urlparse(self.path)
        parametros = {k: v[0] for k, v in parse_qs(url.query).items()}
        if url.path == "/":
            return self._pagina()
        if url.path == "/api/estado":
            return self._responder(self.tela.estado)
        if url.path == "/api/modelo":
            return self._responder(self.tela.modelo_json)
        if url.path == "/api/grafia":
            return self._responder(
                lambda: self.tela.grafia(parametros.get("nome", ""), parametros.get("competencia")))
        if url.path == "/api/funil":
            return self._responder(self.tela.funil)
        if url.path == "/api/destinos":
            return self._responder(self.tela.destinos)
        if url.path == "/api/sistema":
            return self._responder(self.tela.sistema)
        if url.path == "/api/auditoria":
            return self._responder(lambda: self.tela.auditoria(parametros.get("alvo")))
        self._json({"erro": "não há nada neste endereço."}, HTTPStatus.NOT_FOUND)

    def do_POST(self):
        if not self._origem_ok():
            return self._json({"erro": "pedido recusado: veio de outro site."}, HTTPStatus.FORBIDDEN)
        rotas = {
            "/api/originar/plano": self.tela.plano_originar,
            "/api/encerrar/plano": self.tela.plano_encerrar,
            "/api/reabrir/plano": self.tela.plano_reabrir,
            "/api/promover/plano": self.tela.plano_promover,
            "/api/frente/plano": self.tela.plano_frente,
            "/api/ramo/plano": self.tela.plano_ramo,
            "/api/cliente/plano": self.tela.plano_cliente,
            "/api/ativo/plano": self.tela.plano_ativo,
            "/api/alinhar/plano": self.tela.plano_alinhar,
            "/api/instalar/plano": self.tela.plano_instalar,
            "/api/desinstalar/plano": self.tela.plano_desinstalar,
            "/api/executar": lambda d: self.tela.executar(d.get("senha")),
        }
        funcao = rotas.get(urlparse(self.path).path)
        if not funcao:
            return self._json({"erro": "não há nada neste endereço."}, HTTPStatus.NOT_FOUND)
        self._responder(lambda: funcao(self._ler_json()))


def servidor_para(tela: Tela, porta: int) -> ThreadingHTTPServer:
    """Monta o servidor sem o pôr a rodar. Os testes usam com porta 0."""

    class _Manipulador(Manipulador):
        pass

    _Manipulador.tela = tela
    servidor = ThreadingHTTPServer((ENDERECO, porta), _Manipulador)
    porta_real = servidor.server_address[1]
    _Manipulador.origens_permitidas = {f"http://{ENDERECO}:{porta_real}",
                                       f"http://localhost:{porta_real}"}
    servidor.daemon_threads = True
    return servidor


def _ja_no_ar(porta: int) -> str | None:
    """A porta está ocupada: é o próprio VBR Pastas? Devolve o modo dele
    ("drive" ou "falso"), ou None se for outro programa."""
    try:
        with urllib.request.urlopen(f"http://{ENDERECO}:{porta}/api/estado", timeout=1) as r:
            dados = json.loads(r.read().decode("utf-8"))
            return dados.get("modo") if "competencia_hoje" in dados else None
    except Exception:  # noqa: BLE001 — qualquer falha quer dizer "não é o nosso"
        return None


def _linha_de_comando_do_agente(args, lancador: Lancador) -> int:
    """--instalar, --desinstalar e --situacao, para quem prefere o Terminal."""
    if args.instalar:
        print("Vai:")
        for linha in lancador.plano_de_instalacao():
            print("  " + linha)
        if input("Instalar? [s/N]: ").strip().lower() not in ("s", "sim"):
            print("cancelado.")
            return 0
        try:
            for passo in lancador.instalar():
                print("  " + passo)
        except RuntimeError as erro:
            print(f"ERRO: {erro}", file=sys.stderr)
            return 1
        print(f"\nO VBR Pastas passa a subir com o Mac. Para abrir a tela: “{lancador.atalho_web.name}” "
              f"ou {lancador.endereco}.")
        return 0
    if args.desinstalar:
        if input(f"Tirar {lancador.plist.name} e parar o programa de fundo? [s/N]: ").strip().lower() \
                not in ("s", "sim"):
            print("cancelado.")
            return 0
        for passo in lancador.desinstalar():
            print("  " + passo)
        return 0
    sit = lancador.situacao()
    if not sit["instalado"]:
        print("O agente não está instalado. Para instalar: python3 servidor.py --instalar")
    elif sit["rodando"]:
        print(f"Instalado e rodando (pid {sit['pid']}) em {sit['endereco']}. Log: {sit['log']}")
    else:
        print(f"Instalado, mas não está rodando. Veja o log: {sit['log']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="servidor.py", description="A tela do vbr-pastas.")
    p.add_argument("--porta", type=int, default=None,
                   help=f"padrão {PORTA_PADRAO}; a demonstração (--falso) usa {PORTA_DEMO}")
    p.add_argument("--falso", action="store_true",
                   help="usa um Drive de demonstração, em memória, sem credencial")
    p.add_argument("--sem-navegador", action="store_true", help="não abre o navegador ao subir")
    p.add_argument("--raiz", default=None, help="caminho da pasta de clientes, só desta vez")
    p.add_argument("--originacao", default=None, help="caminho do funil, só desta vez")
    p.add_argument("--paciencia", type=int, default=12,
                   help="a partir de quantos meses uma originação aberta é sinalizada")
    p.add_argument("--fundo", action="store_true",
                   help="modo do launchd: sem navegador, e espera a porta se estiver ocupada")
    p.add_argument("--instalar", action="store_true", help="grava o agente do launchd e o carrega")
    p.add_argument("--desinstalar", action="store_true", help="descarrega o agente e apaga o arquivo")
    p.add_argument("--situacao", action="store_true", help="diz se o agente está instalado e rodando")
    args = p.parse_args(argv)

    global FUNDO
    FUNDO = args.fundo
    if args.porta is None:
        args.porta = PORTA_DEMO if args.falso else PORTA_PADRAO
    lancador = Lancador(args.porta)

    if args.instalar or args.desinstalar or args.situacao:
        return _linha_de_comando_do_agente(args, lancador)

    if args.falso:
        import drive_falso

        # Caminhos fixos, de propósito: a demonstração não lê o config.json
        # nem depende do que está gravado nele.
        tela = Tela(drive_falso.com_exemplo, "falso",
                    "GESTAO DE RISCOS/CLIENTES", "GESTAO DE RISCOS/ORIGINACAO", args.paciencia, lancador)
    else:
        raiz = config.raiz(args.raiz, perguntar_se_faltar=None)
        tela = Tela(drive.conectar, "drive", raiz,
                    config.raiz_originacao(args.originacao, raiz), args.paciencia, lancador)

    endereco = f"http://{ENDERECO}:{args.porta}"
    avisou = False
    while True:
        try:
            servidor = servidor_para(tela, args.porta)
            break
        except OSError as erro:
            if erro.errno != errno.EADDRINUSE:
                raise
            if args.fundo:
                # O programa de fundo não desiste: a porta costuma estar com
                # um servidor aberto pelo atalho, e ele assume quando aquele
                # fechar. Uma linha no log, não uma por tentativa.
                if not avisou:
                    print(f"A porta {args.porta} está ocupada — esperando ela ficar livre.", flush=True)
                    avisou = True
                time.sleep(5)
                continue
            modo_no_ar = _ja_no_ar(args.porta)
            modo_pedido = "falso" if args.falso else "drive"
            if modo_no_ar == modo_pedido:
                qual = "A demonstração" if args.falso else "O VBR Pastas"
                print(f"{qual} já está no ar em {endereco} — abrindo o navegador nele.")
                if not args.sem_navegador:
                    webbrowser.open(endereco)
                return 0
            if modo_no_ar:
                # Um está no ar e o outro foi pedido: nunca abrir um pelo outro.
                outro = "o VBR Pastas de verdade" if modo_no_ar == "drive" else "a demonstração"
                print(f"A porta {args.porta} está com {outro}. "
                      f"Tente: python3 servidor.py{' --falso' if args.falso else ''} --porta {args.porta + 1}")
                return 1
            print(f"A porta {args.porta} está ocupada por outro programa. "
                  f"Tente: python3 servidor.py{' --falso' if args.falso else ''} --porta {args.porta + 1}")
            return 1

    modo = " (demonstração, sem Drive)" if args.falso else ""
    como_parar = ("é o programa de fundo, do launchd" if args.fundo
                  else "para parar, feche esta janela ou aperte Ctrl+C")
    print(f"VBR Pastas{modo} no ar em {endereco} — {como_parar}.", flush=True)
    if not args.sem_navegador and not args.fundo:
        webbrowser.open(endereco)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
