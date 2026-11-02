# vbr-pastas

Monta e confere a árvore de pastas de clientes da VB Risk no Google Drive.

O modelo inteiro vive em `modelo.py`. Mudou a regra, muda um arquivo — a
criação e a auditoria passam a seguir a regra nova sem mais nenhuma alteração.

---

## O que ele faz

```
python vbr_pastas.py originar   abre uma originação no funil
python vbr_pastas.py funil      mostra o funil, com a idade de cada uma
python vbr_pastas.py encerrar   originação que não fechou sai do funil
python vbr_pastas.py reabrir    traz de volta do ZZ-ENCERRADAS
python vbr_pastas.py promover   assinou: a originação entra no cliente
python vbr_pastas.py novo       cria um cliente com mandato, do zero
python vbr_pastas.py ativo      acrescenta um ativo a um cliente que já existe
python vbr_pastas.py frente     abre uma frente num cliente que já existe
python vbr_pastas.py ramo       abre um ramo de apólice
python vbr_pastas.py auditar    confere um cliente, ou o funil, contra o modelo
python vbr_pastas.py alinhar    põe uma frente atrás do modelo na forma certa
python vbr_pastas.py config     vê e muda onde ficam os clientes e o funil
python vbr_pastas.py modelo     mostra o modelo em vigor
```

Nenhum comando escreve no Drive sem imprimir o plano e esperar você confirmar.

Tem também uma tela, que sobe com o Mac: `Abrir VBR Pastas.webloc` a abre no
navegador. Como operar está em `MANUAL_DE_OPERACAO.md`. Sem o agente: duplo
clique em `VBR Pastas.command`, ou
`python3 servidor.py` (`--falso` para ver a tela sem credencial, contra um
Drive de demonstração, na porta 8766). O que ela faz e o que ainda não faz está em
`TELA_ETAPA1.md` (funil), `TELA_ETAPA2.md` (clientes, frente, ramo, auditoria) e
`TELA_ETAPA3.md` (subir com o Mac, sem Terminal).

---

## Duas raízes, não uma

```
GESTÃO DE RISCOS/
├── CLIENTES/      só quem tem mandato assinado
└── ORIGINACAO/    o funil: quem ainda não assinou
```

Prospecto não tem pasta em `CLIENTES`. É aritmética: no AVRA há onze projetos
em originação contra um ativo, então com uma raiz só onze de doze pastas de
cliente não seriam de cliente.

Quando o contrato assina, a originação **muda de lugar**: sai do funil, entra
na pasta do cliente e passa a se chamar `00-ORIGINACAO`. Move, não copia —
mesmo id, mesmo compartilhamento, mesmo histórico.

```bash
python vbr_pastas.py originar CVCP
python vbr_pastas.py promover CVCP
```

Quem não fecha vai para `ZZ-ENCERRADAS` com data e motivo, e não some:
prospecto volta, e saber quem disse não e por quê é metade do trabalho da
próxima vez.

---

## Onde ficam os clientes e o funil

O caminho **não está no código**. Na primeira execução o programa pergunta o
dos clientes, grava a resposta em `config.json` e não pergunta mais. O do
funil ele deduz: a pasta irmã de `CLIENTES` chamada `ORIGINACAO`.

```bash
python vbr_pastas.py config                                  # vê e muda
python vbr_pastas.py config --definir "GESTÃO DE RISCOS/CLIENTES"
python vbr_pastas.py config --definir-funil "OUTRO/LUGAR"    # se não for a irmã
```

Quatro maneiras de dizer o caminho, da mais forte para a mais fraca:

| Como | Vale para | Quando usar |
|---|---|---|
| `--raiz "CAMINHO"` | só aquela execução | testar outro lugar sem mexer em nada |
| `VBR_RAIZ` no ambiente | a sessão do terminal | rodar contra uma cópia de teste |
| `config.json` | sempre | o normal |
| a pergunta na 1ª execução | grava no config.json | acontece uma vez só |

