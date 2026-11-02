"""
Testa o que drive.conectar faz com um token vencido — sem Google, sem token
de verdade: as bibliotecas são de mentira, e o token fica numa pasta temporária.

    python3 teste_conectar.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import drive

FALHAS: list[str] = []


def conferir(condicao: bool, descricao: str) -> None:
    print(f"  [{'ok  ' if condicao else 'FALHA'}] {descricao}")
    if not condicao:
        FALHAS.append(descricao)


class RefreshErrorFalso(Exception):
    pass


acontecimentos: list[str] = []


class CredVencida:
    valid = False
    expired = True
    refresh_token = "sim"

    def refresh(self, _pedido):
        acontecimentos.append("refresh")
        raise RefreshErrorFalso("invalid_grant: Token has been expired or revoked.")


class CredNova:
    valid = True
    expired = False
    refresh_token = "sim"

    def to_json(self):
        return '{"token": "novo"}'


class CredentialsFalso:
    @staticmethod
    def from_authorized_user_file(caminho, escopos):
        acontecimentos.append("leu token")
        return CredVencida()


class FluxoFalso:
    @staticmethod
    def from_client_secrets_file(caminho, escopos):
        acontecimentos.append("abriu credencial")
        return FluxoFalso()

    def run_local_server(self, port=0):
        acontecimentos.append("navegador")
        return CredNova()


def build_falso(nome, versao, credentials=None, cache_discovery=True):
    acontecimentos.append("build")
    return "serviço"


pasta = Path(tempfile.mkdtemp(prefix="vbr-conectar-"))
drive.TOKEN = pasta / "token.json"
drive.CREDENCIAL = pasta / "credentials.json"
drive.TOKEN.write_text('{"token": "vencido"}')
drive.CREDENCIAL.write_text("{}")
drive._bibliotecas = lambda: (object, CredentialsFalso, FluxoFalso, build_falso, RefreshErrorFalso)

print("\n1. token vencido: o programa reautoriza em vez de parar")
servico = drive.conectar()
conferir(servico == "serviço", "devolveu o serviço")
conferir(acontecimentos == ["leu token", "refresh", "abriu credencial", "navegador", "build"],
         f"leu o token, tentou renovar, falhou, abriu o navegador e seguiu: {acontecimentos}")
conferir(drive.TOKEN.read_text() == '{"token": "novo"}', "gravou o token novo por cima do vencido")

print("\n2. a frase na tela")
import servidor
frase = servidor.frase_de_erro(RefreshErrorFalso("invalid_grant: Bad Request"))
conferir("autorização do Google venceu" in frase and "Publicar" in frase, "diz que a autorização venceu e como parar de vencer")

print("\n" + "=" * 60)
if FALHAS:
    print(f"{len(FALHAS)} falha(s):")
    for f in FALHAS:
        print(f"  - {f}")
    sys.exit(1)
print("tudo passou.")
