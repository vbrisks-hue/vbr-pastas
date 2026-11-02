# A tela — etapa 3 (16/09/2026)

O programa passa a poder subir sozinho com o Mac, sem janela de Terminal,
por um agente do `launchd` da própria conta. A instalação se faz na aba
**Sistema** da página, com plano e confirmação, ou pelo Terminal.

## O que entrou

| Arquivo | O que é |
|---|---|
| `lancador.py` | o agente: o conteúdo do `.plist`, instalar, desinstalar, situação; recebe a pasta home e o `launchctl` por parâmetro, para o teste não tocar no Mac |
| `teste_lancador.py` | o ciclo inteiro contra um `launchctl` de mentira |
| `TELA_ETAPA3.md` | esta página |

**Aba Sistema.** O programa (Drive, caminhos, pasta, Python, se este
servidor é o do atalho ou o de fundo) e o agente: não instalado, ou
instalado e rodando com o número do processo, com o caminho do `.plist`,
do log e do atalho. Botões: Subir com o Mac; depois, Regravar e Deixar de
subir com o Mac.

**O atalho sem Terminal.** A instalação grava `Abrir VBR Pastas.webloc` na
pasta do programa: duplo clique abre a tela no navegador.

## O que mudou no que existia

- **`servidor.py`** — `--fundo` (sem navegador; espera a porta ocupada e
  assume quando ela libera), `--instalar`, `--desinstalar`, `--situacao`;
  `/api/sistema`, `/api/instalar/plano`, `/api/desinstalar/plano`; a `Tela`
  recebe o lançador.
- **`pagina.html`** — a aba Sistema.
- **`teste_servidor.py`** — seção 15.
- **`DECISOES.md`** — decisões 29 a 33.

## Como instalar

Na página, aba Sistema, **Subir com o Mac**, conferir o plano, Confirmar.
Se a página estiver sendo servida pelo atalho, o programa de fundo sobe,
espera, e assume quando a janela do Terminal fechar. Daí em diante a tela
abre por `Abrir VBR Pastas.webloc` ou pelo endereço `http://127.0.0.1:8765`.

Pelo Terminal, na pasta do programa:

    python3 servidor.py --instalar
    python3 servidor.py --situacao
    python3 servidor.py --desinstalar

Depois de trocar arquivos do programa: **Regravar**, na aba Sistema.

## Como foi conferido

- Os quatro testes passam (`teste_funil`, `teste_arvore`, `teste_lancador`,
  `teste_servidor`).
- Uma prova real, temporária: um agente de teste (`com.vbrisk.pastas.teste`,
  porta 8799, modo de demonstração) foi carregado no launchd desta conta,
  esperou um servidor manual fechar, assumiu a porta em poucos segundos, e
  foi descarregado e apagado. Nenhum agente ficou em `~/Library/LaunchAgents`.
- **O agente de verdade foi instalado em seguida, a pedido** (16/09, 19:38): rodando contra o Drive de verdade, nos caminhos do `config.json`.
- No navegador, com `--falso`: a aba Sistema e o plano de instalação.

## O que ficou de fora

- Rotação do log. Configuração pela página. `alinhar` e as decisões da
  auditoria. Qualquer mudança no modelo.
