# Manual da estrutura de pastas de clientes
### VB Risk — modelo, operação e ferramenta
*Versão 1.2 — 16 de setembro de 2026*

---

## Para que serve este manual

Descreve **como as pastas de cliente da VB Risk são organizadas**, por que são
assim, e como usar o programa `vbr-pastas` para criar e conferir essa estrutura.

Três leituras possíveis:

- **Quem só precisa arquivar um documento** lê as partes 1 e 2 e para.
- **Quem vai usar o programa** pode ir direto para a parte 3, que começa num
  passo a passo do zero até a primeira pasta criada.
- **Quem quer entender por que é assim** lê tudo. As partes 4 e 5 são o que
  impede o modelo de se desfazer por acúmulo de exceções.

**Se você tem trinta segundos:** são duas raízes no Drive. `CLIENTES` só tem
quem assinou mandato; `ORIGINACAO` é o funil de quem ainda não assinou. Quando
assina, a pasta da originação **muda de lugar** — do funil para dentro do
cliente — e a árvore cresce ao redor dela.

---

# Parte 1 — O modelo

## 1.1 As quatro espécies

Toda pasta da estrutura pertence a uma de quatro espécies. Saber a espécie
responde sozinha onde um documento deve morar.

| Espécie | Onde mora | O que guarda | Dura |
|---|---|---|---|
| **ORIGINAÇÃO** | no funil antes de assinar; no grupo depois | insumo, análise, proposta, contrato, comunicação — tudo que é **pré-mandato** | permanente, e muda de lugar quando assina |
| **FRENTE** | grupo ou ativo | um **trabalho** com começo, meio e fim, sob mandato e plano de trabalho | fecha quando entrega |
| **ACERVO** | ativo | o que **descreve o ativo**: laudo, planta, contrato, relatório de inspeção | permanente |
| **APÓLICES** | grupo e ativo | a **apólice em si**, por ramo | permanente |

## 1.2 As três regras que resolvem 90% das dúvidas

**Regra 1 — Originação não é frente, e não é cliente.**
Frente é trabalho executado sob mandato e plano de trabalho. Antes do contrato
não há mandato, logo não há frente — e também não há cliente. Enquanto não
assina, a originação mora no **funil**, numa pasta própria ao lado de
`CLIENTES`. Quando assina, ela **muda de lugar**: entra na pasta do cliente e
passa a se chamar `00-ORIGINACAO`, no nível do grupo. Nunca no ativo.

**Regra 2 — A frente mora no nível do seu escopo.**
Frente de um ativo fica sob o ativo. Frente que atravessa ativos fica sob o
cliente. Uma renovação de RO do Pecém I é do Pecém I; uma RFP que cobre CTJL,
Pecém I e Pecém II é do grupo.

**Regra 3 — O que tem número e vigência é acervo ou apólice, não frente.**
Apólice, endosso e certificado são identificáveis por número e por vigência:
vão para `APOLICES/[RAMO]`. O que não é identificável assim é processo, logo é
frente. **Uma apólice nunca vai para o ACERVO**, mesmo que tenha chegado dentro
de uma pasta de documentação técnica.

## 1.3 A árvore

São **duas raízes**, irmãs:

```
GESTÃO DE RISCOS/
├── CLIENTES/      ← só quem tem mandato assinado
└── ORIGINACAO/    ← o funil: quem ainda não assinou
```

O funil:

```
ORIGINACAO/
├── 2026-03_CVCP/                      ← uma originação aberta
│   ├── 01-CADASTRO-DO-CLIENTE/
│   │   └── LOGOS/
│   ├── 02-INSUMOS-RECEBIDOS/          ← apólices atuais, sinistralidade, cadastro
│   ├── 03-TRABALHOS/                  ← a análise que sustenta a proposta
│   ├── 04-PROPOSTAS/
│   ├── 05-CONTRATOS-E-ADENDOS/
│   └── 06-COMUNICACOES/
├── 2026-08_XPTO/
└── ZZ-ENCERRADAS/                     ← não fechou; fica com data e motivo
    └── 2025-11_FULANO/
        └── _ENCERRAMENTO.txt
```

O cliente:

