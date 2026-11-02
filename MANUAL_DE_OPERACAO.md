# Manual de operação — VBR Pastas
### A tela do vbr-pastas, no dia a dia
*Versão 1.0 — 16 de setembro de 2026*

Este manual diz **como operar a tela**: abrir, criar, promover, encerrar,
conferir, e o que fazer quando algo dá errado. Não explica o modelo de
pastas — isso está no `MANUAL.md`, partes 1 e 2. Se a dúvida é *onde um
documento mora*, é lá. Se a dúvida é *qual botão apertar*, é aqui.

**Se você tem trinta segundos:** duplo clique em `Abrir VBR Pastas.webloc`.
Toda ação mostra um plano antes; nada muda no Drive até você clicar em
**Confirmar**. Enter nunca confirma.

---

## 1. Abrir a tela

O programa sobe sozinho quando você entra na sua conta do Mac, sem janela
nenhuma. Para ver a tela:

- **duplo clique em `Abrir VBR Pastas.webloc`**, na pasta `vbr_pastas`; ou
- no navegador, o endereço `http://127.0.0.1:8765` (vale guardar nos
  favoritos).

A página só existe neste Mac. Ninguém na rede alcança, e nada dela sai para
a internet além das chamadas ao seu próprio Google Drive.

**Se o navegador disser que não conseguiu conectar**, o programa de fundo
não está no ar. Duplo clique em `VBR Pastas.command`: abre uma janela do
Terminal com uma linha só e a tela em seguida. Depois, na aba **Sistema**,
veja o que aconteceu (seção 6).

No alto da página há quatro abas — **Funil**, **Clientes**, **Auditoria**,
**Sistema** — e, à direita, onde o programa está olhando: `Drive da VB
Risk · GESTAO DE RISCOS/CLIENTES`. Se aparecer uma faixa âmbar dizendo
*Drive de demonstração*, você está na demonstração (porta 8766): nada ali é
de verdade.

**Para brincar sem risco**, existe a demonstração: no Terminal, dentro da
pasta do programa, `python3 servidor.py --falso`. Ela abre em outro
endereço, `http://127.0.0.1:8766`, com a faixa âmbar. As pastas existem só
na memória e somem quando a janela fecha. A tela de verdade continua no ar
na 8765, sem se misturar.

## 2. A regra que vale para tudo

Toda ação que cria, move ou renomeia segue o mesmo caminho:

1. você preenche o que a folha pede;
2. clica em **Ver o plano** — o programa mostra a árvore inteira e a
   contagem, e **ainda não tocou em nada**;
3. lê o plano;
4. clica em **Confirmar** — só agora o Drive muda.

Três coisas para confiar:

- **Enter nunca escreve.** No formulário, Enter pede o plano (que não muda
  nada). No plano, Enter não faz nada; o foco nasce em Cancelar. Confirmar
  é sempre um clique.
- **Rodar duas vezes é seguro.** O programa procura antes de criar: pasta
  que já existe é reaproveitada, nunca duplicada. Se algo falhar no meio,
  repita.
- **Um plano é de uso único** e vale meia hora. Se você deixou a folha
  aberta e voltou depois, peça o plano de novo — o Drive pode ter mudado.

Depois de Confirmar, a folha mostra o que aconteceu, passo a passo:
`+` criada agora · `=` já existia · `>` mudou de lugar · `-` apagada.

## 3. Funil — quem ainda não assinou

É a tela inicial. Lista as originações abertas, há quantos meses, e as
encerradas, com data e motivo.

A marca **`!`** com fundo âmbar é originação aberta há mais de doze meses.
Não é erro: é uma decisão que ninguém tomou. Fechar ou encerrar.

**+ Nova originação.** Nome do prospecto e competência (`AAAA-MM`, quando
a conversa começou — não hoje). Enquanto você digita, a grafia da casa
aparece: `Campo Verde` vira `2026-09_CAMPO-VERDE`. É esse o nome que vai
para o Drive. Cria a originação com as seis subpastas, e só isso: sem
acervo, sem apólice, sem frente, porque ainda não há mandato.

**Promover.** Assinou. O nome do cliente vem preenchido com o da
originação; acrescente os ativos (**+ Ativo**, um por linha) e, se já
houver trabalho começando, as frentes (**+ Frente**: onde mora, título,
competência, tipo). O plano sai em duas partes:

- **MOVER** — a pasta da originação sai do funil, entra em CLIENTES e
  passa a se chamar `00-ORIGINACAO`, com tudo dentro. É a mesma pasta,
  com o mesmo link e o mesmo compartilhamento.
- **CRIAR** — o que cresce ao redor dela: APOLICES, FRENTES, cada ativo com
  seu acervo.

