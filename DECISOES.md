# Decisões — vbr-pastas

Registro do que foi decidido, por quê, e o que ficou aberto. Quem for mexer
neste programa lê isto antes.

A regra da casa é que o modelo muda **por decisão registrada**, não por
acúmulo de exceções. Este arquivo é o registro. Entrada nova vai no fim da
seção da data, com o motivo junto — decisão sem motivo não se defende seis
meses depois.

---

## 16/09/2026 — o funil de originação

### 1. O funil é uma raiz própria, irmã de CLIENTES

```
GESTÃO DE RISCOS/           (no Drive: GESTAO DE RISCOS, ver decisão 9)
├── CLIENTES/      só quem tem mandato assinado
└── ORIGINACAO/    o funil
```

**Motivo: aritmético.** No AVRA há onze projetos em `origination` contra um
`active`. Com uma raiz só, onze de doze pastas de cliente não seriam de
cliente, e a palavra CLIENTES pararia de significar alguma coisa — para quem
olha, para quem dá permissão e para qualquer contagem.

Separar não é organização. É manter a pasta dizendo a verdade sobre o que
tem dentro.

### 2. Promover move, não copia

Quando o contrato assina, a pasta da originação **sai** do funil, **entra**
na pasta do cliente e é **renomeada** para `00-ORIGINACAO`.

**Motivo:** mover preserva id, compartilhamentos e histórico. Copiar deixaria
duas versões da mesma originação convivendo — o defeito que a migração de
setembro passou três dias desfazendo.

É também o que faz "a originação não se mexe" deixar de ser promessa e virar
operação.

### 3. A originação tem seis subpastas, não quatro

```
01-CADASTRO-DO-CLIENTE (+ LOGOS)
02-INSUMOS-RECEBIDOS
03-TRABALHOS
04-PROPOSTAS
05-CONTRATOS-E-ADENDOS
06-COMUNICACOES
```

**Motivo:** a forma anterior — cadastro, propostas, contratos, comunicações —
descrevia bem o **resultado** de uma originação e mal o **trabalho** dela. O
material que o prospecto manda (apólices vigentes, sinistralidade, cadastro
de bens) e a análise que sustenta a proposta caíam os dois em `02-PROPOSTAS`,
junto da proposta.

As seis põem o eixo da casa também aqui: **insumo, trabalho, entrega**. É o
mesmo começo de toda frente, e pelo mesmo motivo — a proposta é a entrega da
originação. Não faz dela uma frente: frente é trabalho **sob** mandato.

**A forma de quatro não é erro, é o modelo anterior.** A auditoria a
reconhece e sugere a renumeração como NOTA. GRUPO-DIAMANTE ainda está assim e
não há pressa.

### 4. Nome datado no funil: `AAAA-MM_NOME`

A competência é quando **a conversa começou**.

**Motivo:** com a data no nome, a lista ordena por idade sozinha, e uma
originação parada há dezoito meses se denuncia sem ninguém perguntar.

### 5. Encerrar exige motivo, e nunca apaga

Originação que não fecha vai para `ZZ-ENCERRADAS`, com data e motivo em dois
lugares: o arquivo `_ENCERRAMENTO.txt` dentro da pasta, e uma propriedade
invisível que o comando `funil` lê. `reabrir` traz de volta, e o bilhete
fica.

**Motivo:** prospecto volta. Saber quem disse não, quando e por quê é metade
do trabalho da próxima vez que o nome aparecer. O motivo é obrigatório porque
é a única coisa que dá valor ao registro dois anos depois.

### 6. A etiqueta da originação segue o nome, não o caminho

```
vbr/ORIGINACAO/CVCP
```

Sem a data, sem o lugar. Vale da criação até muito depois de promovida.

**Motivo:** uma originação ganha e perde o prefixo de data, e muda de lugar
duas ou três vezes na vida — funil, encerradas, funil de novo, dentro do
cliente. É sempre a mesma coisa. Etiqueta ancorada no caminho se invalidaria
a cada mudança dessas, e o programa criaria uma segunda pasta ao lado.

As demais pastas continuam etiquetadas pelo caminho
(`vbr/GRUPO-DIAMANTE/PECEM-I/ACERVO`), com a âncora fixa `vbr` — se fosse o
caminho da raiz, renomear a raiz invalidaria tudo, e isso já aconteceu uma
vez quando `NOVA_CLIENTES` virou `CLIENTES`.

