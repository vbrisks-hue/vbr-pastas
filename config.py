"""
Configuração do programa — onde ficam os clientes e o funil no Drive.

Os caminhos não moram no código. Ficam num `config.json` ao lado dos
arquivos, que o programa cria sozinho na primeira execução perguntando uma vez.

Ordem de precedência, da mais forte para a mais fraca:
  1. a opção --raiz na linha de comando (vale só para aquela execução)
  2. a variável de ambiente VBR_RAIZ
  3. o config.json
  4. a pergunta na primeira execução, que grava a resposta

São dois caminhos: o dos clientes e o do funil. O do funil tem a mesma
escada (--originacao, VBR_ORIGINACAO, config.json) e, no fim dela, em vez de
perguntar, deduz: a pasta irmã de CLIENTES chamada ORIGINACAO.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

ARQUIVO = Path(os.environ.get("VBR_CONFIG", "config.json"))

# Sugestão oferecida na primeira execução. É só um palpite — o que vale é
# o que você responder, e a resposta fica gravada.
RAIZ_SUGERIDA = "GESTÃO DE RISCOS/CLIENTES"


def ler() -> dict:
    if not ARQUIVO.exists():
        return {}
    try:
        return json.loads(ARQUIVO.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as erro:
        print(f"aviso: não consegui ler {ARQUIVO} ({erro}); seguindo sem ele.")
        return {}


def gravar(dados: dict) -> None:
    ARQUIVO.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def raiz(opcao_linha_comando: str | None = None, perguntar_se_faltar=None) -> str:
    """
    Devolve o caminho da pasta de clientes.

    `perguntar_se_faltar` é uma função que recebe (texto, padrao) e devolve a
    resposta. Fica assim para o config não depender do terminal e continuar
    testável.
    """
    if opcao_linha_comando:
        return opcao_linha_comando

    do_ambiente = os.environ.get("VBR_RAIZ")
    if do_ambiente:
        return do_ambiente

    dados = ler()
    if dados.get("raiz"):
        return dados["raiz"]

    if perguntar_se_faltar is None:
        return RAIZ_SUGERIDA

    print()
    print("Primeira execução: onde ficam as pastas de clientes no seu Drive?")
    print("  Use o caminho a partir da raiz do Meu Drive, com barras.")
    print(f"  Exemplo: {RAIZ_SUGERIDA}")
    print()
    escolhido = perguntar_se_faltar("Caminho", RAIZ_SUGERIDA).strip("/")
    dados["raiz"] = escolhido
    gravar(dados)
    print(f"gravado em {ARQUIVO}. Para mudar depois: vbr_pastas.py config")
    return escolhido


def definir_raiz(caminho: str) -> None:
    dados = ler()
    dados["raiz"] = caminho.strip("/")
    gravar(dados)


# ---------------------------------------------------------------------------
# A raiz do funil — onde ficam as originações que ainda não viraram cliente.
#
# Não é uma segunda pergunta na primeira execução. Por padrão ela é deduzida:
# a pasta irmã de CLIENTES chamada ORIGINACAO. Quem quiser outro lugar grava
# o caminho, e aí a dedução para de valer.
# ---------------------------------------------------------------------------

NOME_DA_ORIGINACAO = "ORIGINACAO"


def irma_de(caminho_clientes: str, nome: str = NOME_DA_ORIGINACAO) -> str:
    """
    'GESTÃO DE RISCOS/CLIENTES' -> 'GESTÃO DE RISCOS/ORIGINACAO'

    Troca só o último degrau. Se o caminho tiver um degrau só, a irmã fica na
    raiz do Meu Drive, ao lado dele.
    """
    degraus = [d for d in caminho_clientes.strip("/").split("/") if d]
    return "/".join(degraus[:-1] + [nome]) if degraus else nome


def raiz_originacao(
    opcao_linha_comando: str | None = None, caminho_clientes: str | None = None
) -> str:
    """
    Mesma precedência da raiz de clientes, com um degrau a mais no fim:
    --originacao, VBR_ORIGINACAO, config.json, e por último a dedução.
    """
    if opcao_linha_comando:
        return opcao_linha_comando.strip("/")

    do_ambiente = os.environ.get("VBR_ORIGINACAO")
    if do_ambiente:
        return do_ambiente.strip("/")

    dados = ler()
    if dados.get("originacao"):
        return dados["originacao"]

    return irma_de(caminho_clientes or raiz())


def definir_raiz_originacao(caminho: str) -> None:
    dados = ler()
    dados["originacao"] = caminho.strip("/")
    gravar(dados)
