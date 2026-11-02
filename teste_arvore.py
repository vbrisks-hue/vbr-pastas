"""
Prova que a leitura de árvore por nível custa ordens de grandeza menos
chamadas ao Drive — e devolve exatamente o mesmo resultado de antes.

    python3 teste_arvore.py

Roda contra o Drive falso; o DriveFalso registra cada chamada em `chamadas`.
"""

from __future__ import annotations

import sys

import drive
from drive_falso import DriveFalso

FALHAS: list[str] = []


def conferir(condicao: bool, descricao: str) -> None:
    print(f"  [{'ok  ' if condicao else 'FALHA'}] {descricao}")
    if not condicao:
        FALHAS.append(descricao)


def ler_arvore_pasta_a_pasta(servico, pasta_id, incluir_arquivos=False) -> dict:
    """A forma antiga, uma chamada por pasta. Fica aqui como régua."""
    resultado: dict = {}
    filhos = drive.listar_filhos(servico, pasta_id)
    arquivos = [f for f in filhos if f["mimeType"] != drive.MIME_PASTA]
    pastas = [f for f in filhos if f["mimeType"] == drive.MIME_PASTA]
    if incluir_arquivos:
        resultado["__arquivos__"] = [a["name"] for a in arquivos]
    for pasta in sorted(pastas, key=lambda p: p["name"]):
        resultado[pasta["name"]] = ler_arvore_pasta_a_pasta(servico, pasta["id"], incluir_arquivos)
    return resultado


def chamadas_de_lista(falso: DriveFalso) -> int:
    return sum(1 for c in falso.chamadas if c.startswith("list"))


# Uma árvore do tamanho de um cliente de verdade: quatro ativos, cada um com
# acervo, três ramos e quatro frentes de sete subpastas. Mais arquivos soltos,
# um nome repetido e uma pasta na lixeira, para a comparação ter o que pegar.
falso = DriveFalso()
cliente = falso.semear("GESTAO DE RISCOS/CLIENTES/GRUPO-TESTE")
falso._criar("00-ORIGINACAO", cliente)
falso._criar("APOLICES", cliente)
falso._criar("FRENTES", cliente)
falso._criar("solto na raiz.pdf", cliente, mime="application/pdf")
for ativo in ("ATIVO-A", "ATIVO-B", "ATIVO-C", "ATIVO-D"):
    a = falso._criar(ativo, cliente)
    acervo = falso._criar("ACERVO", a)
    for sub in ("DOCUMENTACAO-TECNICA", "ENGENHARIA-E-INSPECOES", "CADASTRO-DE-VALORES",
                "CONTRATOS-DO-ATIVO", "PLANTAS-E-IMAGENS"):
        falso._criar(sub, acervo)
    falso._criar("laudo.pdf", acervo, mime="application/pdf")
    apolices = falso._criar("APOLICES", a)
    for ramo in ("RO-BI", "RCG", "D-O"):
        r = falso._criar(ramo, apolices)
        for sub in ("VIGENTE", "HISTORICO", "SINISTROS"):
            falso._criar(sub, r)
    frentes = falso._criar("FRENTES", a)
    for i in range(1, 5):
        f = falso._criar(f"2026-0{i}_FRENTE-{i}", frentes)
        for sub in ("01-INSUMOS", "02-TRABALHOS", "03-ENTREGAS", "04-COTACOES-RECEBIDAS",
                    "05-ANALISE-COMPARATIVA", "06-DECISAO-E-EMISSAO", "07-COMUNICACOES"):
            falso._criar(sub, f)
        falso._criar("ata.docx", f, mime="application/msword")
# Duas pastas com o mesmo nome no mesmo pai: o Drive deixa, e a leitura tem
# de tratar as duas do mesmo jeito de antes.
falso._criar("FRENTES", cliente)
# Uma pasta na lixeira não aparece.
lixo = falso._criar("LIXO", cliente)
falso.itens[lixo]["trashed"] = True

total = falso.contar_pastas(cliente)
print(f"\nárvore de teste: {total} pastas")
conferir(total >= 200, "a árvore tem pelo menos 200 pastas")

for incluir in (False, True):
    rotulo = "com arquivos" if incluir else "só pastas"
    print(f"\nleitura {rotulo}")

    falso.chamadas.clear()
    antiga = ler_arvore_pasta_a_pasta(falso, cliente, incluir)
    n_antiga = chamadas_de_lista(falso)

    falso.chamadas.clear()
    nova = drive.ler_arvore(falso, cliente, incluir)
    n_nova = chamadas_de_lista(falso)

    conferir(nova == antiga, "o resultado é idêntico ao da leitura pasta a pasta")
    conferir(list(nova) == list(antiga), "a ordem das chaves é a mesma")
    conferir(n_antiga >= total, f"pasta a pasta custou {n_antiga} chamadas (uma por pasta)")
    conferir(n_nova * 10 <= n_antiga, f"por nível custou {n_nova} chamadas — {n_antiga // max(n_nova, 1)}x menos")
    conferir("LIXO" not in nova, "a pasta na lixeira não aparece")
    if incluir:
        conferir(nova["__arquivos__"] == ["solto na raiz.pdf"], "arquivo solto na raiz do cliente aparece")
        conferir(nova["ATIVO-A"]["ACERVO"]["__arquivos__"] == ["laudo.pdf"], "arquivo dentro do acervo aparece")

print("\nlotes")
falso.chamadas.clear()
pais = [i["id"] for i in falso.itens.values() if i["mimeType"] == drive.MIME_PASTA][:60]
por_pai = drive.listar_filhos_de_varios(falso, pais)
conferir(chamadas_de_lista(falso) == 3, "60 pais viram 3 consultas de até 25")
conferir(all(all(pai in f["parents"] for f in filhos) for pai, filhos in por_pai.items()),
         "cada filho aparece sob o pai certo")

print("\n" + "=" * 60)
if FALHAS:
    print(f"{len(FALHAS)} falha(s):")
    for f in FALHAS:
        print(f"  - {f}")
    sys.exit(1)
print("tudo passou.")