### 7. A raiz do funil é deduzida, não perguntada

Por padrão, a pasta irmã de CLIENTES chamada ORIGINACAO. Configurável por
`--originacao`, `VBR_ORIGINACAO` ou `config.json`.

**Motivo:** uma pergunta a menos na primeira execução, e a resposta certa em
99% dos casos.

### 8. Paciência do funil: doze meses

Acima disso, a originação sai marcada na listagem e vira AVISO na auditoria.
Ajustável com `--paciencia`.

**Motivo:** originação parada não é erro de pasta. É uma decisão que ninguém
tomou.

### 9. A pasta raiz no Drive perdeu o acento

`GESTÃO DE RISCOS` → `GESTAO DE RISCOS`.

**Motivo:** o mesmo `Ã` pode ser gravado de dois jeitos em Unicode — um
caractere só (NFC) ou `A` mais um til combinante (NFD). São idênticos na tela
e diferentes para a busca do Drive. O macOS grava NFD; a pasta tinha sido
criada no Finder. O programa dizia "não achei GESTÃO DE RISCOS" e listava
`GESTÃO DE RISCOS` na linha seguinte.

Tirar o acento elimina a classe inteira do problema, e alinha a raiz com a
grafia da casa — hífen, maiúscula, sem acento — que ela mesma violava.

### 10. `achar_pasta` compara normalizado quando o exato falha

Primeiro tenta o nome exato, que é uma chamada só. Se não achar, lista os
filhos e compara pelo nome reduzido: acento em forma única (NFC), espaço das
pontas fora, maiúscula e minúscula indiferentes.

**Motivo:** a decisão 9 resolve a pasta de hoje; esta resolve a próxima que
alguém criar com acento pelo Finder. Cobre de quebra dois primos do mesmo
problema — espaço no fim do nome e caixa trocada.

**Não remove acento.** `GESTAO` e `GESTÃO` continuam sendo palavras
diferentes, e devem continuar.

### 11. Quatro regras novas na auditoria

- **acento em forma decomposta** no nome → AVISO, mostrando o nome com os
  caracteres à mostra (decisão 9)
- **pasta em CLIENTES que só tem originação** → ERRO, um diagnóstico só em
  vez dos três achados soltos que sairiam daí (sem APOLICES, sem FRENTES, sem
  ativo)
- **originação no modelo anterior** → NOTA com a lista do que renomear
  (decisão 3)
- **originação aberta há tempo demais** → AVISO, só em `--funil` (decisão 8)

E uma correção: `_ENCERRAMENTO.txt` deixou de ser acusado como arquivo solto.
Uma regra que acusa a saída do próprio programa é defeito da regra.

### 12. O front-end será um servidor local em Python

Não PHP no MAMP, não página pura no navegador.

**Motivo:** o navegador sozinho não lê `credentials.json` nem fala com o
Drive como o usuário — é a caixa de areia dele, e é proteção, não limitação.
A alternativa real seria reescrever tudo em JavaScript ou em PHP, e aí o
modelo passaria a existir em duas linguagens. O modelo inteiro vive num
arquivo só justamente para isso não acontecer.

**Correção de rumo registrada:** o MAMP Pro **executa** Python, ao contrário
do que foi dito primeiro nesta conversa. Fica como opção futura para o
programa ficar sempre no ar sem janela de Terminal. Não agora: o Python do
MAMP é outro Python, sem as bibliotecas instaladas, e a autorização do Google
não funciona bem servida pelo Apache.

### 13. Ordem de entrega do front-end

1. O funil (ver, originar, encerrar, reabrir, promover) e a leitura de árvore
   mais rápida
2. Abrir frente, abrir ramo, criar cliente e a auditoria na tela
3. O programa ligando sozinho com o Mac, sem janela de Terminal

---

## A primeira auditoria contra o Drive de verdade — 16/09/2026

`GRUPO-DIAMANTE`: **0 erros**, 10 avisos, 3 notas.

Zero erro quer dizer, concretamente: nenhum espaço no fim de nome, nenhum
compartimento faltando em acervo nenhum, nenhuma originação dentro de ativo,
nenhum ramo com nome antigo, nenhum arquivo solto na raiz do cliente. A
migração de setembro ficou de pé.