```
CLIENTES/
└── GRUPO-DIAMANTE/                    ← o cliente
    ├── 00-ORIGINACAO/                 ← a MESMA pasta do funil, movida para cá
    │   ├── 01-CADASTRO-DO-CLIENTE/
    │   │   └── LOGOS/
    │   ├── 02-INSUMOS-RECEBIDOS/
    │   ├── 03-TRABALHOS/
    │   ├── 04-PROPOSTAS/
    │   ├── 05-CONTRATOS-E-ADENDOS/
    │   └── 06-COMUNICACOES/
    ├── APOLICES/                      ← apólice do grupo (nasce vazia)
    ├── FRENTES/                       ← frente que atravessa ativos
    │   ├── 2026-07_RFP-CORRETORA/
    │   └── 2026-07_CESSAO-BANCO/
    ├── CTJL/                          ← um ativo
    │   ├── ACERVO/
    │   │   ├── DOCUMENTACAO-TECNICA/
    │   │   ├── ENGENHARIA-E-INSPECOES/
    │   │   ├── CADASTRO-DE-VALORES/
    │   │   ├── CONTRATOS-DO-ATIVO/
    │   │   └── PLANTAS-E-IMAGENS/
    │   ├── APOLICES/
    │   │   └── RO-BI/
    │   │       ├── VIGENTE/
    │   │       ├── HISTORICO/
    │   │       └── SINISTROS/
    │   └── FRENTES/
    ├── PECEM-I/
    └── PECEM-II/
```

`APOLICES` **nasce vazia** nos dois níveis. Os ramos entram quando houver
apólice — não se criam ramos "por precaução".

## 1.4 Os cinco compartimentos do acervo

Travados. Revisão só se vier a ser necessária.

| Subpasta | O que vai |
|---|---|
| `DOCUMENTACAO-TECNICA` | manual, procedimento, resumo, compêndio, dado operacional |
| `ENGENHARIA-E-INSPECOES` | relatório específico de inspeção, *risk survey report*, teste de bomba |
| `CADASTRO-DE-VALORES` | laudo de avaliação, planilha de valores, cotação de máquina |
| `CONTRATOS-DO-ATIVO` | CCEAR, contrato de conexão, contrato de O&M |
| `PLANTAS-E-IMAGENS` | planta, unifilar, foto, termografia |

A fronteira que mais gera dúvida: **relatório específico de inspeção vai para
ENGENHARIA; resumo e compêndio vão para DOCUMENTACAO.**

## 1.5 Ramos de apólice

Cada ramo tem sempre três subpastas: `VIGENTE`, `HISTORICO`, `SINISTROS`.
**Sinistro não é ramo** — é a subpasta do ramo que sofreu o sinistro.

| Ramo | Cobre |
|---|---|
| `RO-BI` | riscos operacionais e lucros cessantes — a parte física da usina |
| `EMPRESARIAL` | o escritório. Existe porque a franquia do RO é de USD 5 milhões, o que deixaria um sinistro na sede sem indenização |
| `RCG` | RC Geral, SUSEP 51 |
| `D-O` | responsabilidade de administradores |
| `CYBER`, `AMBIENTAL`, `FROTA`, `TRANSPORTES` | — |
| `GARANTIA-JUDICIAL` | garantia ambiental, cível, trabalhista |
| `GARANTIA-BID` | bid bond de leilão |

A garantia ganha nível de modalidade porque judicial e bid bond não têm nada em
comum além do nome. **A corretora que colocou a garantia não vira pasta.**

## 1.6 Tipos de frente

Cada necessidade tem sua forma de árvore. É o que impede uma renovação de virar
uma pasta genérica com tudo dentro.

| Tipo | Quando usar | Subpastas |
|---|---|---|
| **RENOVACAO** | vencimento chegando, com cotação de mais de uma seguradora | 01-INSUMOS · 02-TRABALHOS · 03-ENTREGAS · 04-COTACOES-RECEBIDAS · 05-ANALISE-COMPARATIVA · 06-DECISAO-E-EMISSAO · 07-COMUNICACOES |
| **CONCORRENCIA** | RFP de corretora, concorrência de seguradora | 01-INSUMOS · 02-TRABALHOS · 03-ENTREGAS · 04-PROPOSTAS-RECEBIDAS · 05-ANALISE-COMPARATIVA · 06-DECISAO · 07-COMUNICACOES |
| **ANALISE** | estudo ou diagnóstico que termina numa decisão | 01-INSUMOS · 02-TRABALHOS · 03-ENTREGAS · 04-DECISOES · 05-COMUNICACOES |
| **VISITA-TECNICA** | visita de campo com relatório e recomendações | 01-INSUMOS · 02-TRABALHOS · 03-ENTREGAS · 04-REGISTRO-DE-CAMPO · 05-RECOMENDACOES · 06-COMUNICACOES |
| **SINISTRO** | sinistro relevante que exige condução própria | 01-INSUMOS · 02-TRABALHOS · 03-ENTREGAS · 04-REGULACAO · 05-ENCERRAMENTO · 06-COMUNICACOES |

