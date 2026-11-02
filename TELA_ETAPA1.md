# A tela — etapa 1 (16/09/2026)

O vbr-pastas ganhou uma página no navegador, servida por um servidor local em
Python, sem tocar no que já existia. Duplo clique em `VBR Pastas.command`
abre a tela; `python3 servidor.py --falso` abre a mesma tela contra um Drive
de demonstração, sem credencial.

## O que entrou

| Arquivo | O que é |
|---|---|
| `servidor.py` | o servidor (`http.server`, só biblioteca padrão), em `127.0.0.1:8765`; os endereços JSON que a página chama; a classe `Tela`, que é a aplicação sem HTTP |
| `pagina.html` | a página inteira — HTML, CSS e JavaScript — sem nada de fora |
| `VBR Pastas.command` | o atalho de duplo clique; escolhe um Python 3.10+ com as bibliotecas do Google e sobe o servidor |
| `teste_servidor.py` | o ciclo inteiro pelo HTTP — originar, encerrar, reabrir, promover — contra o Drive falso |
| `teste_arvore.py` | prova que a leitura de árvore usa ordens de grandeza menos chamadas, com resultado idêntico |
| `TELA_ETAPA1.md` | esta página |

## O que mudou no que existia

- **`drive.py`** — `ler_arvore` lê por nível, 25 pais por consulta
  (`listar_filhos_de_varios`). Mesma assinatura, mesma saída. 217 chamadas
  viraram 11 numa árvore de 216 pastas.
- **`drive_falso.py`** — entende consulta com vários pais, devolve `parents`
  quando pedido, e ganhou `com_exemplo()`: o Drive de demonstração.
- **`DECISOES.md`** — decisões 14 a 22, e uma observação.

Nada mais foi alterado. `modelo.py`, `auditoria.py`, `vbr_pastas.py`,
`config.py` e `teste_funil.py` estão como estavam.

## As telas

**Funil.** Abertas com a idade em meses; as que passaram da paciência levam a
marca `!` e um fundo âmbar — destaque, não alarme. Encerradas com data e
motivo. Botões: Promover, Encerrar, Reabrir, + Nova originação.

**Nova originação.** Nome e competência; a grafia da casa aparece enquanto se
digita (`Campo Verde` → `2026-09_CAMPO-VERDE`). A grafia vem do servidor, que
pergunta ao `modelo.py`: a página não sabe normalizar nome nenhum.

**Promover.** Nome do cliente já preenchido, ativos e frentes (onde mora,
título, competência, tipo). O plano sai em duas partes — MOVER e CRIAR — com a
contagem.

**Encerrar.** Pede o motivo e não encerra sem ele; a tela diz por quê em uma
linha.

**Reabrir.** Plano simples, avisando que o `_ENCERRAMENTO.txt` fica.

Em todas: primeiro o plano, depois Confirmar. O foco nasce em Cancelar; Enter
nunca escreve. Erro do Drive vira frase em português; o traceback fica no
terminal.

## Como foi conferido

- `python3 teste_funil.py` — passa, sem nenhuma alteração no arquivo.
- `python3 teste_arvore.py` — passa: 11 chamadas em vez de 217, saída idêntica.
- `python3 teste_servidor.py` — passa: 56 verificações pelo HTTP, incluindo
  senha inventada, senha reaproveitada, escrita vinda de outro site, encerrar
  sem motivo, promover encerrada, tipo fora do modelo.
- `python3 servidor.py --falso` — a tela foi percorrida no navegador: originar,
  ver o plano, Enter no plano (nada acontece), confirmar, promover com ativo e
  frente, ver o plano em duas partes, confirmar, encerrar e reabrir.
- A página não referencia nenhum endereço externo (conferido por busca).
- `credentials.json`, `token.json` e `config.json` não foram lidos, escritos
  nem movidos.

## O que ficou de fora, de propósito

- **Etapa 2** — abrir frente, abrir ramo, criar cliente e a auditoria na
  tela. O `/api/modelo` já devolve tudo que os cartões de tipo vão mostrar.
- **Etapa 3** — o programa subindo com o Mac, via `launchd`.
- **`alinhar`** e as quatro decisões abertas da auditoria.
- **Qualquer mudança no modelo.** Uma observação foi registrada no
  `DECISOES.md`: a decisão 10 (`achar_pasta` comparando normalizado) e o
  `drive._chave` não estão no `drive.py` desta pasta. Não foi corrigido.
- **Configuração pela página.** Se o caminho gravado estiver errado, a tela
  diz onde quebrou e o que existe ali, e manda para o `config` do terminal.

## Uma pasta, duas cópias

Há uma cópia idêntica dos fontes em `~/Desktop/Pastas Python/vbr_pastas`.
Esta etapa foi feita em `~/vbr_pastas`, que é a pasta em uso (tem a
credencial e o token). A cópia do Desktop não foi tocada.