**Seis dos dez avisos são a mesma coisa:** as frentes foram criadas na
migração de 14/09 e o caderno v4 travou as cinco formas depois. As pastas
ficaram atrás do modelo.

| Divergência | Frentes |
|---|---|
| `06-DECISAO-EMISSAO` em vez de `06-DECISAO-E-EMISSAO` | UNIFICACAO-D-O, RENOVACAO-RO, RENOVACAO-TRANSPORTES |
| `05-ANALISE` em vez de `05-ANALISE-COMPARATIVA` | RFP-CORRETORA |
| falta `COMUNICACOES` | todas as seis |

O `COMUNICACOES` faltando em todas confirma o registro do caderno: a v3 não
previa a pasta, a prática já usava, e a v4 formalizou.

**As três notas estão certas e não pedem nada.** A originação no modelo de
quatro é a tolerância desenhada na decisão 3. E as duas frentes classificadas
como ANALISE — Cessão Banco e Garantia BID — são as mesmas que foram
apontadas como divergência duas vezes durante a migração e não eram.

---

## Aberto

**Da auditoria de 16/09 — quatro decisões, não conserto de pasta:**

- `CTJL/ACERVO/ROADSHOW` — acervo é o que descreve o ativo de forma
  permanente. Material de roadshow descreve uma operação, não a usina. Pelo
  modelo é originação ou frente.
- dez arquivos soltos na raiz da frente Cessão Banco
- uma apólice na raiz de `PECEM-II/APOLICES` — provavelmente falta criar o
  ramo
- `Estratégia de Pecem II seguros.docx` duplicado em
  `GROWTH-CREDIT/02-TRABALHOS` — conferir as datas antes de apagar qualquer um

**Do programa:**

- ~~as seis frentes atrás do modelo v4~~ — alinhadas em 16/09, à noite, pelo
  `alinhar` (decisão 34), a pedido do sócio: quatro renomes e seis
  `COMUNICACOES` criadas. A auditoria do GRUPO-DIAMANTE passou de 10 avisos
  para 4 — os quatro que são decisão, não conserto
- a leitura de árvore faz uma chamada ao Drive por pasta: 440 chamadas na
  Diamante, minutos de espera. Entra na etapa 1 do front-end.

**De antes:**

- minuta de contrato do Tony Harvey — precisa de transferência de propriedade
- as duas versões divergentes de `dados operacionais CTJL` — lembrete em
  13/11/2026
- `entity_type` NULL nas dez frentes do AVRA
- dessincronia entre AVRA e Drive
- purga da `ZZ_ANTIGA_NAO_USAR` em 13/11/2026

---

## 16/09/2026 — a tela, etapa 1

### 14. A página é um arquivo ao lado do servidor, não uma string dentro dele

`servidor.py` serve `pagina.html`. HTML, CSS e JavaScript estão no mesmo
arquivo, sem nada de fora — mas esse arquivo é separado do Python.

**Motivo:** quem tem olho para desenho mexe no `.html` sem passar por dentro
de um programa. E o servidor fica magro: ele traduz, não desenha.

### 15. Toda escrita passa por um plano com senha de uso único

A página pede o plano; o servidor guarda o plano e devolve uma senha. Para
executar, a página manda só a senha — e o que se executa é o plano guardado,
não o que a página mandar depois. A senha vale uma vez e envelhece em trinta
minutos.

**Motivo:** a regra "nada muda sem o plano aparecer e o usuário confirmar" não
pode depender da página se comportar. Morando no servidor, ela vale também
para uma página com defeito, ou para uma aba antiga que ficou aberta com um
plano de ontem.

### 16. Só a própria página escreve

Escrita (POST) com `Origin` de outro endereço é recusada, e o pedido tem de
vir como JSON.

**Motivo:** qualquer site aberto em outra aba alcança `127.0.0.1`. Sem isto,
um site mal-intencionado poderia pedir um plano e executá-lo em nome de quem
está logado.

### 17. Enter nunca escreve

No formulário, Enter pede o plano — que não toca o Drive. Na tela do plano,
Enter não faz nada, e o foco nasce em Cancelar. Confirmar é sempre um clique
num botão que nunca é o botão azul.

**Motivo:** o padrão é "não". Um Enter distraído tem de ser inofensivo.

