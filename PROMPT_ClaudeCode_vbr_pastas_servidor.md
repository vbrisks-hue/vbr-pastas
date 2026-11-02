# Prompt para o Claude Code — tela do vbr-pastas

Cole o conteúdo abaixo da linha numa sessão do Claude Code aberta na pasta
`~/vbr_pastas`. Ele é autossuficiente: não depende desta conversa.

---

Você está na pasta de um programa chamado **vbr-pastas**, que monta e confere
a árvore de pastas de clientes da VB Risk no Google Drive. Ele funciona e está
em uso. Sua tarefa é dar a ele uma **tela** — uma página no navegador, servida
por um servidor local em Python — sem tocar no que já existe.

## Antes de escrever uma linha

Leia, nesta ordem:

1. `DECISOES.md` — o que foi decidido, por quê, e o que está aberto
2. `modelo.py` — o modelo inteiro vive aqui
3. `drive.py` — a camada sobre a API do Drive
4. `vbr_pastas.py` — o terminal de hoje, que é a referência de comportamento
5. `auditoria.py` — as regras de conferência
6. `drive_falso.py` e `teste_funil.py` — como se testa sem tocar no Drive
7. `MANUAL.md` — o modelo explicado para quem usa

Não repita neles o que já está escrito. O objetivo não é reimplementar nada:
é **chamar** o que existe a partir de uma página.

## Quem vai usar

Fabio Medeiros, sócio da VB Risk. Não é programador e não gosta do terminal —
a instalação de hoje travou três vezes em coisas de terminal, não de conceito.
Ele tem olho apurado para desenho e lê tudo o que aparece na tela. Escreva a
interface para ele: em português, sem jargão, com os nomes que a casa usa
(originação, frente, acervo, ramo, mandato, competência).

Código e comentários também em português, como o resto do programa. Os
comentários explicam **por quê**, não o quê.

## Regras invioláveis

Quebrar qualquer uma destas é pior do que não entregar.

**1. Nunca teste contra o Drive de verdade.** Existe `drive_falso.py`, um
Drive em memória com a mesma cara da API. Todo teste passa por ele. Uma sessão
que "testa" a promoção com as credenciais reais move pasta de cliente de
verdade, e não há desfazer.

**2. Nunca toque em `credentials.json`, `token.json` nem `config.json`.** Não
leia para "conferir", não reescreva, não faça backup, não inclua em nada.
O `credentials.json` dá acesso ao Drive inteiro da conta.

**3. Nada é criado, movido ou renomeado sem o plano aparecer e o usuário
confirmar.** Vale para toda ação de escrita, sem exceção. O plano mostra a
árvore inteira e a contagem antes de qualquer chamada. Na página, o padrão é
sempre "não": nenhum botão que escreve pode ser o alvo natural de um Enter
distraído.

**4. O modelo só muda em `modelo.py`.** Se a tela precisar saber os tipos de
frente, as subpastas da originação ou a grafia, ela pergunta ao `modelo.py`.
Nenhuma lista de subpastas escrita à mão no HTML ou no JavaScript. É a regra
que mantém o modelo existindo uma vez só.

**5. Sem dependências novas.** Só a biblioteca padrão do Python mais as que já
estão no `requirements.txt`. Nada de Flask, FastAPI, npm, React, Tailwind.
O usuário passou a tarde instalando coisa; não peça mais nenhuma.

**6. O servidor escuta em `127.0.0.1`.** Nunca em `0.0.0.0`. Ninguém na rede
alcança.

**7. Uma página só.** HTML, CSS e JavaScript no mesmo arquivo, servido pelo
Python. Sem CDN, sem fonte externa, sem build.

## O que construir — etapa 1

### `servidor.py`

Um servidor com `http.server` da biblioteca padrão que:

- serve a página em `http://127.0.0.1:8765` (porta configurável; 8765 foi
  escolhida para ficar longe das do MAMP — 8888, 8889, 3306)
- abre o navegador sozinho ao iniciar (`webbrowser.open`)
- expõe alguns endereços que devolvem JSON e chamam os módulos existentes
- imprime uma linha só no terminal, dizendo o endereço e como parar
- aceita `--falso`, que troca `drive.conectar()` pelo `DriveFalso` já povoado
  com um exemplo. É assim que se desenvolve e se demonstra a tela sem
  credencial nenhuma. **Faça isto primeiro**, antes de qualquer tela.

Os erros aparecem na página, em português, e não como traceback. Um erro do
Drive vira uma frase que o usuário entenda; o traceback vai para o terminal.

### `VBR Pastas.command`

Um arquivo de duplo clique para o macOS: entra na pasta, roda
`python3 servidor.py`, e deixa a janela aberta. Precisa de `chmod +x`, e o
script deve dizer isso ao usuário se ainda não estiver marcado.

### As telas da etapa 1

**Funil** — a tela inicial:

```
FUNIL                                         + Nova originação

2026-03_CVCP           aberta há 6 meses       [Promover] [Encerrar]
2026-08_XPTO           aberta há 1 mês         [Promover] [Encerrar]
2023-01_ANTIGA    !    aberta há 44 meses      [Promover] [Encerrar]

ENCERRADAS
2025-11_FULANO    11/2025 — ficou com a corretora atual      [Reabrir]
```

O `!` marca as que passaram da paciência (doze meses, decisão 8). Elas
merecem destaque visual, não um alarme: originação parada não é erro, é uma
decisão que ninguém tomou.

**Nova originação** — nome e competência. Mostre a grafia da casa se
atualizando enquanto o usuário digita (`Campo Verde` → `CAMPO-VERDE`), para
ele ver o nome antes de criar em vez de descobrir na auditoria depois.

