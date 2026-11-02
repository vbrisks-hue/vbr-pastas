"""Testa o plano de alinhamento, sem Drive.    python3 teste_alinhar.py"""

from __future__ import annotations

import sys

import alinhar

FALHAS: list[str] = []


def conferir(condicao: bool, descricao: str) -> None:
    print(f"  [{'ok  ' if condicao else 'FALHA'}] {descricao}")
    if not condicao:
        FALHAS.append(descricao)


BASE = ["01-INSUMOS", "02-TRABALHOS", "03-ENTREGAS"]

print("\n1. as três situações do GRUPO-DIAMANTE")
p = alinhar.planejar(BASE + ["04-COTACOES-RECEBIDAS", "05-ANALISE-COMPARATIVA", "06-DECISAO-EMISSAO"])
conferir(p.tipo == "RENOVACAO", "renovação antiga é reconhecida como RENOVACAO")
conferir(p.renomear == [("06-DECISAO-EMISSAO", "06-DECISAO-E-EMISSAO")], "renomeia a 06 pelo número")
conferir(p.criar == ["07-COMUNICACOES"], "cria a 07 que falta")
conferir(not p.ficam, "nada fica de fora")

p = alinhar.planejar(BASE + ["04-PROPOSTAS-RECEBIDAS", "05-ANALISE", "06-DECISAO"])
conferir(p.tipo == "CONCORRENCIA", "RFP antiga é CONCORRENCIA")
conferir(p.renomear == [("05-ANALISE", "05-ANALISE-COMPARATIVA")] and p.criar == ["07-COMUNICACOES"],
         "renomeia a 05 e cria a 07")

p = alinhar.planejar(BASE + ["04-DECISOES"])
conferir(p.tipo == "ANALISE" and not p.renomear and p.criar == ["05-COMUNICACOES"], "análise antiga só ganha a 05")

print("\n2. o que não se faz")
p = alinhar.planejar(BASE + ["04-COTACOES-RECEBIDAS", "05-ANALISE-COMPARATIVA", "06-DECISAO-E-EMISSAO", "07-COMUNICACOES"])
conferir(p.ja_estava and p.vazio(), "frente já na forma: nada a fazer")
p = alinhar.planejar(BASE + ["04-COTACOES-RECEBIDAS", "05-ANALISE-COMPARATIVA", "06-DECISAO-EMISSAO", "06-DECISAO-E-EMISSAO"])
conferir(not p.renomear and p.ficam == ["06-DECISAO-EMISSAO"], "se a nova já existe, a antiga fica e não se renomeia")
p = alinhar.planejar(BASE + ["04-DECISOES", "05-COMUNICACOES", "FOTOS"])
conferir(p.tipo == "ANALISE" and p.ficam == ["FOTOS"] and p.vazio(), "pasta sem número não tem par: fica")
p = alinhar.planejar(BASE + ["04-DECISOES", "05-COMUNICACOES", "06-EXTRA"])
conferir(p.ficam == ["06-EXTRA"] and not p.criar, "número sem esperada correspondente: fica")

print("\n3. escolhendo o tipo à mão")
p = alinhar.planejar(BASE + ["04-DECISOES"], tipo="sinistro")
conferir(p.tipo == "SINISTRO" and p.renomear == [("04-DECISOES", "04-REGULACAO")]
         and p.criar == ["05-ENCERRAMENTO", "06-COMUNICACOES"], "forçando SINISTRO: 04 vira REGULACAO, faltam 05 e 06")
try:
    alinhar.planejar(BASE, tipo="INVENTADO")
    conferir(False, "tipo inventado deveria falhar")
except ValueError:
    conferir(True, "tipo inventado é recusado")

print("\n4. as linhas do plano")
p = alinhar.planejar(BASE + ["04-COTACOES-RECEBIDAS", "05-ANALISE-COMPARATIVA", "06-DECISAO-EMISSAO", "RASCUNHOS"])
r, c, a = alinhar.linhas_do_plano(p)
conferir(r == ["06-DECISAO-EMISSAO  →  06-DECISAO-E-EMISSAO"] and c == ["07-COMUNICACOES"] and "RASCUNHOS" in a[0],
         "renomear, criar e aviso do que fica")

print("\n" + "=" * 60)
if FALHAS:
    print(f"{len(FALHAS)} falha(s):")
    for f in FALHAS:
        print(f"  - {f}")
    sys.exit(1)
print("tudo passou.")