### 18. A demonstração (`--falso`) tem caminhos fixos e não lê o config.json

Com `--falso`, a raiz é `GESTAO DE RISCOS/CLIENTES` e o funil
`GESTAO DE RISCOS/ORIGINACAO`, escritos no `servidor.py`. O Drive falso vem
povoado por `drive_falso.com_exemplo()`, que monta o exemplo a partir do
`modelo.py`.

**Motivo:** a demonstração não pode depender do que está gravado nem mexer
nele. E o exemplo segue o modelo por construção: se o modelo mudar, a
demonstração muda junto.

### 19. A leitura de árvore é por nível, 25 pais por consulta

`drive.ler_arvore` mantém assinatura e formato de saída — chave por chave e
na mesma ordem — mas por baixo chama `listar_filhos_de_varios`, que junta os
pais de um nível numa consulta só (`'a' in parents or 'b' in parents …`),
em lotes de 25. A deduplicação por id é por lote, não por chamada inteira,
porque um arquivo com dois pais em lotes diferentes tem de aparecer sob os
dois.

**Motivo:** 217 chamadas viraram 11 numa árvore de 216 pastas
(`teste_arvore.py`), com resultado idêntico ao da leitura pasta a pasta. O
Drive falso aprendeu a responder a consultas com vários pais e a devolver
`parents`, que é o que a leitura por nível precisa para saber de quem é cada
filho.

### 20. Erro é frase na página, traceback no terminal

`frase_de_erro` traduz: acesso recusado pelo Google, pasta não encontrada,
excesso de chamadas, sem conexão, e um genérico que manda olhar o terminal.
O traceback inteiro vai para o terminal, sempre.

**Motivo:** quem usa a tela não vai ler um traceback, e o traceback é o que
quem conserta precisa. Cada um no seu lugar.

### 21. O atalho escolhe o Python

`VBR Pastas.command` procura um Python 3.10 ou mais novo que tenha as
bibliotecas do Google; na falta, um 3.10+ qualquer, que serve para a
demonstração.

**Motivo:** o `/usr/bin/python3` do macOS é 3.9, e o `modelo.py` usa
`list[str] | None` — não abre nele. E o `pip install` foi feito num Python
só; o atalho tem de achar esse.

### 22. Abrir duas vezes não é erro

Se a porta já estiver ocupada pelo próprio VBR Pastas, o segundo clique só
abre o navegador no endereço. Se estiver ocupada por outro programa, diz
qual porta tentar.

**Motivo:** duplo clique repetido é o uso normal, não um engano a corrigir.

### Observação — decisão 10 e `_chave` não estão no drive.py

A decisão 10 (comparar normalizado quando o exato falha) e o `drive._chave`
citado nas armadilhas não existem no `drive.py` desta pasta: `achar_pasta`
procura só pelo nome exato. O arquivo é anterior ao registro. **Não foi
corrigido nesta etapa** — mexer em `achar_pasta` é mudança de comportamento
de todos os comandos, e pede decisão e teste próprios. Fica aqui para não se
perder.

### Aberto, para as etapas 2 e 3

- **Etapa 2:** abrir frente (destino escolhido numa lista lida do Drive;
  tipo em cartões com as subpastas), abrir ramo, criar cliente, auditoria
  agrupada por tipo. A API já devolve o modelo inteiro em `/api/modelo`, e
  `Tela` já tem os pedaços de leitura e execução que essas telas vão chamar.
- **Etapa 3:** o programa subindo com o Mac via `launchd`, sem janela.
- Configuração pela página: hoje, se o caminho gravado estiver errado, a tela
  explica onde quebrou e manda para o comando `config` do terminal.

---

## 16/09/2026 — a tela, etapa 2

### 23. O destino de frente e ramo é escolhido, nunca digitado

A aba Clientes lista cada cliente e cada ativo lidos do Drive naquele momento
(`/api/destinos`: uma listagem da raiz mais uma consulta por nível dos
filhos). Frente e ramo nascem de um botão nessa lista, e a folha só oferece o
que existe. Na execução, o caminho é resolvido de novo pelo nome — o id da
listagem não é guardado (armadilha 6).

**Motivo:** metade dos avisos da primeira auditoria real foi frente montada
à mão por quem não lembrava da forma ou errou o caminho.

