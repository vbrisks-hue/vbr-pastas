"""
Alinhar uma frente com a forma do modelo.

Seis frentes do GRUPO-DIAMANTE foram criadas na migração de 14/09, e o
caderno v4 travou as cinco formas depois: ficaram com 06-DECISAO-EMISSAO no
lugar de 06-DECISAO-E-EMISSAO, 05-ANALISE no lugar de 05-ANALISE-COMPARATIVA,
e sem a COMUNICACOES do fim. É conserto mecânico, e este módulo o descreve.

O que alinhar faz: RENOMEIA subpastas que têm par no modelo e CRIA as que
faltam. O que nunca faz: apagar pasta, mover arquivo, mexer no nome da
frente. Pasta fora do modelo que não tem par fica como está, e o plano diz.

O par é decidido pelo número: `06-DECISAO-EMISSAO` casa com a esperada que
começa por `06-` se — e só se — essa esperada ainda não existe. Se as duas
existirem, nada se renomeia: decidir o que fazer com o conteúdo é de gente.

Nada aqui toca o Drive. Devolve um plano; quem executa é o servidor ou o
terminal, depois da confirmação.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import modelo

_PREFIXO = re.compile(r"^(\d{2})-")


@dataclass
class Plano:
    tipo: str
    renomear: list[tuple[str, str]] = field(default_factory=list)   # (de, para)
    criar: list[str] = field(default_factory=list)
    ficam: list[str] = field(default_factory=list)                   # fora do modelo, sem par
    ja_estava: bool = False

    def vazio(self) -> bool:
        return not self.renomear and not self.criar


def _prefixo(nome: str) -> str | None:
    casamento = _PREFIXO.match(nome.strip())
    return casamento.group(1) if casamento else None


def planejar(presentes: list[str], tipo: str | None = None) -> Plano:
    """
    Dado o que a frente tem hoje, e a forma que ela deve ter, diz o que
    renomear e o que criar. Sem `tipo`, usa a forma mais parecida.
    """
    presentes = list(presentes)
    if tipo is None:
        tipo = modelo.tipo_por_subpastas(presentes) or modelo.tipo_mais_proximo(presentes)[0]
    tipo = tipo.upper()
    if tipo not in modelo.TIPOS_FRENTE:
        raise ValueError(f"tipo de frente desconhecido: {tipo}")
    esperadas = list(modelo.TIPOS_FRENTE[tipo]["subpastas"])
    plano = Plano(tipo=tipo)

    if set(presentes) == set(esperadas):
        plano.ja_estava = True
        return plano

    # Uma esperada só pode receber um renome, e só se ainda não existir.
    por_prefixo = {_prefixo(e): e for e in esperadas}
    presentes_exatas = set(presentes)
    reservadas: set[str] = set()
    for nome in presentes:
        if nome in esperadas:
            continue
        alvo = por_prefixo.get(_prefixo(nome))
        if alvo and alvo not in presentes_exatas and alvo not in reservadas:
            plano.renomear.append((nome, alvo))
            reservadas.add(alvo)
        else:
            plano.ficam.append(nome)

    depois = presentes_exatas | reservadas
    plano.criar = [e for e in esperadas if e not in depois]
    return plano


def linhas_do_plano(plano: Plano) -> tuple[list[str], list[str], list[str]]:
    """As três listas de linhas para mostrar: renomear, criar, avisos."""
    renomear = [f"{de}  →  {para}" for de, para in plano.renomear]
    criar = list(plano.criar)
    avisos = [f"{nome} não tem par na forma {plano.tipo}: fica como está, com o que tem dentro."
              for nome in plano.ficam]
    return renomear, criar, avisos