**Toda frente termina em `COMUNICACOES`.** Entra só o que tem consequência —
define, aceita, altera ou recusa algo. Agenda e confirmação de reunião não
entram, senão a pasta vira arquivo morto de e-mail.

**Nome da frente: `AAAA-MM_TITULO`.** A competência é **quando a frente
começou**, não quando a pasta foi criada. `2026-05_RENOVACAO-GARANTIA-BID`
começou em maio, mesmo que a pasta tenha nascido em setembro.

## 1.7 O funil, e a travessia para cliente

**Prospecto não tem pasta em CLIENTES.** Tem pasta no funil, e só a
originação: sem ativo, sem acervo, sem apólice, sem frente. Frente é trabalho
sob mandato, e antes do contrato não há mandato.

**Por que o funil é uma raiz separada.** É aritmética. No AVRA há hoje onze
projetos em `origination` contra um `active`. Se cada originação virasse pasta
em `CLIENTES`, onze de doze pastas de cliente não seriam de cliente — e a
palavra `CLIENTES` pararia de significar alguma coisa, para quem olha, para
quem dá permissão e para qualquer contagem. Separar não é organização: é
manter a pasta dizendo a verdade sobre o que tem dentro.

**A originação tem nome datado**, `AAAA-MM_NOME`, com a competência de quando
a conversa começou. Com a data no nome, a lista ordena por idade sozinha, e
uma originação parada há dezoito meses se denuncia sem ninguém precisar
perguntar.

**Quem não fechou não some.** Vai para `ZZ-ENCERRADAS`, com data e motivo
gravados — num arquivo `_ENCERRAMENTO.txt` dentro da pasta, e numa propriedade
invisível que o comando `funil` lê. Não se apaga porque prospecto volta: saber
quem disse não, quando e por quê é metade do trabalho da próxima vez que o
nome aparecer. Se voltar, `reabrir` traz de volta ao funil e o bilhete fica.

**Quando o contrato assina, a originação muda de lugar.** Ela sai do funil,
entra na pasta do cliente e passa a se chamar `00-ORIGINACAO`. **Move, não
copia** — é a mesma pasta, com o mesmo id, os mesmos compartilhamentos e o
mesmo histórico. Copiar deixaria duas versões da mesma coisa convivendo, que
foi o defeito que a migração de setembro passou três dias desfazendo.

Só então a árvore cresce: entram as apólices e frentes do grupo, e cada ativo
com seu acervo. **A originação não se mexe por dentro** — ela é o registro do
que houve antes do contrato e permanece inteira.

**Mandato não vira pasta.** Olhando os tipos de trabalho que a casa faz, eles
se partem em dois: consultoria avulsa e diagnóstico pontual têm começo e fim,
logo já são frentes; mandato continuado não tem fim, logo é a própria relação
com o cliente, que já é a pasta do cliente. Nenhum dos dois pede nível novo.

### Por que a originação tem seis subpastas, e não quatro

A forma anterior tinha quatro: cadastro, propostas, contratos, comunicações.
Ela descrevia bem o **resultado** de uma originação, e mal o **trabalho** dela.
O material que o prospecto manda — apólices vigentes, sinistralidade, cadastro
de bens — e a análise que sustenta a proposta não tinham compartimento, e
caíam os dois dentro de `02-PROPOSTAS`, junto da proposta.

As seis põem o eixo da casa também aqui: **insumo, trabalho, entrega**. É o
mesmo começo de toda frente, e pelo mesmo motivo — a proposta é a entrega da
originação. Não faz dela uma frente: frente é trabalho **sob** mandato.

Originação que já existe na forma de quatro não está errada, está no modelo
anterior. A auditoria a reconhece e diz o que renomear, como nota, não como
erro. Não há pressa.

## 1.8 Grafia

**Hífen, maiúscula, sem acento.** Sempre.