O caminho é a partir da raiz do Meu Drive, com barras:
`GESTÃO DE RISCOS/CLIENTES`.

**Mudou o nome ou o lugar da pasta?** Rode `config` e aponte para o novo.
Se errar, o programa não diz só "não achei" — ele diz em que degrau o caminho
quebrou e lista o que existe ali:

```
não achei 'GESTÃO DE RISCOS/NOVA_CLIENTES' no seu Drive.
  cheguei até 'GESTÃO DE RISCOS', mas lá dentro não há 'NOVA_CLIENTES'.
  o que existe em 'GESTÃO DE RISCOS':
    ADMINISTRATIVO
    CLIENTES
    FINANCEIRO
    ...
```

---

## Instalação

```bash
pip install -r requirements.txt
```

### A credencial do Google — uma vez só

O programa fala com o Drive pela API oficial, então precisa de uma credencial
sua. São cinco minutos, e vale para sempre.

1. Abra <https://console.cloud.google.com/> e crie um projeto
   (nome livre, `vbrisk-pastas` serve).
2. Em **APIs e serviços → Biblioteca**, procure **Google Drive API** e clique
   em **Ativar**.
3. Em **APIs e serviços → Tela de consentimento OAuth**, escolha **Externo**,
   preencha nome do app e seu e-mail, e salve. Em **Usuários de teste**,
   acrescente o e-mail da conta que é dona das pastas — `vbrisks@gmail.com`.
4. Em **APIs e serviços → Credenciais**, clique em **Criar credenciais →
   ID do cliente OAuth**, tipo **App para computador**.
5. Baixe o JSON e salve como `credentials.json` ao lado destes arquivos.

Na primeira execução o navegador abre pedindo autorização. Depois disso o
programa grava `token.json` e não pergunta mais — o token se renova sozinho.

> `credentials.json` e `token.json` dão acesso ao seu Drive. Não os coloque
> em pasta compartilhada nem em repositório.

Se preferir guardá-los em outro lugar:

```bash
export VBR_CREDENCIAL=~/.config/vbrisk/credentials.json
export VBR_TOKEN=~/.config/vbrisk/token.json
```

---

## O modelo

Quatro espécies de árvore:

| Espécie | Onde mora | O que é |
|---|---|---|
| **ORIGINAÇÃO** | no funil antes de assinar; no grupo depois | pré-mandato: cadastro, insumos, trabalhos, propostas, contratos, comunicações |
| **FRENTE** | grupo ou ativo | trabalho temporário sob mandato e plano de trabalho |
| **ACERVO** | ativo | permanente: o que descreve o ativo |
| **APÓLICES** | grupo e ativo | permanente, por ramo → VIGENTE / HISTORICO / SINISTROS |

A frente mora no nível do seu escopo: frente de um ativo fica sob o ativo,
frente que atravessa ativos fica sob o cliente.

### Tipos de frente

Foi o ponto do pedido — cada necessidade tem sua forma de árvore.

| Tipo | Quando usar | Subpastas |
|---|---|---|
| **RENOVACAO** | vencimento chegando, com cotação de mais de uma seguradora | 01-INSUMOS · 02-TRABALHOS · 03-ENTREGAS · 04-COTACOES-RECEBIDAS · 05-ANALISE-COMPARATIVA · 06-DECISAO-E-EMISSAO · 07-COMUNICACOES |
| **CONCORRENCIA** | RFP de corretora, concorrência de seguradora | 01-INSUMOS · 02-TRABALHOS · 03-ENTREGAS · 04-PROPOSTAS-RECEBIDAS · 05-ANALISE-COMPARATIVA · 06-DECISAO · 07-COMUNICACOES |
| **ANALISE** | estudo ou diagnóstico que termina numa decisão | 01-INSUMOS · 02-TRABALHOS · 03-ENTREGAS · 04-DECISOES · 05-COMUNICACOES |
| **VISITA-TECNICA** | visita de campo com relatório e recomendações | 01-INSUMOS · 02-TRABALHOS · 03-ENTREGAS · 04-REGISTRO-DE-CAMPO · 05-RECOMENDACOES · 06-COMUNICACOES |
| **SINISTRO** | sinistro relevante que exige condução própria | 01-INSUMOS · 02-TRABALHOS · 03-ENTREGAS · 04-REGULACAO · 05-ENCERRAMENTO · 06-COMUNICACOES |

