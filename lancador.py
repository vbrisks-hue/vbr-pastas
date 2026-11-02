"""
O programa subindo sozinho com o Mac — um agente do launchd.

O launchd é o que o macOS usa para manter programas de fundo: um arquivo
.plist em ~/Library/LaunchAgents diz o que rodar, e ele roda ao entrar na
conta e de novo se cair. Sem janela de Terminal, sem Dock.

O que se grava e o que se apaga está todo aqui, para o servidor e a página
só chamarem. Nada aqui fala com o Drive.

    python3 servidor.py --instalar      grava o agente e o põe a rodar
    python3 servidor.py --desinstalar   tira o agente e apaga o arquivo
    python3 servidor.py --situacao      diz se está instalado e rodando
"""

from __future__ import annotations

import os
import plistlib
import re
import subprocess
import sys
import time
from pathlib import Path

ROTULO = "com.vbrisk.pastas"
ATALHO_WEB = "Abrir VBR Pastas.webloc"
ARQUIVO_DE_LOG = "servidor.log"


class Lancador:
    """
    Instala, remove e consulta o agente. Recebe por parâmetro tudo que
    depende da máquina — a pasta home, o Python, quem executa o launchctl —
    para o teste rodar contra uma pasta temporária e um launchctl de mentira.
    """

    def __init__(self, porta: int, pasta: Path | None = None, python: str | None = None,
                 casa: Path | None = None, executar=subprocess.run, uid: int | None = None,
                 esperar=time.sleep):
        self.porta = porta
        self.esperar = esperar
        self.pasta = (pasta or Path(__file__).parent).resolve()
        self.python = python or sys.executable
        self.casa = casa or Path.home()
        self.executar = executar
        self.uid = os.getuid() if uid is None else uid

    # -- caminhos -------------------------------------------------------------

    @property
    def plist(self) -> Path:
        return self.casa / "Library" / "LaunchAgents" / f"{ROTULO}.plist"

    @property
    def log(self) -> Path:
        return self.pasta / ARQUIVO_DE_LOG

    @property
    def atalho_web(self) -> Path:
        return self.pasta / ATALHO_WEB

    @property
    def endereco(self) -> str:
        return f"http://127.0.0.1:{self.porta}"

    @property
    def dominio(self) -> str:
        return f"gui/{self.uid}"

    # -- o que se grava -------------------------------------------------------

    def conteudo_plist(self) -> bytes:
        return plistlib.dumps({
            "Label": ROTULO,
            # --fundo: não abre navegador, e espera a porta se ela estiver
            # ocupada por um servidor aberto pelo atalho — assume quando ele
            # fechar, em vez de desistir.
            "ProgramArguments": [self.python, str(self.pasta / "servidor.py"),
                                 "--fundo", "--porta", str(self.porta)],
            # credentials.json e config.json são lidos por caminho relativo.
            "WorkingDirectory": str(self.pasta),
            "RunAtLoad": True,
            # Volta se cair; não volta se saiu por vontade própria (código 0).
            "KeepAlive": {"SuccessfulExit": False},
            "ThrottleInterval": 10,
            "StandardOutPath": str(self.log),
            "StandardErrorPath": str(self.log),
            # BROWSER=open: quando a autorização do Google precisa do navegador,
            # a biblioteca abre com `open`, que funciona a partir do launchd. Sem
            # isso, o processo de fundo só escrevia o endereço no log (31/10).
            "EnvironmentVariables": {"PYTHONUNBUFFERED": "1", "LANG": "pt_BR.UTF-8", "BROWSER": "open"},
        }, sort_keys=False)

    def conteudo_atalho_web(self) -> bytes:
        """Um .webloc: duplo clique abre o endereço no navegador, sem Terminal."""
        return plistlib.dumps({"URL": self.endereco})

    # -- launchctl ------------------------------------------------------------

    def _launchctl(self, *args: str):
        return self.executar(["launchctl", *args], capture_output=True, text=True)

    def situacao(self) -> dict:
        """Instalado é ter o .plist; rodando é o launchd conhecer o rótulo com um pid."""
        instalado = self.plist.exists()
        carregado, pid = False, None
        if instalado:
            saida = self._launchctl("print", f"{self.dominio}/{ROTULO}")
            carregado = saida.returncode == 0
            achado = re.search(r"\bpid = (\d+)", saida.stdout or "")
            pid = int(achado.group(1)) if achado else None
        return {
            "instalado": instalado, "carregado": carregado, "rodando": pid is not None, "pid": pid,
            "plist": str(self.plist), "log": str(self.log), "atalho_web": str(self.atalho_web),
            "atalho_web_existe": self.atalho_web.exists(),
            "python": self.python, "pasta": str(self.pasta), "endereco": self.endereco,
        }

    def plano_de_instalacao(self) -> list[str]:
        return [
            f"gravar  {self.plist}",
            f"        roda: {self.python} servidor.py --fundo --porta {self.porta}",
            f"        em:   {self.pasta}",
            f"        log:  {self.log}",
            f"gravar  {self.atalho_web}   (duplo clique abre a tela)",
            f"pedir ao launchd que carregue {ROTULO}: sobe agora e a cada entrada na conta",
        ]

    def _carregado(self) -> bool:
        return self._launchctl("print", f"{self.dominio}/{ROTULO}").returncode == 0

    def _descarregar_e_esperar(self) -> None:
        """
        bootout devolve na hora, mas o launchd ainda leva um instante para
        derrubar o serviço; um bootstrap nesse instante falha com
        "Bootstrap failed: 5: Input/output error". Espera o rótulo sumir.
        """
        self._launchctl("bootout", f"{self.dominio}/{ROTULO}")
        for _ in range(40):  # até uns 20 segundos
            if not self._carregado():
                return
            self.esperar(0.5)

    def instalar(self) -> list[str]:
        passos = []
        self.plist.parent.mkdir(parents=True, exist_ok=True)
        # Se já estava carregado, descarrega antes: bootstrap em cima de um
        # agente carregado é recusado pelo launchd.
        if self.plist.exists():
            self._descarregar_e_esperar()
            passos.append(f"= {ROTULO} já estava instalado; regravado")
        self.plist.write_bytes(self.conteudo_plist())
        passos.append(f"+ {self.plist}")
        self.atalho_web.write_bytes(self.conteudo_atalho_web())
        passos.append(f"+ {self.atalho_web}")
        # Mesmo depois de esperar, o launchd às vezes recusa a primeira
        # tentativa; tenta mais algumas antes de desistir.
        saida = None
        for tentativa in range(5):
            saida = self._launchctl("bootstrap", self.dominio, str(self.plist))
            if saida.returncode == 0:
                break
            self.esperar(1.0)
        if saida is None or saida.returncode != 0:
            raise RuntimeError(
                "o launchd recusou carregar o agente: "
                + ((saida.stderr or saida.stdout or "").strip() or f"código {saida.returncode}"))
        passos.append(f"> launchd carregou {ROTULO}")
        return passos

    def desinstalar(self) -> list[str]:
        passos = []
        saida = self._launchctl("bootout", f"{self.dominio}/{ROTULO}")
        passos.append(f"> launchd descarregou {ROTULO}" if saida.returncode == 0
                      else f"= {ROTULO} não estava carregado")
        for arquivo in (self.plist, self.atalho_web):
            if arquivo.exists():
                arquivo.unlink()
                passos.append(f"- {arquivo}")
        return passos