### 24. O tipo de frente se escolhe num cartão que mostra as subpastas

Cinco cartões, um por tipo, com a descrição, o "usar quando" e a lista das
subpastas que vão nascer. Sem número, sem sigla de memória. Os cartões vêm de
`/api/modelo`; a página não conhece tipo nenhum de cor.

**Motivo:** quem escolhe vendo as pastas não escolhe errado. E um tipo novo
em `modelo.py` vira cartão sozinho.

### 25. Ramo com nome antigo é recusado no plano, não apontado depois

`RC Geral` não vira pasta: o plano recusa e diz que a casa chama de `RCG`.
Ramo fora da lista da casa entra, com aviso no plano e nota na auditoria.

**Motivo:** o terminal aceitava o nome antigo e a auditoria acusava como
ERRO em seguida — criar para depois mandar renomear é trabalho em dobro. O
`RAMOS_RENOMEADOS` do modelo já sabia a resposta; passou a ser usado antes.

### 26. Cliente novo exige a marca "o mandato está assinado"

A folha tem uma caixa a marcar; sem ela o plano não sai, e a frase manda
para o funil. A mesma folha lembra: se a originação passou pelo funil, é
Promover, não cliente novo.

**Motivo:** é a pergunta que o terminal fazia ("já tem mandato assinado?"),
na forma que uma página tem de fazer. O padrão continua "não".

### 27. A auditoria na tela agrupa por família

Cada achado é classificado por um trecho fixo da mensagem (`FAMILIAS`, no
`servidor.py`): "Subpasta faltando", "Arquivos soltos", "Originação parada",
e assim por diante. Dentro de cada gravidade, uma dobra por família com a
contagem; erros e avisos abertos, notas fechadas.

**Motivo:** a lista corrida do terminal serve para quem lê tudo; a tela
serve para decidir por onde começar. Mensagem que não casar com família
nenhuma vira família própria com o texto dela, e o `teste_servidor.py`
acusa quando isso acontece — é o aviso de que a auditoria ganhou uma regra
que a tela não conhece.

**Ressalva registrada:** as famílias moram no servidor, não em
`auditoria.py`. Pôr uma família em cada `rel.add` seria o lugar certo, mas
são trinta chamadas num arquivo que não é desta etapa. Fica para quando a
auditoria for mexida por outro motivo.

### 28. A auditoria roda sob demanda, não ao abrir a aba

A aba Auditoria abre com o seletor e o botão Conferir; a leitura do Drive só
começa no clique. O botão Auditar da aba Clientes já vai com o cliente
escolhido e dispara.

**Motivo:** mesmo por nível, um cliente grande leva alguns segundos; a aba
não pode travar só por ter sido aberta.

---

## 16/09/2026 — a tela, etapa 3

### 29. O programa de fundo é um agente do launchd, do usuário

`~/Library/LaunchAgents/com.vbrisk.pastas.plist`, com `RunAtLoad` e
`KeepAlive` só em saída com erro. Roda `servidor.py --fundo --porta 8765`
com o Python que estava servindo a página na hora da instalação, e com a
pasta do programa como diretório de trabalho — `credentials.json`,
`token.json` e `config.json` são lidos por caminho relativo. Saída e erro
vão para `servidor.log`, na pasta do programa.

**Motivo:** é o mecanismo do próprio macOS para programa de fundo por
conta de usuário: sem janela, sem Dock, sem senha de administrador, e sobe
de novo se cair. Nada é instalado além de um arquivo de texto.

### 30. `--fundo` espera a porta em vez de desistir

Se a porta estiver ocupada — em geral por um servidor aberto pelo atalho —
o programa de fundo escreve uma linha no log e tenta de novo a cada cinco
segundos. Quando o outro fecha, ele assume.

**Motivo:** o caso comum de instalação é este: a pessoa instala pela
página, servida por um servidor do atalho. Com `KeepAlive` sem condição, o
launchd reiniciaria o agente a cada dez segundos enquanto o atalho
estivesse aberto, enchendo o log; saindo com código 0, o launchd não o
traria de volta. Esperar dentro do processo resolve os dois. Conferido: o
agente de teste esperou o servidor manual fechar e assumiu em seis
segundos.

### 31. Instalar e remover passam pelo mesmo plano das outras escritas