**Toda frente termina em COMUNICACOES.** Entra só o que tem consequência —
define, aceita, altera ou recusa algo. Agenda de reunião não entra, senão a
pasta vira arquivo morto de e-mail.

### Prospecto e mandato

**Prospecto tem só a originação**, e ela mora no funil. Sem ativo, sem acervo,
sem apólice, sem frente — frente é trabalho sob mandato, e antes do contrato
não há mandato.

Quando o contrato assina, a árvore cresce:

```bash
python vbr_pastas.py promover CVCP
```

A originação atravessa inteira e vira `00-ORIGINACAO`; entram as apólices e
frentes do grupo, e cada ativo com seu acervo. **A originação não se mexe por
dentro** — é o registro do que houve antes do contrato e permanece.

As seis subpastas da originação põem o eixo da casa também aqui — insumo,
trabalho, entrega — porque a proposta é a entrega da originação. A forma
anterior, de quatro, descrevia o resultado e não o trabalho: o material que o
prospecto manda e a análise que sustenta a proposta caíam os dois dentro de
`02-PROPOSTAS`. Quem já está na forma de quatro não está errado, está no
modelo anterior: a auditoria diz o que renomear, como nota.

Mandato não vira pasta. Olhando os tipos reais de projeto, eles se partem em
dois: trabalho com começo e fim já é uma frente; mandato continuado é a própria
relação com o cliente, que já é a pasta do cliente. Nenhum dos dois pede nível
novo.

### Como criar um tipo novo

Acrescente uma entrada em `TIPOS_FRENTE`, dentro de `modelo.py`:

```python
"VISTORIA": {
    "descricao": "vistoria de risco em campo",
    "quando": "visita técnica com relatório e recomendações",
    "subpastas": [
        "01-PREPARACAO",
        "02-CAMPO",
        "03-RELATORIO",
        "04-RECOMENDACOES",
    ],
},
```

Pronto. O terminal passa a oferecer o tipo, a criação sabe montá-lo e a
auditoria para de reclamar das frentes que seguem essa forma.

### Grafia

Hífen, maiúscula, sem acento. O programa normaliza sozinho:

```
'Renovação Apólices'  ->  'RENOVACAO-APOLICES'
'D&O'                 ->  'D-O'
'  Pecem I  '         ->  'PECEM-I'
'RC Geral'            ->  'RC-GERAL'
```

Nome de frente é `AAAA-MM_TITULO`, com a competência de quando a frente
começou — não de quando a pasta foi criada.

---

## A auditoria

```bash
python vbr_pastas.py auditar GRUPO-DIAMANTE
python vbr_pastas.py auditar GRUPO-DIAMANTE --saida relatorio.txt
```

Ela só lê. Nunca muda nada. Sai com código 1 se houver erro, o que permite
usá-la numa verificação automática.

Três gravidades: **ERRO** foge do modelo, **AVISO** merece um olhar,
**NOTA** é informação.

As regras saíram de defeitos reais encontrados na migração de setembro de
2026 — cada uma existe porque alguma coisa deu errado daquele jeito:

- **espaço no começo ou no fim do nome.** Invisível na tela do Drive e
  quebra qualquer busca por nome exato. Foi o que escondeu
  `FRENTE CESSÃO BANCO ` e `05-ANALISE ` por meses.
- **subpasta faltando** na originação, no acervo ou num ramo.
- **frente que não bate com nenhum tipo.** O relatório diz de qual tipo ela
  mais se aproxima e o que falta ou sobra — sintoma de estrutura montada à mão.