**Promover** — o formulário pede o nome do cliente (já preenchido com o nome
da originação), os ativos e as frentes. O plano sai em duas partes, porque são
duas operações de natureza diferente:

```
MOVER   ORIGINACAO/2026-03_CVCP
     →  CLIENTES/CVCP/00-ORIGINACAO   (com tudo dentro)

CRIAR   CVCP/APOLICES
        CVCP/FRENTES
        CVCP/USINA-NORTE/ACERVO  (+5 subpastas)
        ...
        26 pastas

                                    [Confirmar]  [Cancelar]
```

**Encerrar** — pede o motivo, e **não deixa encerrar sem ele**. Diga na tela
por quê, em uma linha: é o que dá valor ao registro quando o nome voltar.

**Reabrir** — confirmação simples, avisando que o `_ENCERRAMENTO.txt` fica.

### A leitura de árvore mais rápida

Entra nesta etapa, porque sem ela a tela trava. Hoje `drive.ler_arvore` faz
**uma chamada por pasta**: 440 chamadas no GRUPO-DIAMANTE, minutos de espera.

O caminho: em vez de descer pasta por pasta, leia **por nível**, juntando os
ids dos pais numa consulta só:

```
('id1' in parents or 'id2' in parents or ...) and trashed = false
```

Vinte e cinco ids por consulta é um lote seguro — a consulta do Drive tem
limite de tamanho, e estourar dá erro difícil de ler. Isso derruba 440
chamadas para umas vinte.

Mantenha `ler_arvore` com a mesma assinatura e o mesmo formato de saída, para
a auditoria não mudar em nada. E mantenha a deduplicação por id: a paginação
do Drive devolve a mesma entrada em páginas diferentes quando a pasta muda
durante a varredura — uma pasta de 169 arquivos vira 193 se você somar as
páginas.

Prove a melhora com um teste no `drive_falso.py`: monte uma árvore de umas
200 pastas e conte as chamadas (o `DriveFalso` já registra em `chamadas`).

## Etapas 2 e 3 — não faça agora

Deixe prontas para depois, sem começar:

**Etapa 2** — abrir frente, abrir ramo, criar cliente e a auditoria na tela.

A tela de frente é a que mais ganha da página, e está desenhada assim: o
destino vem de uma **lista lida do Drive**, não de um caminho digitado
(`GRUPO-DIAMANTE`, `GRUPO-DIAMANTE / CTJL`, ...); e o tipo se escolhe em
**cartões que mostram as subpastas de cada um**, não por número. Metade dos
avisos da primeira auditoria real foi frente montada à mão por quem não
lembrava da forma.

A auditoria na tela agrupa os achados por tipo, em vez da lista corrida do
terminal.

**Etapa 3** — o programa subindo sozinho com o Mac, via `launchd`, sem janela
de terminal.

## Fora de escopo, de propósito

- **O comando `alinhar`**, que consertaria as seis frentes que estão atrás do
  modelo v4. Está decidido que existe a necessidade; não está decidido fazer.
- **As quatro decisões abertas da auditoria** (ROADSHOW, arquivos soltos,
  apólice na raiz, duplicata). São decisões do usuário, não trabalho de tela.
- **Qualquer mudança no modelo.** Se algo no `modelo.py` parecer errado,
  escreva a observação e pergunte. Não corrija.
- **Levar isto para o AVRA.** O AVRA é outro sistema, em PHP, e a decisão
  registrada é testar fora dele primeiro.

## Armadilhas do Google Drive já pagas

Cada uma custou tempo de verdade. Estão implementadas no código; não as
desfaça ao mexer.

1. **Espaço no fim do nome é invisível e quebra busca exata.**
   `FRENTE CESSÃO BANCO ` conviveu meses sem ninguém notar.
2. **O Drive numera cópias, e a de número maior costuma ser a mais nova.**
   `PACOTE 2` frequentemente é mais recente que `PACOTE`. Confira datas.
3. **A paginação repete entradas.** Sempre deduplique por id antes de contar.
4. **Arquivo cujo dono é outra conta não se move**, por mais permissão que se
   tenha.
5. **Pasta de descarte aninhada dentro de pasta que se move vai junto** e
   nunca mais é purgada.
6. **Id de pasta guardado de memória não é confiável.** Confirme navegando
   pelo caminho.
7. **`appProperties` é privado do cliente OAuth que gravou.** Regerar a
   credencial com outro client_id torna as etiquetas antigas invisíveis. Por
   isso a busca por nome continua existindo como recurso.
8. **Acento tem duas formas em Unicode.** O macOS grava NFD (`A` + til
   combinante), o resto costuma gravar NFC (`Ã`). Iguais na tela, diferentes
   na busca. `drive._chave` resolve; não remova.

## Como saber que está pronto

- `python3 teste_funil.py` continua passando, sem nenhuma alteração nele além
  das que você acrescentar
- `python3 servidor.py --falso` sobe, abre o navegador, e dá para percorrer o
  ciclo inteiro — originar, encerrar, reabrir, promover — sem credencial
- um teste novo prova que a leitura de árvore usa ordens de grandeza menos
  chamadas
- nenhum arquivo de credencial ou configuração foi lido, escrito ou movido
- a página funciona sem internet além do próprio Drive: nenhuma fonte, script
  ou folha de estilo vinda de fora

Ao terminar, escreva em uma página o que mudou e o que ficou de fora — e
acrescente ao `DECISOES.md` qualquer decisão que você tiver tomado no caminho,
com o motivo junto. Decisão sem motivo não se defende seis meses depois.