A aba Sistema mostra o plano — o arquivo, o comando, a pasta, o log — e só
grava depois de Confirmar. Também existe pelo Terminal: `--instalar`,
`--desinstalar`, `--situacao`. O `launchctl` é chamado só com `bootstrap`,
`bootout` e `print`, no domínio `gui/<uid>`.

**Motivo:** gravar o que sobe com o Mac é escrita persistente, mesmo não
sendo no Drive. A regra 3 vale para ela também.

### 32. A tela se abre por um `.webloc`, não por outro programa

A instalação grava `Abrir VBR Pastas.webloc` na pasta do programa: um
arquivo de endereço que o Finder abre no navegador com duplo clique. Sem
Terminal. O `VBR Pastas.command` continua existindo para quando o agente
não estiver instalado; se o programa de fundo já estiver no ar, ele só abre
o navegador.

**Motivo:** um `.app` de verdade exigiria ferramenta de empacotamento ou
AppleScript compilado; um `.webloc` é um arquivo de texto e faz o mesmo.

### 33. Depois de atualizar o programa, Regravar

O agente carrega o código na hora em que sobe. Arquivos trocados na pasta
só entram em vigor com Regravar (na aba Sistema) ou com `--instalar` de
novo, que descarrega e carrega. Não há reinício automático nem por botão
separado: reiniciar o próprio servidor que está servindo a página deixaria
a resposta pela metade.

**Motivo:** um passo explícito e nomeado é mais fácil de lembrar do que um
reinício que acontece sozinho e ninguém viu.

### Conferido

- `teste_lancador.py`: o conteúdo do agente e do atalho, instalar, regravar,
  recusa do launchd, desinstalar — contra um `launchctl` de mentira.
- `teste_servidor.py`, seção 15: o mesmo ciclo pela página.
- **Uma prova real, temporária**: um agente com o rótulo
  `com.vbrisk.pastas.teste`, na porta 8799 e em modo de demonstração, foi
  carregado no launchd desta conta, esperou um servidor manual fechar,
  assumiu a porta, e foi descarregado e apagado em seguida. **O agente de
  verdade não foi instalado**: isso é decisão de quem usa, na aba Sistema.

### Instalado de verdade — 16/09/2026, 19:38

A pedido do sócio, o agente `com.vbrisk.pastas` foi instalado nesta conta
pela rotina do próprio programa (`servidor.py --instalar`), com o Python
3.14 do framework e a pasta `/Users/fabiomedeiros/vbr_pastas`. Subiu na
hora, contra o Drive de verdade, nos caminhos do `config.json`
(`GESTAO DE RISCOS/CLIENTES` e `GESTAO DE RISCOS/ORIGINACAO`). O
`MANUAL_DE_OPERACAO.md` descreve a operação a partir daqui.

### A primeira auditoria do funil pela tela — 16/09/2026, à noite

**21 erros, 14 avisos, 0 notas — e é uma situação só, três vezes.** As três
pastas do funil (`CVCP`, `GRUPO-MERCURIO-PARTNERS`, `GRUPO-STARBOARD`) não
são originações na forma do modelo: são os esqueletos de cliente da etapa 1
de 13/09 (`00-ORIGINACAO`, `APOLICES`, `FRENTES` e os ativos `UISA`,
`UTE-PILAR`, `UTE-BIRIBEIRA`, `PAMPA-SUL`), levados inteiros para
`ORIGINACAO` quando o funil foi separado. Por isso a auditoria cobra as seis
subpastas em cada uma (18 erros), acusa o nome sem competência (3 erros) e
lista o esqueleto como subpasta fora do modelo (13 avisos). Mais uma
duplicata: `Mapa_Corporativo_Seguros_Success_Fee_Cronograma_Mercurio_Versao_Corrigida.docx`,
duas vezes em `GRUPO-MERCURIO-PARTNERS/00-ORIGINACAO/02-PROPOSTAS`.

**O que o modelo diz que deveria ser:** `ORIGINACAO/AAAA-MM_NOME/` com o
conteúdo do `00-ORIGINACAO` de cada uma, e nada mais — prospecto não tem
ativo, acervo, apólice nem frente. Fica em aberto, como decisão, porque
envolve renomear três pastas, mover o conteúdo um nível acima e decidir o
que fazer com os esqueletos vazios (ou não vazios: conferir os ativos antes).
Nada foi mexido.