**Encerrar.** Pede o motivo, em uma linha, e **não encerra sem ele**: é o
que dá valor ao registro quando o nome voltar, dali a dois anos. A pasta
vai para `ZZ-ENCERRADAS` com um bilhete `_ENCERRAMENTO.txt` dentro. Nada é
apagado.

**Reabrir.** Traz de volta ao funil. O bilhete fica.

## 4. Clientes — quem tem mandato

Lista cada cliente e, abaixo dele, cada ativo, lidos do Drive naquele
momento. Em cada linha:

**+ Ativo** (só na linha do cliente). O mandato ganhou uma usina, ou um
ativo ficou de fora na promoção. Nome do ativo, com a grafia aparecendo;
se já houver apólice, marque os ramos; se já houver trabalho, **+ Frente**.
Nasce com `ACERVO` e os cinco compartimentos, `APOLICES` e `FRENTES`, e
nada do que o cliente já tem é tocado. Não use "+ Novo cliente" com o nome
de um cliente que já existe para isso: ele mexeria também na originação.

**Frente.** A folha já vem apontando para a linha de onde você clicou
(`GRUPO-DIAMANTE` ou `GRUPO-DIAMANTE / CTJL`). Regra: frente de um ativo
fica sob o ativo; frente que atravessa ativos fica no cliente. Título e
competência, com a grafia aparecendo. O **tipo se escolhe num cartão**:
cada cartão mostra a descrição, quando usar, e a lista das subpastas que
vão nascer. Escolha olhando as pastas, não de memória.

**Ramo.** Os ramos da casa em botões; clique nos que vai abrir. Um campo
para ramo fora da lista — só se for ramo novo mesmo; a auditoria vai
apontar como nota para conferência. Nome antigo (`RC Geral`, `Comercial`,
`RO`) é recusado, e a folha diz o nome novo. Cada ramo nasce com
`VIGENTE`, `HISTORICO`, `SINISTROS`. Ramo se abre quando há apólice, não
por precaução.

**Auditar.** Vai para a aba Auditoria já com esse cliente escolhido.

**+ Novo cliente.** Para quem chega com mandato assinado e nunca passou
pelo funil. Precisa marcar *O mandato está assinado* — sem isso o plano
não sai. Se a originação passou pelo funil, não é aqui: é **Promover**, no
Funil, que leva a originação junto.

## 5. Auditoria — conferir sem mexer

Escolha o funil ou um cliente e clique em **Conferir**. O programa lê a
árvore inteira (num cliente grande, alguns segundos) e compara com o
modelo. **Só lê.** Nada muda, nunca.

O resultado vem por gravidade e, dentro dela, por família — *Subpasta
faltando*, *Arquivos soltos*, *Originação parada*… — com a contagem. Cada
achado traz o caminho, o que foi visto e uma sugestão.

| Gravidade | Significa | O que fazer |
|---|---|---|
| **Erro** | foge do modelo | consertar no Drive, à mão, seguindo a sugestão |
| **Aviso** | merece um olhar | decidir: é legado, é engano, ou é o modelo que não cobre o caso |
| **Nota** | informação | nada; fica fechada por padrão |

Árvore no modelo: uma caixa verde, *Nenhum erro nem aviso*.

**Alinhar.** Um achado *Frente fora de qualquer tipo* traz o botão
**Alinhar**. Ele abre a frente com a forma mais parecida já escolhida num
cartão (troque só se a frente for de outro tipo), e o plano mostra o que vai
renomear (`06-DECISAO-EMISSAO` → `06-DECISAO-E-EMISSAO`) e o que vai criar
(`07-COMUNICACOES`). Nada é apagado nem movido: pasta renomeada fica com
tudo que tem dentro, e pasta que não tem par no modelo fica como está, com
aviso. Depois de Confirmar, rode a auditoria de novo.

Uma coisa esperada, que não é defeito: a originação do GRUPO-DIAMANTE
aparece *no modelo anterior*, de quatro subpastas. É nota, e a
reconciliação é à mão, quando for conveniente.

## 6. Sistema — o programa

Mostra onde o programa está olhando (Drive, clientes, funil), a pasta, o
Python, e se **este servidor** é o programa de fundo ou um aberto pelo
atalho.

**Subir com o Mac.** Já está feito neste Mac (16/09/2026). Mostra
*Instalado e rodando (processo N)*. Se mostrar *Instalado, mas não está
rodando*, veja o log (o caminho está na ficha) e clique em **Regravar**.

**Regravar.** Descarrega e carrega o programa de fundo de novo. É o que se
faz **depois de trocar arquivos do programa**: o código novo só entra em
vigor assim. Se a página estiver sendo servida pelo próprio programa de
fundo, ela para de responder por alguns segundos e volta.

**Deixar de subir com o Mac.** Remove o agente. O programa e as pastas
continuam como estão; a tela passa a abrir só pelo `VBR Pastas.command`.

## 7. Quando dá errado