```
Renovação Apólices  →  RENOVACAO-APOLICES
D&O                 →  D-O
RC Geral            →  RC-GERAL
```

Não é preciosismo. Acento e espaço quebram busca, script e sincronização — e
**espaço no fim do nome é invisível na tela**, o que esconde o problema até
alguém procurar a pasta e não achar.

---

# Parte 2 — Onde arquivar: o caminho rápido

Quatro perguntas, em ordem. A primeira que der "sim" resolve.

**1. É uma apólice, endosso ou certificado?**
→ `APOLICES/[RAMO]/VIGENTE`. Se venceu, `HISTORICO`.
Está no nível do ativo, salvo se a apólice cobrir o grupo inteiro.

**2. É anterior ao contrato com o cliente?**
→ A originação. Se o contrato **já assinou**, ela está em
`CLIENTES/[CLIENTE]/00-ORIGINACAO/`. Se **ainda não assinou**, está no funil,
em `ORIGINACAO/AAAA-MM_NOME/`. Nos dois casos, na subpasta numerada que
couber, e sempre no nível do grupo — nunca no ativo.

**3. Descreve o ativo de forma permanente?**
→ `[ATIVO]/ACERVO/`, num dos cinco compartimentos.

**4. É trabalho em curso, com começo e fim?**
→ `FRENTES/AAAA-MM_TITULO/`, na subpasta numerada do tipo.
No ativo se for de um ativo; no grupo se atravessar ativos.

> **Nenhuma das quatro?** Provavelmente é acervo. Se continuar em dúvida, é
> sinal de que o documento é fronteiriço — decida e registre a decisão, em vez
> de criar uma pasta nova para o caso.

---

# Parte 3 — A ferramenta

## 3.0 Do zero até a primeira pasta criada

Sete passos. Do quarto em diante você não repete mais nenhum.

**1. Descompacte** o `vbr_pastas.zip` numa pasta sua — `~/vbr-pastas` serve.
Todos os comandos abaixo rodam de dentro dela.

**2. Instale as bibliotecas.**

```bash
cd ~/vbr-pastas
pip install -r requirements.txt
```

**3. Gere a credencial do Google.** Cinco minutos, uma vez na vida. O passo a
passo com os nomes de cada tela está no `README.md`, seção *A credencial do
Google*. O resumo: crie um projeto no Google Cloud, ative a **Google Drive
API**, crie uma credencial **OAuth de app para computador**, baixe o JSON e
salve como `credentials.json` ao lado dos arquivos do programa. Acrescente
`vbrisks@gmail.com` como usuário de teste — é a conta dona das pastas.

> `credentials.json` e `token.json` dão acesso ao Drive. Não os ponha em pasta
> compartilhada nem em repositório.

**4. Veja o modelo, sem tocar em nada.** Este comando não fala com o Drive:
serve para confirmar que a instalação está de pé.

```bash
python vbr_pastas.py modelo
```

**5. Diga onde ficam as pastas.** Na primeira execução de qualquer comando que
fale com o Drive, o programa pergunta e grava a resposta. Para adiantar:

```bash
python vbr_pastas.py config --definir "GESTÃO DE RISCOS/CLIENTES"
```

O funil ele deduz sozinho: a pasta irmã, `GESTÃO DE RISCOS/ORIGINACAO`.

**6. Autorize.** No primeiro comando que fale com o Drive, o navegador abre
pedindo autorização. Depois disso o programa grava o `token.json` e não
pergunta mais — o token se renova sozinho.

**7. Crie a primeira coisa.** Um prospecto:

```bash
python vbr_pastas.py originar CVCP
```

Ele pergunta a competência, mostra o plano, e só cria depois do seu "criar?".
Como a pasta `ORIGINACAO` ainda não existe, ele avisa e oferece criá-la.

## 3.1 A regra que vale para todos os comandos

**Nada é criado, movido ou renomeado sem o plano aparecer na tela e você
confirmar.** O plano mostra a árvore inteira e o número de pastas antes de
qualquer chamada de escrita. O padrão da resposta é "não": se você apertar
Enter sem pensar, nada acontece.

**Rodar duas vezes é seguro.** Antes de criar, o programa procura. Não existe
`PECEM-I` e `PECEM-I 2` — é o que torna seguro repetir um comando que falhou
no meio.

## 3.2 Onde ficam os clientes e o funil