### 34. O comando `alinhar` — 16/09/2026, noite

Decidido fazer, e feito. Uma frente atrás do modelo ganha a forma certa em
duas operações e nada mais: **renomear** as subpastas que têm par no modelo
e **criar** as que faltam. O par é decidido pelo número — `06-DECISAO-EMISSAO`
casa com a esperada que começa por `06-` — e só se a esperada ainda não
existir. Pasta sem par fica como está, e o plano avisa. Nunca apaga, nunca
move arquivo, não mexe no nome da frente.

Mora em `alinhar.py` (só a lógica, sem Drive), aparece na tela como botão
**Alinhar** em cada achado "frente fora de qualquer tipo" da auditoria, com
a forma mais parecida já escolhida num cartão, e no terminal como
`vbr_pastas.py alinhar CAMINHO [--tipo]`. Pasta renomeada ganha a etiqueta
pelo caminho novo, como se tivesse sido criada pelo programa.

**Motivo:** as seis frentes do GRUPO-DIAMANTE são a maior parte dos avisos
da auditoria, e o conserto é sempre o mesmo. Fazer à mão são dezoito
operações no Finder, com a grafia a decorar; pelo programa é um clique por
frente, com o plano na frente.

**O que fica de fora, de propósito:** decidir o que fazer com pasta sem par
(é conteúdo, e conteúdo é de gente), e o nome da frente (precisa da
competência, que só os sócios sabem).

### 35. Regravar espera o launchd derrubar o serviço antigo

Descoberto ao regravar o agente de verdade pela primeira vez: `bootout`
devolve na hora, mas o launchd ainda leva um instante para derrubar o
serviço, e um `bootstrap` nesse instante falha com "Bootstrap failed: 5:
Input/output error". O agente ficava gravado e parado — e a tela, fora do
ar. Agora o lançador espera o rótulo sumir do `launchctl print` (até vinte
segundos) e tenta o `bootstrap` até cinco vezes. O `launchctl` de mentira do
teste passou a demorar para derrubar, como o de verdade.

**Motivo:** Regravar é o passo que toda atualização do programa pede; não
pode ser o passo que derruba o programa.

### 36. A demonstração tem porta própria: 8766

`python3 servidor.py --falso` sobe na 8766; a tela de verdade fica na 8765
com o programa de fundo. Se alguém pedir um modo na porta do outro, o
servidor recusa e diz a porta certa — nunca abre a tela de verdade achando
que é a de mentira, nem o contrário.

**Motivo:** com o agente instalado, a 8765 está sempre ocupada. Na mesma
porta, `--falso` dizia "já está no ar" e abria o navegador no Drive de
verdade, com a faixa de demonstração ausente. Um clique distraído ali seria
uma escrita real. O `--porta` continua valendo para os dois.

### 37. Ativo novo em cliente que já existe — 18/09/2026

Faltava: ativo só nascia no Promover e no cliente novo, e um mandato que
ganha uma usina não tinha por onde entrar. Agora a aba Clientes tem
**+ Ativo** na linha de cada cliente, e o terminal tem `vbr_pastas.py ativo`.
Cria a árvore do ativo — ACERVO com os cinco compartimentos, APOLICES,
FRENTES — e, se pedido, ramos e frentes já de saída. A árvore é pedida ao
`modelo.py` (a parte do ativo de `arvore_de_promocao`), não escrita à parte.

Recusa ativo que já existe, ativo dentro de ativo, nome de pasta do modelo
e ramo com nome antigo. Não toca em nada do que o cliente já tem; o teste
confere que a originação de quatro do GRUPO-DIAMANTE sai intacta.

**Motivo, e o atalho que não serve:** dava para usar "+ Novo cliente" com o
nome de um cliente existente, porque criar é idempotente. Mas o plano de
cliente novo inclui a originação na forma de seis, e num cliente com a de
quatro isso criaria cinco subpastas ao lado das antigas. Uma ação própria,
que só sabe criar ativo, não tem como errar assim.

Percebido pelo sócio no uso, dois dias depois da entrega.

### 38. Token vencido: o programa reautoriza sozinho — 31/10/2026

