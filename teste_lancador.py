"""
Testa o agente do launchd sem tocar no launchd: a pasta home é temporária e
o launchctl é de mentira.

    python3 teste_lancador.py
"""

from __future__ import annotations

import plistlib
import shutil
import sys
import tempfile
from pathlib import Path

from lancador import ATALHO_WEB, ROTULO, Lancador

FALHAS: list[str] = []


def conferir(condicao: bool, descricao: str) -> None:
    print(f"  [{'ok  ' if condicao else 'FALHA'}] {descricao}")
    if not condicao:
        FALHAS.append(descricao)


class Saida:
    def __init__(self, rc, stdout="", stderr=""):
        self.returncode, self.stdout, self.stderr = rc, stdout, stderr


chamadas: list[list[str]] = []
esperas: list[float] = []
# "derrubando": depois do bootout, o launchd de verdade ainda responde ao
# print por um instante, e recusa bootstrap nesse meio-tempo.
estado = {"carregado": False, "recusar_bootstrap": False, "derrubando": 0}


def launchctl_falso(cmd, **_):
    """Reage como o launchctl reage: print só responde a rótulo carregado."""
    chamadas.append(cmd)
    verbo = cmd[1]
    if verbo == "print":
        if estado["derrubando"]:
            estado["derrubando"] -= 1
            return Saida(0, "state = running")
        return Saida(0, f"{ROTULO} = {{\n\tstate = running\n\tpid = 4242\n}}") if estado["carregado"] else Saida(113)
    if verbo == "bootstrap":
        if estado["recusar_bootstrap"] or estado["derrubando"]:
            return Saida(5, stderr="Bootstrap failed: 5: Input/output error")
        estado["carregado"] = True
        return Saida(0)
    if verbo == "bootout":
        rc = 0 if estado["carregado"] else 3
        if estado["carregado"]:
            estado["derrubando"] = 3
        estado["carregado"] = False
        return Saida(rc)
    return Saida(1)


raiz = Path(tempfile.mkdtemp(prefix="vbr-lancador-"))
casa = raiz / "casa"
pasta = raiz / "vbr_pastas"
pasta.mkdir()
pasta = pasta.resolve()  # o Lancador resolve a pasta; /var vira /private/var no macOS
(pasta / "servidor.py").write_text("# de mentira\n")
lanc = Lancador(8765, pasta=pasta, python="/opt/python/bin/python3", casa=casa, executar=launchctl_falso, uid=501,
                esperar=esperas.append)

print("\n1. o que se grava")
plist = plistlib.loads(lanc.conteudo_plist())
conferir(plist["Label"] == ROTULO, f"rótulo {ROTULO}")
conferir(plist["ProgramArguments"] == ["/opt/python/bin/python3", str(pasta / "servidor.py"), "--fundo", "--porta", "8765"],
         "roda o servidor com --fundo na porta certa, com o Python informado")
conferir(plist["WorkingDirectory"] == str(pasta), "a pasta de trabalho é a do programa (credentials.json é relativo)")
conferir(plist["RunAtLoad"] is True and plist["KeepAlive"] == {"SuccessfulExit": False}, "sobe ao entrar e volta se cair, mas não se saiu por vontade própria")
conferir(plist["StandardOutPath"] == str(pasta / "servidor.log") == plist["StandardErrorPath"], "saída e erro no mesmo log, na pasta do programa")
conferir(plist["EnvironmentVariables"].get("BROWSER") == "open", "o agente abre o navegador da autorização com `open`")
web = plistlib.loads(lanc.conteudo_atalho_web())
conferir(web == {"URL": "http://127.0.0.1:8765"}, "o .webloc aponta para o endereço")
conferir(lanc.plist == casa / "Library" / "LaunchAgents" / f"{ROTULO}.plist", "o .plist vai para ~/Library/LaunchAgents")

print("\n2. antes de instalar")
sit = lanc.situacao()
conferir(not sit["instalado"] and not sit["rodando"] and sit["pid"] is None, "não instalado, não rodando")
conferir(not chamadas, "sem .plist, nem pergunta ao launchctl")

print("\n3. instalar")
passos = lanc.instalar()
conferir(lanc.plist.exists() and plistlib.loads(lanc.plist.read_bytes())["Label"] == ROTULO, "gravou o .plist")
conferir((pasta / ATALHO_WEB).exists(), "gravou o atalho .webloc")
conferir(["launchctl", "bootstrap", "gui/501", str(lanc.plist)] in chamadas, "pediu bootstrap no domínio do usuário")
conferir(any(p.startswith("> launchd carregou") for p in passos), f"relatou os passos: {passos}")
sit = lanc.situacao()
conferir(sit["instalado"] and sit["carregado"] and sit["rodando"] and sit["pid"] == 4242, "instalado, carregado, rodando com pid")

print("\n4. instalar de novo — regrava, descarregando antes e esperando o launchd derrubar")
chamadas.clear(); esperas.clear()
passos = lanc.instalar()
conferir(chamadas[0][:2] == ["launchctl", "bootout"] and chamadas[-1][1] == "bootstrap", "bootout antes, bootstrap depois")
prints = [c for c in chamadas if c[1] == "print"]
conferir(len(prints) >= 3 and len(esperas) >= 3, f"esperou o rótulo sumir antes do bootstrap ({len(prints)} consultas, {len(esperas)} esperas)")
conferir(sum(1 for c in chamadas if c[1] == "bootstrap") == 1, "e o bootstrap passou de primeira")
conferir(any("já estava" in p for p in passos), "avisou que regravou")
conferir(lanc.situacao()["rodando"], "está rodando de novo")

print("\n5. o launchd recusa")
estado["recusar_bootstrap"] = True
try:
    lanc.instalar()
    conferir(False, "deveria ter levantado erro")
except RuntimeError as erro:
    conferir("recusou" in str(erro) and "Input/output" in str(erro), f"erro com a frase do launchd: {erro}")
conferir(sum(1 for c in chamadas if c[1] == "bootstrap") >= 5, "tentou cinco vezes antes de desistir")
estado["recusar_bootstrap"] = False

print("\n6. desinstalar")
lanc.instalar()
chamadas.clear()
passos = lanc.desinstalar()
conferir(chamadas[0] == ["launchctl", "bootout", f"gui/501/{ROTULO}"], "pediu bootout")
conferir(not lanc.plist.exists() and not (pasta / ATALHO_WEB).exists(), "apagou o .plist e o atalho")
conferir(not lanc.situacao()["instalado"], "voltou a não instalado")
passos = lanc.desinstalar()
conferir(any("não estava carregado" in p for p in passos) and len(passos) == 1, "desinstalar de novo é inofensivo")

shutil.rmtree(raiz)
print("\n" + "=" * 60)
if FALHAS:
    print(f"{len(FALHAS)} falha(s):")
    for f in FALHAS:
        print(f"  - {f}")
    sys.exit(1)
print("tudo passou.")