Os caminhos **não estão no código**. Na primeira execução o programa pergunta
o dos clientes e grava em `config.json`. O do funil ele **deduz**: a pasta
irmã de `CLIENTES` chamada `ORIGINACAO`.

```bash
python vbr_pastas.py config --definir "GESTÃO DE RISCOS/CLIENTES"
python vbr_pastas.py config      # vê os dois e confere se existem no Drive
python vbr_pastas.py config --definir-funil "OUTRO/LUGAR"   # se não for a irmã
```

Para uma execução só, sem gravar: `--raiz "OUTRO/CAMINHO"` e
`--originacao "OUTRO/CAMINHO"`.

Na primeira vez que você rodar `originar`, a pasta do funil provavelmente não
existe. O programa percebe, diz que o pai está lá e oferece criá-la.

## 3.3 Os comandos

| Comando | O que faz |
|---|---|
| `originar` | abre uma originação no funil |
| `funil` | mostra o funil: o que está aberto, há quanto tempo, o que foi encerrado e por quê |
| `encerrar` | originação que não fechou sai do funil, com data e motivo |
| `reabrir` | traz de volta do `ZZ-ENCERRADAS` |
| `promover` | assinou: a originação sai do funil, entra no cliente e a árvore cresce |
| `novo` | cria um cliente com mandato, do zero |
| `frente` | abre uma frente em cliente ou ativo que já existe |
| `ramo` | abre um ramo de apólice |
| `auditar` | confere um cliente, ou o funil, contra o modelo |
| `config` | vê e muda onde ficam os clientes e o funil |
| `modelo` | imprime o modelo em vigor |

**Nada é criado, movido ou renomeado sem o plano aparecer na tela e você
confirmar.**

### O ciclo de uma originação

```bash
python vbr_pastas.py originar CVCP        # entra no funil
python vbr_pastas.py funil                # vê o funil inteiro
python vbr_pastas.py promover CVCP        # assinou: atravessa para CLIENTES
```

Ou, se não fechar:

```bash
python vbr_pastas.py encerrar CVCP --motivo "ficou com a corretora atual"
python vbr_pastas.py reabrir CVCP         # se o nome voltar
```

`originar` pergunta o nome e a competência, e cria as seis subpastas. Rodar
duas vezes não cria pasta repetida — e continua achando a mesma pasta mesmo
que alguém a tenha renomeado à mão, porque a busca é por uma **etiqueta
invisível** gravada na própria pasta.

Essa etiqueta é o nome da originação, sem a data e sem onde ela está:
`vbr/ORIGINACAO/CVCP`. De propósito. Uma originação ganha e perde o prefixo de
data, muda de lugar duas ou três vezes na vida — funil, encerradas, funil de
novo, dentro do cliente — e continua sendo a mesma coisa. Se a etiqueta
seguisse o caminho, cada mudança dessas a invalidaria.

`promover` mostra o plano em duas partes — o que **muda de lugar** e o que é
**criado** — antes de tocar em qualquer coisa. Se você promover um nome que
não está no funil, ele avisa e oferece seguir assim mesmo, criando uma
originação vazia dentro do cliente novo.

### Criar um cliente sem passar pelo funil

```bash
python vbr_pastas.py novo
```

Para cliente que já chega com mandato e nunca teve originação registrada. Se
houve originação no funil, use `promover` em vez disto — senão a originação
fica lá e o cliente nasce com uma pasta vazia no lugar dela.

Ele pergunta nome, ativos e frentes, mostra a árvore inteira e espera o
"criar?". Um grupo com três ativos e duas frentes dá cerca de 50 pastas.

### Abrir uma frente

```bash
python vbr_pastas.py frente
```

Pergunta o caminho (`GRUPO-DIAMANTE` ou `GRUPO-DIAMANTE/PECEM-I`), o título, a
competência e o tipo. Cria `FRENTES` se ainda não existir.

O caminho é **a partir da raiz de clientes**, não do Meu Drive: `GRUPO-DIAMANTE`
para uma frente do grupo, `GRUPO-DIAMANTE/PECEM-I` para uma frente do ativo. Na
dúvida sobre o nível, volte à Regra 2 — a frente mora no nível do seu escopo.

### Abrir um ramo de apólice

```bash
python vbr_pastas.py ramo
```

Pergunta o caminho do cliente ou do ativo e quantos ramos você quiser, um por
linha. Cada ramo nasce com `VIGENTE`, `HISTORICO` e `SINISTROS`. Cria
`APOLICES` se ainda não existir.

