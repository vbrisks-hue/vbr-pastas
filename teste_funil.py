"""
Testa o ciclo inteiro de uma originação contra o Drive falso.

    python teste_funil.py

Sai com código 1 se alguma verificação falhar, para poder entrar numa
verificação automática.
"""

from __future__ import annotations

import builtins
import os
import sys
from argparse import Namespace

os.environ["VBR_RAIZ"] = "GESTAO DE RISCOS/CLIENTES"
os.environ["VBR_ORIGINACAO"] = "GESTAO DE RISCOS/ORIGINACAO"
os.environ["VBR_CONFIG"] = "/tmp/config_de_teste.json"

import drive  # noqa: E402
import modelo  # noqa: E402
import vbr_pastas  # noqa: E402
from drive_falso import DriveFalso  # noqa: E402

FALHAS: list[str] = []


def conferir(condicao: bool, descricao: str) -> None:
    marca = "ok  " if condicao else "FALHA"
    print(f"  [{marca}] {descricao}")
    if not condicao:
        FALHAS.append(descricao)


def responder(*respostas: str):
    """Faz o input() do terminal ler de uma fila em vez do teclado."""
    fila = list(respostas)

    def falso_input(prompt=""):
        if not fila:
            raise AssertionError(f"o programa perguntou a mais: {prompt!r}")
        resposta = fila.pop(0)
        return resposta

    builtins.input = falso_input
    return lambda: conferir(not fila, f"consumiu todas as respostas (sobraram {fila})")


def rodar(comando, respostas, **campos):
    args = Namespace(raiz=None, originacao=None, **campos)
    sobrou = responder(*respostas)
    silencioso = []
    original = builtins.print
    builtins.print = lambda *a, **k: silencioso.append(" ".join(str(x) for x in a))
    try:
        comando(args)
    except SystemExit:
        pass
    finally:
        builtins.print = original
    sobrou()
    return "\n".join(silencioso)


# ---------------------------------------------------------------------------

falso = DriveFalso()
drive.conectar = lambda: falso
clientes_id = falso.semear("GESTAO DE RISCOS/CLIENTES")
gestao_id = falso.semear("GESTAO DE RISCOS")

print("\n1. originar — o funil ainda não existe, o programa oferece criar")
saida = rodar(
    vbr_pastas.cmd_originar,
    ["2026-03", "s", "s"],  # competência, confirmar plano, criar a pasta do funil
    nome="CVCP",
)
funil_id = falso.semear("GESTAO DE RISCOS/ORIGINACAO")
conferir("ainda não existe" in saida, "avisou que o funil não existia")
conferir(falso.contar_pastas(funil_id) == 8, "criou 1 originação + 6 subpastas + LOGOS")
orig = [i for i in falso.itens.values() if i["name"] == "2026-03_CVCP"]
conferir(len(orig) == 1, "a pasta se chama 2026-03_CVCP")
conferir(
    orig[0]["appProperties"].get("vbr") == "vbr/ORIGINACAO/CVCP",
    "a etiqueta é vbr/ORIGINACAO/CVCP — sem a data e sem o lugar",
)
conferir(
    falso.contar_pastas(clientes_id) == 0,
    "CLIENTES continua vazia: prospecto não é cliente",
)

print("\n2. originar de novo — não duplica")
antes = len(falso.itens)
saida = rodar(vbr_pastas.cmd_originar, ["2026-03", "s"], nome="CVCP")
conferir("já existe" in saida, "reconheceu que já existe")
conferir(len(falso.itens) == antes, "não criou nada de novo")

print("\n3. alguém renomeia a pasta à mão — a etiqueta continua achando")
orig[0]["name"] = "CVCP - conversas"
saida = rodar(vbr_pastas.cmd_originar, ["2026-03", "s"], nome="CVCP")
conferir("já existe" in saida, "achou mesmo com o nome trocado")
orig[0]["name"] = "2026-03_CVCP"

print("\n4. encerrar — sai do funil, não some")
saida = rodar(
    vbr_pastas.cmd_encerrar, ["s"], nome="CVCP", motivo="ficou com a corretora atual"
)
encerradas = [i for i in falso.itens.values() if i["name"] == modelo.ENCERRADAS]
conferir(len(encerradas) == 1, f"criou {modelo.ENCERRADAS}")
conferir(
    encerradas[0]["id"] in orig[0]["parents"],
    f"a originação está dentro de {modelo.ENCERRADAS}",
)
conferir(
    "ficou com a corretora atual" in orig[0]["appProperties"].get("vbr_encerrada", ""),
    "gravou o motivo na propriedade invisível",
)
bilhete = [i for i in falso.itens.values() if i["name"] == "_ENCERRAMENTO.txt"]
conferir(len(bilhete) == 1, "deixou o bilhete _ENCERRAMENTO.txt dentro da pasta")
conferir(
    falso.contar_pastas(funil_id) == 9,  # ZZ-ENCERRADAS + a originação + 7
    "nada foi apagado",
)