- **nome de frente fora de AAAA-MM_TITULO.**
- **ramo com nome antigo.** `comercial` aponta para `EMPRESARIAL`,
  `RO` para `RO-BI`, e assim por diante.
- **originação dentro do ativo.** Originação é do grupo. A regra compara
  normalizado, então pega `00_ORIGINACAO` e `00-ORIGINACAO` igual.
- **arquivo solto** onde o modelo só espera pasta — na raiz do cliente, da
  frente, do acervo ou de APOLICES.
- **nome repetido na mesma pasta**, e o padrão ` 2`, ` 3` que o Drive
  acrescenta ao subir o mesmo nome duas vezes. Foi assim que quatro cópias
  do mesmo pacote de entrega conviveram lado a lado. Atenção: a de número
  maior costuma ser a **mais recente**, não a mais antiga.

---

## Duas garantias do código

**Criar é idempotente.** Antes de criar, procura. Rodar duas vezes no mesmo
cliente não gera `PECEM-I` e `PECEM-I 2`. É o que torna seguro repetir um
comando que falhou no meio.

**A pasta sobrevive a ser renomeada.** Cada pasta criada recebe uma etiqueta
invisível gravada nela mesma, que o Drive não mostra na tela. Na execução
seguinte o programa procura primeiro pela etiqueta e só depois pelo nome —
então alguém renomear ou mover a pasta à mão não faz o programa criar uma
segunda ao lado. Pasta antiga encontrada pelo nome recebe a etiqueta na hora.

A etiqueta é o caminho inteiro, não a espécie: `vbr/GRUPO-DIAMANTE/PECEM-I/ACERVO`.
Uma versão anterior etiquetava a espécie, e o segundo cliente casava com a
etiqueta do primeiro — a árvore inteira caía dentro dele.

A originação é a exceção: a etiqueta dela é o nome, sem a data e sem o lugar —
`vbr/ORIGINACAO/CVCP`. Ela ganha e perde o prefixo de data e muda de lugar
duas ou três vezes na vida (funil, encerradas, funil de novo, dentro do
cliente) e continua sendo a mesma coisa. Etiqueta que seguisse o caminho se
invalidaria a cada mudança dessas.

**Promover move, não copia.** O id não muda, os links que alguém já tem
continuam valendo, o compartilhamento não se perde e o histórico não se parte
em dois. Copiar deixaria duas versões da mesma originação convivendo — o
defeito que a migração de setembro passou três dias desfazendo.

**Listar devolve tudo, sem repetido.** A paginação do Drive pode entregar a
mesma entrada em duas páginas quando a pasta muda durante a varredura. Os ids
passam por um conjunto antes de sair. Sem isso, uma pasta de 169 arquivos é
contada como 193.

---

## Arquivos

```
servidor.py      a tela: serve pagina.html em 127.0.0.1:8765 e chama os módulos daqui
pagina.html      a página — HTML, CSS e JavaScript, sem nada de fora
VBR Pastas.command  duplo clique abre a tela (ver TELA_ETAPA1.md)
alinhar.py       o plano de alinhamento de uma frente atrás do modelo
lancador.py      o agente do launchd: o programa subindo com o Mac
teste_lancador.py   o agente contra um launchctl de mentira
teste_conectar.py   o token vencido: o programa reautoriza em vez de parar
teste_servidor.py   o ciclo inteiro pela tela, contra o Drive falso
teste_arvore.py     a leitura de árvore por nível: mesmas respostas, 20x menos chamadas
modelo.py        o modelo e a grafia — é aqui que se mexe
config.py        lê e grava os caminhos dos clientes e do funil
drive.py         conversa com a API do Drive
auditoria.py     as regras de conferência
vbr_pastas.py    o terminal
drive_falso.py   um Drive de mentira, em memória, para os testes
teste_funil.py   roda o ciclo inteiro de uma originação sem tocar no Drive

config.json      criado na 1ª execução; guarda só o caminho
credentials.json você baixa do Google Cloud   — não versionar
token.json       criado na 1ª autorização     — não versionar
```