Ramo se abre **quando há apólice**, não por precaução. O programa lista os
ramos da casa como sugestão, mas aceita nome fora da lista — a auditoria
depois sinaliza como nota, para você conferir se é ramo novo ou nome
divergente.

### Ver e cuidar do funil

```bash
python vbr_pastas.py funil
python vbr_pastas.py funil --paciencia 6      # mais rigoroso
```

Mostra o que está aberto e há quantos meses, e o que foi encerrado, quando e
por quê. As abertas há mais de doze meses saem marcadas com `!`.

`encerrar` **exige motivo** — sem ele o programa não encerra. Não é burocracia:
o motivo é a única coisa que dá valor ao registro dois anos depois, quando o
nome voltar a aparecer.

```bash
python vbr_pastas.py encerrar CVCP --motivo "ficou com a corretora atual"
```

### Auditar

```bash
python vbr_pastas.py auditar GRUPO-DIAMANTE
python vbr_pastas.py auditar GRUPO-DIAMANTE --saida relatorio.txt
python vbr_pastas.py auditar --funil       # audita o funil em vez de um cliente
```

**Só lê. Nunca muda nada.** Sai com código 1 se houver erro, o que permite usar
numa verificação automática.

No funil ela checa outra coisa: não há apólice nem ativo para cobrar, então o
que importa é o nome datado, a forma das seis subpastas, e **originação parada
há tempo demais** — acima de doze meses, por padrão. Originação parada não é
erro de pasta: é uma decisão que ninguém tomou.

## 3.4 O que a auditoria procura

| Gravidade | Significa |
|---|---|
| **ERRO** | foge do modelo |
| **AVISO** | merece um olhar |
| **NOTA** | informação |

Cada regra existe porque alguma coisa deu errado daquele jeito na migração de
setembro:

- **espaço no começo ou no fim do nome** — invisível na tela, quebra busca
- **subpasta faltando** na originação, no acervo ou num ramo
- **frente fora de qualquer tipo** — diz de qual mais se aproxima e o que falta
- **nome de frente fora de `AAAA-MM_TITULO`**
- **ramo com nome antigo** — `comercial` aponta para `EMPRESARIAL`
- **originação dentro do ativo** — originação é do grupo
- **pasta em `CLIENTES` que só tem originação** — é um prospecto no lugar
  errado: não há mandato, logo não há cliente. Um diagnóstico só, em vez dos
  três achados soltos que sairiam daí (sem APOLICES, sem FRENTES, sem ativo)
- **originação no modelo anterior, de quatro subpastas** — nota, não erro, com
  a lista do que renomear
- **originação aberta há mais de doze meses** (só em `--funil`)
- **arquivo solto** onde o modelo só espera pasta
- **nome repetido**, e o padrão ` 2`, ` 3` do Drive

## 3.5 Criar um tipo de frente novo

Uma entrada em `TIPOS_FRENTE`, dentro de `modelo.py`:

```python
"VISTORIA": {
    "descricao": "vistoria de risco em campo",
    "quando": "visita técnica com relatório e recomendações",
    "subpastas": ["01-PREPARACAO", "02-CAMPO", "03-RELATORIO", "04-RECOMENDACOES"],
},
```

O terminal passa a oferecer, a criação sabe montar e a auditoria para de
reclamar. **Não é preciso mexer em mais nada.**

## 3.6 Quando dá errado

| O que aparece | O que é | O que fazer |
|---|---|---|
| `faltam as bibliotecas do Google` | o `pip install` não rodou, ou rodou noutro Python | `pip install -r requirements.txt`, na mesma pasta |
| `não achei credentials.json` | a credencial do Google não foi gerada ou está noutro lugar | passo 3 da seção 3.0; ou aponte com `VBR_CREDENCIAL` |
| `não achei 'X/Y' no seu Drive` | o caminho gravado não existe mais — em geral alguém renomeou ou moveu a pasta | o programa diz **em que degrau** quebrou e lista o que existe ali; corrija com `config` |
| a pasta do funil não existe | normal na primeira vez | o programa oferece criá-la; responda que sim |
| `já existe uma originação com esse nome` | ela está no funil ou em `ZZ-ENCERRADAS` | se estiver encerrada, `reabrir` em vez de `originar` |
| `está em ZZ-ENCERRADAS` ao promover | você tentou promover uma originação encerrada | `reabrir` primeiro, depois `promover` |
| `sem motivo, não encerro` | `encerrar` sem `--motivo` | dê o motivo; é o que faz o registro valer |
| o comando parou no meio | conexão, token expirado, qualquer coisa | **rode de novo**. Criar é idempotente: o que já existe não é recriado |