print("\n5. funil — mostra a encerrada com o motivo")
saida = rodar(vbr_pastas.cmd_funil, [], paciencia=12)
conferir("nenhuma originação aberta" in saida, "o funil ficou vazio")
conferir("ficou com a corretora atual" in saida, "listou o motivo do encerramento")
conferir("aberta há" not in saida, "não listou nada como aberta")

print("\n6. reabrir — o prospecto voltou")
saida = rodar(vbr_pastas.cmd_reabrir, ["s"], nome="CVCP")
conferir(funil_id in orig[0]["parents"], "voltou para a raiz do funil")
conferir(
    "vbr_encerrada" not in orig[0]["appProperties"],
    "a marca de encerramento saiu",
)
conferir(
    len([i for i in falso.itens.values() if i["name"] == "_ENCERRAMENTO.txt"]) == 1,
    "o bilhete fica: é a memória de por que parou da outra vez",
)

print("\n7. promover — a originação atravessa para o cliente")
antes_id = orig[0]["id"]
saida = rodar(
    vbr_pastas.cmd_promover,
    [
        "CVCP",        # nome do cliente
        "Usina Norte", "",   # ativos
        "n",           # frente no grupo?
        "n",           # frente no ativo?
        "s",           # promover?
    ],
    cliente="CVCP",
)
cliente = [i for i in falso.itens.values() if i["name"] == "CVCP" and i["mimeType"].endswith("folder")]
conferir(len(cliente) == 1, "criou a pasta CVCP em CLIENTES")
conferir(clientes_id in cliente[0]["parents"], "está dentro de CLIENTES")
conferir(orig[0]["id"] == antes_id, "a originação é a MESMA pasta: o id não mudou")
conferir(orig[0]["name"] == modelo.ORIGINACAO, f"passou a se chamar {modelo.ORIGINACAO}")
conferir(cliente[0]["id"] in orig[0]["parents"], "mora dentro do cliente agora")
conferir(funil_id not in orig[0]["parents"], "saiu do funil")
conferir(
    len([i for i in falso.itens.values() if i["name"] == "_ENCERRAMENTO.txt"]) == 1,
    "o conteúdo veio junto — mover leva tudo",
)
filhos_cliente = {
    i["name"] for i in falso.itens.values() if cliente[0]["id"] in i["parents"]
}
conferir(
    filhos_cliente == {modelo.ORIGINACAO, "APOLICES", "FRENTES", "USINA-NORTE"},
    f"o cliente tem originação, apólices, frentes e o ativo: {sorted(filhos_cliente)}",
)
conferir(falso.contar_pastas(funil_id) == 1, "no funil sobrou só ZZ-ENCERRADAS, vazia")

print("\n8. auditar o cliente — sem erro")
saida = rodar(vbr_pastas.cmd_auditar, [], cliente="CVCP", funil=False, saida=None)
conferir("0 erro(s)" in saida, f"auditoria limpa\n{saida}")

print("\n9. auditar o funil — sem erro")
saida = rodar(vbr_pastas.cmd_auditar, [], cliente=None, funil=True, saida=None)
conferir("0 erro(s)" in saida, f"funil limpo\n{saida}")

print("\n10. a armadilha: um prospecto largado dentro de CLIENTES")
solto_id = falso._criar("XPTO", clientes_id)
for sub in [modelo.ORIGINACAO]:
    falso._criar(sub, solto_id)
saida = rodar(vbr_pastas.cmd_auditar, [], cliente="XPTO", funil=False, saida=None)
conferir(
    "só tem originação" in saida,
    "a auditoria diagnostica em uma linha, não em três achados soltos",
)

print("\n11. originação parada há tempo demais")
falso.semear(f"GESTAO DE RISCOS/ORIGINACAO/2023-01_ANTIGA")
saida = rodar(vbr_pastas.cmd_funil, [], paciencia=12)
conferir("!" in saida and "2023-01_ANTIGA" in saida, "sinalizou a originação velha")

print("\n" + "=" * 60)
if FALHAS:
    print(f"{len(FALHAS)} falha(s):")
    for f in FALHAS:
        print(f"  - {f}")
    sys.exit(1)
print("tudo passou.")