Os erros aparecem na própria folha, em uma frase. O detalhe técnico vai
para `servidor.log`, na pasta do programa.

| O que aparece | O que é | O que fazer |
|---|---|---|
| *Não consegui falar com o programa* | o programa de fundo não está no ar | `VBR Pastas.command`; depois, Sistema → Regravar |
| *A autorização do Google venceu* | o Google não renova mais a autorização (com o app em modo Teste, isso acontece a cada sete dias) | clique em Tentar de novo: o navegador pede autorização; para parar de vencer, publique o app no Google Cloud (Tela de consentimento OAuth → Publicar) |
| *O Google recusou o acesso* | a conta negou, ou a credencial do app foi revogada | confira a conta no navegador; em último caso, apague `token.json` e autorize de novo |
| *Não achei "…" no Drive. Cheguei até "…"* | a pasta de clientes ou do funil mudou de nome ou de lugar | a frase diz em que degrau quebrou e o que existe ali; corrija o caminho com `python3 vbr_pastas.py config`, no Terminal, e Regravar |
| *Já existe uma originação com esse nome* | ela está no funil ou em ZZ-ENCERRADAS | se estiver encerrada, Reabrir em vez de criar |
| *Sem motivo, não encerro* | Encerrar sem o motivo | escreva o motivo |
| *… está em ZZ-ENCERRADAS. Reabra primeiro* | tentou promover uma encerrada | Reabrir, depois Promover |
| *Este plano não está mais valendo* / *O plano envelheceu* | a folha ficou aberta tempo demais, ou já foi usada | peça o plano de novo |
| *Sem conexão com o Drive* | internet | espere e tente de novo |
| *O Drive pediu para ir mais devagar* | muitas chamadas seguidas | espere um minuto |
| *Algo deu errado do lado do programa* | defeito | abra `servidor.log` e mande o trecho para quem cuida do programa |
| *pedido recusado: veio de outro site* | outra aba do navegador tentou usar o programa | ignore; feche abas que não sejam a do VBR Pastas |

Duas coisas que nenhum programa resolve: **arquivo cujo dono é outra
conta não se move** (o dono precisa transferir a propriedade); e **pasta
criada à mão fora da grafia da casa** não é encontrada — a auditoria é o
que revela.

## 8. Cuidados

- `credentials.json` e `token.json`, na pasta do programa, dão acesso ao
  Drive inteiro da conta. Não copie, não compartilhe, não ponha em pasta
  sincronizada.
- A pasta `vbr_pastas` fica em `/Users/fabiomedeiros/vbr_pastas`. Não a
  mova: o programa de fundo sabe onde ela está. Se precisar mover, Deixar
  de subir com o Mac antes, mover, e Subir com o Mac de novo.
- O `servidor.log` só cresce, devagar (uma linha por subida, mais os
  erros). Pode ser apagado a qualquer momento; o programa cria outro.
- Não crie pasta nova à mão para resolver um caso que o modelo não cobre.
  Ponha o documento no lugar menos errado e registre a dúvida (`MANUAL.md`,
  parte 5).

## 9. Atualizar o programa

1. Substitua os arquivos na pasta `vbr_pastas` (nunca `credentials.json`,
   `token.json` nem `config.json`).
2. Na tela, aba Sistema, **Regravar**.
3. Confira: a aba Sistema deve mostrar *Instalado e rodando*.

Quem quiser conferir antes de regravar, no Terminal, dentro da pasta:
`python3 teste_servidor.py` — roda o ciclo inteiro contra um Drive de
mentira, sem tocar no seu.

---

## Ficha rápida

| Quero | Onde | Lembre |
|---|---|---|
| abrir a tela | `Abrir VBR Pastas.webloc` | ou `http://127.0.0.1:8765` |
| registrar um prospecto | Funil → + Nova originação | competência é quando a conversa começou |
| o contrato assinou | Funil → Promover | leva a originação junto; ativos e frentes entram no plano |
| o prospecto disse não | Funil → Encerrar | motivo obrigatório; nada é apagado |
| o prospecto voltou | Funil → Reabrir | o bilhete fica |
| o cliente ganhou um ativo | Clientes → + Ativo, na linha do cliente | não mexe no que já existe |
| abrir um trabalho | Clientes → Frente | escolha o tipo pelo cartão |
| chegou uma apólice de ramo novo | Clientes → Ramo | a apólice mora em VIGENTE |
| cliente que nunca passou pelo funil | Clientes → + Novo cliente | marcar "mandato assinado" |
| conferir se está tudo no lugar | Auditoria → Conferir | só lê |
| frente com pasta de nome antigo | Auditoria → Alinhar, no achado | renomeia e cria; nada é apagado |
| troquei arquivos do programa | Sistema → Regravar | — |
| a tela não abre | `VBR Pastas.command` | depois, Sistema → Regravar |