Duas coisas que o programa **não** resolve, e nenhum programa resolve:

- **Arquivo cujo dono é outra conta não se move.** Nem com permissão de edição.
  O dono precisa transferir a propriedade. Aparece como erro do Drive, não do
  programa.
- **Pasta renomeada à mão no Drive** continua sendo encontrada, porque a busca
  é pela etiqueta invisível antes do nome. Mas pasta **criada** à mão, fora do
  programa, não tem etiqueta: ela é encontrada pelo nome e ganha a etiqueta na
  hora. Se o nome estiver fora da grafia da casa, não será encontrada — e aí a
  auditoria é o que revela.

## 3.7 Conferir o programa sem tocar no Drive

```bash
python teste_funil.py
```

Roda o ciclo inteiro de uma originação — criar, encerrar, reabrir, promover,
auditar — contra um Drive de mentira, em memória. Não fala com o Google, não
precisa de credencial, não muda nada. Serve para conferir que uma alteração em
`modelo.py` não quebrou nada antes de usar o programa de verdade.

---

# Parte 4 — Achados que viraram regra

Sete coisas que a migração de setembro de 2026 ensinou. Valem para qualquer
trabalho em Drive, não só para este.

**1. Espaço no fim do nome é invisível e venenoso.**
`FRENTE CESSÃO BANCO ` e `05-ANALISE ` conviveram meses sem ninguém notar.
Qualquer busca por nome exato falha. A auditoria trata como ERRO.

**2. O Drive numera cópias, e a de número maior costuma ser a mais nova.**
Subir o mesmo nome duas vezes gera `PACOTE v2.0` e `PACOTE v2.0 2`. O instinto
diz que a sem número é a boa; **muitas vezes é o contrário**. Confira as datas
antes de escolher. No caso real os dois eram idênticos, mas só a comparação
arquivo a arquivo provou isso.

**3. Pasta de descarte aninhada dentro de pasta que se move vai junto.**
Se `01_Insumos` vai migrar e tem uma subpasta marcada para descarte, a subpasta
migra também e nunca mais será purgada. **Desencaixe o descarte antes de mover
o pai.** Na Cessão Banco foram doze pastas assim.

**4. A paginação do Drive repete entradas.**
Uma pasta com 169 arquivos devolve 100 + 93, com 24 repetidos. Somar as páginas
dá 193. **Sempre elimine por id** antes de contar. O programa já faz isso.

**5. Arquivo de terceiro não se move.**
Documento cujo dono é outra conta não sai da pasta compartilhada, por mais
permissão de edição que você tenha. O dono precisa transferir a propriedade.

**6. Antes de apagar, prove que existe cópia.**
Trinta e oito arquivos pareciam material vivo indo para a lixeira. Trinta eram
cópias byte a byte, três eram lixo do macOS, três tinham gêmeos em outro lugar
— e **um era único**. Sem a comparação nome a nome, aquele um teria sumido.

**7. ID de pasta guardado de memória não é confiável.**
Depois de muitas etapas, dois IDs "certos" apontavam para o nada. Confirme
navegando pelo caminho, não pelo id que você acha que é.

---

# Parte 5 — Quando o modelo não responde

O modelo cobre o que já apareceu. Vai aparecer coisa que ele não cobre.

**Não crie uma pasta nova para resolver o caso.** Uma pasta criada fora do
modelo vira precedente, e três precedentes desfazem o modelo. Em vez disso:

1. Ponha o documento no lugar **menos errado** dos que existem.
2. Registre a dúvida.
3. Quando o mesmo caso aparecer uma segunda vez, aí sim decida — e a decisão
   entra em `modelo.py`, que é o que faz a regra valer para todo mundo.

O que mantém uma estrutura viva não é ela prever tudo. É ela mudar por decisão
registrada, e não por acúmulo de exceções.

---

*Modelo travado em 13/09/2026 · migração executada em 14/09/2026 ·
funil de originação separado em 16/09/2026 ·
43 decisões, 442 pastas e 1.814 arquivos inventariados.*