Três vezes em seis semanas (28/09, 19/10, 31/10) a tela parou com "algo deu
errado do lado do programa", e o log dizia `invalid_grant`: o Google não
renovava mais a autorização. A causa é o app no Google Cloud estar em modo
**Teste**, em que toda autorização vence em sete dias. O conserto de
verdade é publicar o app (Tela de consentimento OAuth → Publicar), e isso é
uma ação no console do Google, não no programa.

Do lado do programa, duas mudanças. `drive.conectar` trata `RefreshError`
como "comece de novo": abre o navegador para autorizar e grava o token novo
por cima do vencido — em vez de parar com traceback e mandar apagar
`token.json` à mão. E `frase_de_erro` reconhece o caso e diz na tela que a
autorização venceu e como parar de vencer.

**Motivo:** o passo "apague o token.json" é exatamente o tipo de coisa que
o sócio não devia ter de fazer; o programa sabe que o token não serve e
sabe o que fazer com isso.

**Observação sobre o agente:** o navegador da autorização é aberto pelo
processo do launchd; funciona porque o agente roda no domínio gráfico da
conta (`gui/<uid>`). Se um dia não abrir, o caminho é
`python3 vbr_pastas.py funil` na pasta, que faz a mesma autorização.

### 39. O programa de fundo abre o navegador da autorização com `open` — 31/10/2026

Na reautorização de hoje, o agente do launchd escreveu o endereço do Google
no log e ficou esperando: o navegador não abriu, e a tela ficou parada sem
dizer nada. O agente passa a rodar com `BROWSER=open`, que faz a biblioteca
do Google abrir o endereço pelo `open` do macOS, que funciona a partir do
launchd. Conferido só pelo teste do `.plist`: o caso real aparece na próxima
vez que a autorização vencer — e, com o app publicado hoje, isso não deve
mais acontecer por prazo.

### 40. O programa passa a ter repositório no GitHub — 02/11/2026

Até hoje a pasta `~/vbr_pastas` não tinha história: um arquivo apagado ou
reescrito por engano estava perdido. A pasta vira um repositório git, com
cópia privada em `github.com/vbrisks-hue/vbr-pastas`, ao lado do AVRA-SYSTEM.

Ficam **fora** do repositório, pelo `.gitignore`: `credentials.json`,
`token.json` e `config.json` (regra inviolável 2 — não entram em nada),
`servidor.log` (traz endereços de autorização do Google e nomes de pastas
reais de clientes), `__pycache__`, `.DS_Store`. Quem clonar em outro Mac
precisa das próprias credenciais do Google Cloud e responde a pergunta do
caminho na primeira execução, como o README já descreve.

O repositório é a cópia; a pasta que roda continua sendo `~/vbr_pastas`, e o
agente do launchd não sabe que ela virou repositório. Nada muda na operação.

### Aberto

- ~~No Google Cloud, publicar o app~~ — **feito em 31/10/2026** pelo sócio
  (Branding preenchido com o site vbrisk.com.br; status Em produção). A
  autorização gravada em seguida não tem mais o vencimento de sete dias. (sair do modo Teste). Enquanto não
  for feito, a autorização vence a cada sete dias e a tela pede para
  autorizar de novo.
- **Do funil (16/09):** Mercúrio e CVCP foram reconciliadas à mão pelo sócio
  na mesma noite, com a auditoria da tela guiando os nomes. Última auditoria
  do funil: **0 erros, 1 aviso** — a duplicata do mapa corporativo em
  `2026-08_GRUPO-MERCURIO-PARTNERS/04-PROPOSTAS`, para conferir as datas.
- **Starboard, deixada para depois por decisão do sócio (16/09):** a pasta
  `GRUPO-STARBOARD` está na **lixeira do Drive**, e dentro dela, em
  `00-ORIGINACAO/02-PROPOSTAS`, estão as quatro propostas de 10/06/2026
  (Pampa Sul V1 pdf e pptx, Pampa Sul pptx, GENERAL V1 pdf) — as únicas
  cópias fora da lixeira não existem; a `GRUPO STARBOARD` de
  `ZZ_ANTIGA_NAO_USAR` está vazia. **A lixeira guarda por trinta dias: até
  cerca de 16/10/2026.** Restaurar, montar a originação e, se não fechou,
  Encerrar pela tela com o motivo.
- Rotação do `servidor.log`: hoje só cresce. Uma linha por subida e os
  tracebacks; deve levar meses para incomodar.
- Configuração pela página segue de fora.
