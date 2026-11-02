# A tela — etapa 2 (16/09/2026)

A página ganhou duas abas — **Clientes** e **Auditoria** — e três folhas
novas: frente, ramo e cliente novo. Tudo pelo mesmo caminho da etapa 1:
plano com senha de uso único, Confirmar por clique, erro em frase.

## O que entrou

**Aba Clientes.** Cada cliente e cada ativo, lidos do Drive na hora. Em cada
linha: Frente, Ramo e, no cliente, Auditar. Em cima, + Novo cliente.

**Frente.** Onde mora vem de uma lista (`GRUPO-DIAMANTE`,
`GRUPO-DIAMANTE / CTJL`, …), já apontando para a linha de onde se clicou. O
tipo se escolhe em cartões que mostram as subpastas de cada um. Título e
competência com a grafia aparecendo enquanto se digita. O plano mostra a
árvore e avisa se `FRENTES` ainda não existe ali.

**Ramo.** Os ramos da casa em botões; um campo para ramo fora da lista, com
aviso. Nome antigo (`RC Geral`, `Comercial`, `RO`) é recusado no plano com o
nome novo. Cada ramo nasce com `VIGENTE`, `HISTORICO`, `SINISTROS`.

**Cliente novo.** Nome, a marca "o mandato está assinado" (sem ela o plano
não sai e a frase manda para o funil), ativos e frentes — o mesmo bloco da
promoção.

**Auditoria.** Seletor com o funil e cada cliente; Conferir lê a árvore
inteira e mostra os achados por gravidade e, dentro dela, por família
("Subpasta faltando", "Arquivos soltos", "Originação parada"…), cada uma
com a contagem e a sugestão de cada achado. Erros e avisos abertos, notas
fechadas. Árvore no modelo: uma caixa verde.

## O que mudou no que existia

- **`servidor.py`** — `destinos`, `plano_frente`, `plano_ramo`,
  `plano_cliente`, `auditoria`, e o parser de ativos e frentes compartilhado
  entre promoção e cliente novo. Rotas `/api/destinos`, `/api/auditoria`,
  `/api/frente/plano`, `/api/ramo/plano`, `/api/cliente/plano`.
- **`pagina.html`** — abas, as duas vistas e as três folhas; o bloco de
  ativos e frentes virou função para servir a promoção e o cliente novo.
- **`teste_servidor.py`** — seções 10 a 14.
- **`DECISOES.md`** — decisões 23 a 28.

`modelo.py`, `auditoria.py`, `drive.py`, `drive_falso.py`, `vbr_pastas.py` e
`teste_funil.py` não mudaram nesta etapa.

## Como foi conferido

- Os três testes passam. O `teste_servidor.py` ganhou 30 verificações:
  destinos na ordem certa, frente em ativo com etiqueta pelo caminho, tipo
  vazio e destino inexistente recusados, ramo antigo recusado com o nome novo,
  ramo repetido entra uma vez, cliente sem mandato mandado ao funil, cliente
  novo limpo na auditoria, auditoria com as famílias esperadas e nenhuma
  mensagem fora delas, funil com a originação parada.
- No navegador, com `--falso`: aba Clientes, folha de frente no CTJL com o
  cartão SINISTRO, plano com as sete pastas, confirmação; auditoria do
  GRUPO-DIAMANTE agrupada; folha de ramo.

## O que ficou de fora

- **Etapa 3** — o programa subindo com o Mac via `launchd`, sem janela.
- **`alinhar`**, as quatro decisões da auditoria, qualquer mudança no modelo.
- **Configuração pela página.**
- **Família dentro de `auditoria.py`** — ver a ressalva na decisão 27.
