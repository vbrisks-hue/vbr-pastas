"""
Testa a tela de ponta a ponta, pelo HTTP, contra o Drive falso.

    python3 teste_servidor.py

Sobe o servidor numa porta livre, percorre o ciclo inteiro — originar,
encerrar, reabrir, promover — pelos mesmos endereços que a página usa, e
confere o Drive falso do outro lado. Não fala com o Google, não lê credencial.
"""

from __future__ import annotations

import json
import sys
import threading
import urllib.error
import urllib.request

import auditoria
import drive
import drive_falso
import modelo
import servidor

FALHAS: list[str] = []


def conferir(condicao: bool, descricao: str) -> None:
    print(f"  [{'ok  ' if condicao else 'FALHA'}] {descricao}")
    if not condicao:
        FALHAS.append(descricao)


falso = drive_falso.com_exemplo()
tela = servidor.Tela(lambda: falso, "falso", "GESTAO DE RISCOS/CLIENTES", "GESTAO DE RISCOS/ORIGINACAO")
srv = servidor.servidor_para(tela, 0)
porta = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{porta}"


def chamar(caminho, dados=None, origem=None, tipo="application/json"):
    """Devolve (status, corpo). Erros HTTP viram (status, corpo) também."""
    cabecalhos = {}
    corpo = None
    if dados is not None:
        corpo = json.dumps(dados).encode("utf-8")
        cabecalhos["Content-Type"] = tipo
    if origem:
        cabecalhos["Origin"] = origem
    pedido = urllib.request.Request(BASE + caminho, data=corpo, headers=cabecalhos)
    try:
        with urllib.request.urlopen(pedido, timeout=5) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as erro:
        texto = erro.read().decode("utf-8")
        try:
            return erro.code, json.loads(texto)
        except json.JSONDecodeError:
            return erro.code, {"bruto": texto}


def pasta_chamada(nome):
    return [i for i in falso.itens.values() if i["name"] == nome and i["mimeType"] == drive.MIME_PASTA]


print("\n1. a página e o estado")
with urllib.request.urlopen(BASE + "/", timeout=5) as r:
    html = r.read().decode("utf-8")
conferir("<title>VBR Pastas</title>" in html, "a página vem do servidor")
conferir("http://" not in html and "https://" not in html, "a página não referencia nada de fora")
conferir("src=" not in html.split("<script>")[0], "nenhum script externo")
status, estado = chamar("/api/estado")
conferir(status == 200 and estado["modo"] == "falso", "estado diz que o Drive é de demonstração")
status, mod = chamar("/api/modelo")
conferir([t["codigo"] for t in mod["tipos_frente"]] == list(modelo.TIPOS_FRENTE),
         "os tipos de frente vêm do modelo.py, na ordem dele")
conferir(mod["originacao"]["subpastas"] == modelo.ORIGINACAO_SUBPASTAS, "as subpastas da originação vêm do modelo")

print("\n2. o funil de exemplo")
status, funil = chamar("/api/funil")
conferir(funil["existe"], "o funil existe")
conferir([o["nome"] for o in funil["abertas"]] == ["2023-01_ANTIGA", "2026-03_CVCP", "2026-08_XPTO"],
         "três abertas, em ordem de nome")
antiga = next(o for o in funil["abertas"] if o["nome"] == "2023-01_ANTIGA")
conferir(antiga["parada"] and antiga["meses"] >= 12, "a de 2023 passou da paciência")
conferir(funil["encerradas"][0]["motivo"] == "ficou com a corretora atual", "a encerrada traz o motivo")

print("\n3. a grafia enquanto se digita")
status, g = chamar("/api/grafia?nome=Campo%20Verde&competencia=2026-09")
conferir(g["grafia"] == "CAMPO-VERDE" and g["pasta"] == "2026-09_CAMPO-VERDE", "Campo Verde -> 2026-09_CAMPO-VERDE")
status, g = chamar("/api/grafia?nome=X&competencia=13")
conferir(g["erro"] and "AAAA-MM" in g["erro"], "competência errada devolve a frase certa")

print("\n4. originar — plano, senha, execução")
status, r = chamar("/api/originar/plano", {"nome": "Campo Verde", "competencia": "2026-09"})
conferir(status == 200 and "senha" in r, "o plano veio com senha")
conferir(r["plano"]["partes"][0]["total"] == 1 + len(modelo.ORIGINACAO_SUBPASTAS)
         + sum(len(v) for v in modelo.ORIGINACAO_NETOS.values()), "o plano conta a originação, as subpastas e LOGOS")
conferir(any("2026-09_CAMPO-VERDE" in l for l in r["plano"]["partes"][0]["linhas"]), "o plano mostra o nome da pasta")
conferir(not pasta_chamada("2026-09_CAMPO-VERDE"), "pedir o plano não criou nada")
senha = r["senha"]

status, e = chamar("/api/executar", {"senha": "inventada"})
conferir(status == 400 and "não está mais valendo" in e["erro"], "senha inventada é recusada")
status, e = chamar("/api/executar", {"senha": senha}, origem="http://outro-site.exemplo")
conferir(status == 403, "escrita vinda de outro site é recusada")
conferir(not pasta_chamada("2026-09_CAMPO-VERDE"), "e nada foi criado")

status, res = chamar("/api/executar", {"senha": senha}, origem=BASE)
conferir(status == 200 and any(p["texto"] == "2026-09_CAMPO-VERDE" for p in res["passos"]), "executou o plano")
criada = pasta_chamada("2026-09_CAMPO-VERDE")
conferir(len(criada) == 1 and criada[0]["appProperties"].get("vbr") == "vbr/ORIGINACAO/CAMPO-VERDE",
         "a pasta existe, com a etiqueta pelo nome")
status, e = chamar("/api/executar", {"senha": senha})
conferir(status == 400, "a senha é de uso único")
status, e = chamar("/api/originar/plano", {"nome": "campo verde", "competencia": "2026-01"})
conferir(status == 400 and "Já existe" in e["erro"], "originar de novo o mesmo nome é recusado no plano")
status, e = chamar("/api/originar/plano", {"nome": "", "competencia": "2026-01"})
conferir(status == 400, "sem nome, sem plano")

print("\n5. encerrar")
status, e = chamar("/api/encerrar/plano", {"nome": "2026-09_CAMPO-VERDE", "motivo": "   "})
conferir(status == 400 and "motivo" in e["erro"], "sem motivo, não encerra")
status, r = chamar("/api/encerrar/plano", {"nome": "CAMPO-VERDE", "motivo": "preferiu esperar 2027"})
conferir(status == 200 and r["plano"]["partes"][0]["rotulo"] == "MOVER", "o plano diz que move")
status, res = chamar("/api/executar", {"senha": r["senha"]})
conferir(status == 200, "encerrou")
enc = pasta_chamada(modelo.ENCERRADAS)[0]
conferir(enc["id"] in criada[0]["parents"], f"a pasta está em {modelo.ENCERRADAS}")
conferir(criada[0]["appProperties"].get(drive.CHAVE_ENCERRAMENTO, "").endswith("|preferiu esperar 2027"),
         "o motivo ficou na etiqueta")
bilhetes = [i for i in falso.itens.values() if i["name"] == modelo.BILHETE_DE_ENCERRAMENTO
            and criada[0]["id"] in i["parents"]]
conferir(len(bilhetes) == 1, "o bilhete ficou dentro da pasta")
status, funil = chamar("/api/funil")
conferir(any(e["nome"] == "2026-09_CAMPO-VERDE" and e["motivo"] == "preferiu esperar 2027"
             for e in funil["encerradas"]), "o funil lista a encerrada com o motivo")

print("\n6. reabrir")
status, r = chamar("/api/reabrir/plano", {"nome": "2026-09_CAMPO-VERDE"})
conferir(status == 200 and any("fica" in a for a in r["plano"]["avisos"]), "o plano avisa que o bilhete fica")
status, res = chamar("/api/executar", {"senha": r["senha"]})
funil_id = falso.semear("GESTAO DE RISCOS/ORIGINACAO")
conferir(funil_id in criada[0]["parents"], "voltou ao funil")
conferir(drive.CHAVE_ENCERRAMENTO not in criada[0]["appProperties"], "a marca de encerramento saiu")
conferir(len(bilhetes) == 1 and criada[0]["id"] in bilhetes[0]["parents"], "o bilhete continua lá")
status, e = chamar("/api/reabrir/plano", {"nome": "CAMPO-VERDE"})
conferir(status == 400 and "já está aberta" in e["erro"], "reabrir o que está aberto é recusado")

print("\n7. promover")
cvcp = pasta_chamada("2026-03_CVCP")[0]
id_antes = cvcp["id"]
status, e = chamar("/api/promover/plano", {"nome": "CVCP", "cliente": "CVCP", "ativos": ["Usina Norte"],
                                           "frentes": [{"onde": "OUTRO", "titulo": "X", "competencia": "2026-09",
                                                        "tipo": "ANALISE"}]})
conferir(status == 400 and "não está na lista de ativos" in e["erro"], "frente em ativo que não existe é recusada")
status, e = chamar("/api/promover/plano", {"nome": "CVCP", "cliente": "CVCP",
                                           "frentes": [{"onde": "", "titulo": "X", "competencia": "2026-09",
                                                        "tipo": "INVENTADO"}]})
conferir(status == 400 and "sem tipo" in e["erro"], "tipo fora do modelo é recusado")
status, e = chamar("/api/promover/plano", {"nome": "FULANO", "cliente": "Fulano"})
conferir(status == 400 and modelo.ENCERRADAS in e["erro"], "promover uma encerrada manda reabrir primeiro")

pedido = {"nome": "CVCP", "cliente": "CVCP", "ativos": ["Usina Norte", "usina norte"],
          "frentes": [{"onde": "", "titulo": "RFP Corretora", "competencia": "2026-09", "tipo": "CONCORRENCIA"},
                      {"onde": "USINA-NORTE", "titulo": "Renovação RO", "competencia": "2026-09", "tipo": "RENOVACAO"}]}
status, r = chamar("/api/promover/plano", pedido)
conferir(status == 200, "o plano de promoção veio")
rotulos = [p["rotulo"] for p in r["plano"]["partes"]]
conferir(rotulos == ["MOVER", "CRIAR"], "o plano tem as duas partes: mover e criar")
linhas = "\n".join(r["plano"]["partes"][1]["linhas"])
conferir("USINA-NORTE" in linhas and "2026-09_RENOVACAO-RO" in linhas and "2026-09_RFP-CORRETORA" in linhas,
         "o plano mostra o ativo e as duas frentes")
conferir(linhas.count("USINA-NORTE") == 1 or "usina norte" not in linhas, "ativo repetido em grafia diferente entra uma vez")
conferir(not pasta_chamada("CVCP"), "pedir o plano não criou o cliente")
status, res = chamar("/api/executar", {"senha": r["senha"]})
conferir(status == 200, "promoveu")
cliente = pasta_chamada("CVCP")
clientes_id = falso.semear("GESTAO DE RISCOS/CLIENTES")
conferir(len(cliente) == 1 and clientes_id in cliente[0]["parents"], "CVCP está em CLIENTES")
conferir(cvcp["id"] == id_antes and cvcp["name"] == modelo.ORIGINACAO and cliente[0]["id"] in cvcp["parents"],
         f"a originação é a mesma pasta, agora {modelo.ORIGINACAO} dentro do cliente")
conferir(funil_id not in cvcp["parents"], "saiu do funil")
filhos = {i["name"] for i in falso.itens.values() if cliente[0]["id"] in i["parents"]}
conferir(filhos == {modelo.ORIGINACAO, modelo.APOLICES, modelo.FRENTES, "USINA-NORTE"}, f"o cliente tem {sorted(filhos)}")
status, funil = chamar("/api/funil")
conferir([o["nome"] for o in funil["abertas"]] == ["2023-01_ANTIGA", "2026-08_XPTO", "2026-09_CAMPO-VERDE"],
         "o funil tem uma originação a menos")

print("\n8. o cliente promovido passa na auditoria")
arvore = drive.ler_arvore(falso, cliente[0]["id"], incluir_arquivos=True)
rel = auditoria.auditar_cliente("CVCP", arvore)
conferir(not rel.erros, f"0 erros ({len(rel.avisos)} avisos, {len(rel.notas)} notas)")
for a in rel.erros:
    print("      ", a.caminho, a.mensagem)

print("\n9. o que não é da página")
status, e = chamar("/api/nada")
conferir(status == 404, "endereço desconhecido dá 404")
status, e = chamar("/api/executar", {"senha": "x"}, tipo="text/plain")
conferir(status == 400 and "não entende" in e["erro"], "escrita sem JSON é recusada")
conferir(servidor.frase_de_erro(RuntimeError("x")).startswith("Algo deu errado"), "erro desconhecido vira frase, não traceback")
conferir("conexão" in servidor.frase_de_erro(ConnectionError()), "falha de rede vira frase de rede")
conferir(srv.server_address[0] == "127.0.0.1", "o servidor escuta só em 127.0.0.1")

print("\n10. clientes e ativos, lidos do Drive")
status, d = chamar("/api/destinos")
caminhos = [x["caminho"] for x in d["destinos"]]
conferir(caminhos == ["CVCP", "CVCP/USINA-NORTE", "GRUPO-DIAMANTE", "GRUPO-DIAMANTE/CTJL", "GRUPO-DIAMANTE/PECEM-I"],
         f"cada cliente e cada ativo, na ordem: {caminhos}")
conferir(all(x["nivel"] == ("ativo" if "/" in x["caminho"] else "grupo") for x in d["destinos"]), "o nível de cada um")

print("\n11. frente — destino da lista, tipo do modelo")
status, e = chamar("/api/frente/plano", {"caminho": "GRUPO-DIAMANTE/CTJL", "titulo": "Sinistro Turbina",
                                         "competencia": "2026-09", "tipo": ""})
conferir(status == 400 and "tipo" in e["erro"], "sem tipo, sem plano")
status, e = chamar("/api/frente/plano", {"caminho": "NADA/AQUI", "titulo": "X", "competencia": "2026-09", "tipo": "SINISTRO"})
conferir(status == 400 and "Não achei" in e["erro"], "destino que não existe é recusado")
status, r = chamar("/api/frente/plano", {"caminho": "GRUPO-DIAMANTE/CTJL", "titulo": "Sinistro Turbina",
                                         "competencia": "2026-09", "tipo": "sinistro"})
conferir(status == 200 and r["plano"]["destino"].endswith("GRUPO-DIAMANTE/CTJL/FRENTES"), "o plano aponta para FRENTES do ativo")
linhas = "\n".join(r["plano"]["partes"][0]["linhas"])
conferir("2026-09_SINISTRO-TURBINA" in linhas and "04-REGULACAO" in linhas
         and r["plano"]["partes"][0]["total"] == 1 + len(modelo.TIPOS_FRENTE["SINISTRO"]["subpastas"]),
         "a árvore é a do tipo SINISTRO")
status, res = chamar("/api/executar", {"senha": r["senha"]})
frente = pasta_chamada("2026-09_SINISTRO-TURBINA")
ctjl_frentes = falso.semear("GESTAO DE RISCOS/CLIENTES/GRUPO-DIAMANTE/CTJL/FRENTES")
conferir(len(frente) == 1 and ctjl_frentes in frente[0]["parents"], "a frente está em CTJL/FRENTES")
conferir(frente[0]["appProperties"].get("vbr") == "vbr/GRUPO-DIAMANTE/CTJL/FRENTES/2026-09_SINISTRO-TURBINA",
         "etiquetada pelo caminho")

print("\n12. ramo")
status, e = chamar("/api/ramo/plano", {"caminho": "GRUPO-DIAMANTE/PECEM-I", "ramos": ["RC Geral"]})
conferir(status == 400 and "RCG" in e["erro"], "nome antigo de ramo é recusado com o nome novo")
status, e = chamar("/api/ramo/plano", {"caminho": "GRUPO-DIAMANTE/PECEM-I", "ramos": ["", "  "]})
conferir(status == 400, "sem ramo, sem plano")
status, r = chamar("/api/ramo/plano", {"caminho": "GRUPO-DIAMANTE/PECEM-I", "ramos": ["CYBER", "Equipamentos", "cyber"]})
conferir(status == 200 and r["plano"]["partes"][0]["total"] == 2 * (1 + len(modelo.RAMO_SUBPASTAS)), "dois ramos, repetido entra uma vez")
conferir(any("EQUIPAMENTOS" in a for a in r["plano"]["avisos"]), "ramo fora da lista vem com aviso")
status, res = chamar("/api/executar", {"senha": r["senha"]})
pecem_apolices = falso.semear("GESTAO DE RISCOS/CLIENTES/GRUPO-DIAMANTE/PECEM-I/APOLICES")
ramos = {i["name"] for i in falso.itens.values() if pecem_apolices in i["parents"]}
conferir(ramos == {"RO-BI", "CYBER", "EQUIPAMENTOS"}, f"PECEM-I/APOLICES tem {sorted(ramos)}")

print("\n13. cliente novo")
status, e = chamar("/api/cliente/plano", {"nome": "Grupo Mercurio", "mandato": False})
conferir(status == 400 and "funil" in e["erro"], "sem mandato, manda para o funil")
status, r = chamar("/api/cliente/plano", {"nome": "Grupo Mercúrio", "mandato": True, "ativos": ["UTE Pilar"],
                                          "frentes": [{"onde": "UTE-PILAR", "titulo": "Diagnóstico", "competencia": "2026-09", "tipo": "ANALISE"}]})
conferir(status == 200 and r["plano"]["partes"][0]["linhas"][0].endswith("GRUPO-MERCURIO"), "o plano começa pelo cliente")
status, res = chamar("/api/executar", {"senha": r["senha"]})
merc = pasta_chamada("GRUPO-MERCURIO")
conferir(len(merc) == 1 and clientes_id in merc[0]["parents"], "GRUPO-MERCURIO está em CLIENTES")
filhos = {i["name"] for i in falso.itens.values() if merc[0]["id"] in i["parents"]}
conferir(filhos == {modelo.ORIGINACAO, modelo.APOLICES, modelo.FRENTES, "UTE-PILAR"}, f"com {sorted(filhos)}")
rel = auditoria.auditar_cliente("GRUPO-MERCURIO", drive.ler_arvore(falso, merc[0]["id"], incluir_arquivos=True))
conferir(not rel.erros and not rel.avisos, "e passa limpo na auditoria")

print("\n14. auditoria na tela")
status, a = chamar("/api/auditoria?alvo=GRUPO-DIAMANTE")
conferir(status == 200 and a["alvo"] == "GRUPO-DIAMANTE", "auditou o cliente")
por_grav = {g["gravidade"]: g for g in a["gravidades"]}
conferir(por_grav["ERRO"]["total"] == 0, "sem erro no exemplo")
familias_nota = {f["nome"] for f in por_grav["NOTA"]["familias"]}
conferir("Originação no modelo anterior" in familias_nota and "Tipo de cada frente" in familias_nota,
         f"notas agrupadas por família: {sorted(familias_nota)}")
familias_aviso = {f["nome"] for f in por_grav["AVISO"]["familias"]}
conferir("Ramo fora da lista da casa" not in familias_aviso and any(f["nome"] == "Ramo fora da lista da casa" for f in por_grav["NOTA"]["familias"]),
         "o ramo EQUIPAMENTOS aparece como nota, na família certa")
todas = [f for g in a["gravidades"] for f in g["familias"]]
conferir(all(f["conhecida"] for f in todas), "nenhuma mensagem caiu fora das famílias conhecidas: "
         + ", ".join(f["nome"] for f in todas if not f["conhecida"]))
status, a = chamar("/api/auditoria?alvo=" + mod["funil"])
conferir(status == 200 and a["alvo"] == "o funil", "auditou o funil")
avisos = {f["nome"] for f in {g["gravidade"]: g for g in a["gravidades"]}["AVISO"]["familias"]}
conferir("Originação parada" in avisos, "a originação de 2023 aparece como parada")
status, e = chamar("/api/auditoria?alvo=NAO-EXISTE")
conferir(status == 400 and "Não achei" in e["erro"], "cliente inexistente dá frase, não traceback")
status, e = chamar("/api/auditoria")
conferir(status == 400, "sem alvo, sem auditoria")

print("\n17. ativo novo em cliente que já existe")
diamante = pasta_chamada("GRUPO-DIAMANTE")[0]
antes = {i["id"] for i in falso.itens.values()}
orig_antes = sorted(i["name"] for i in falso.itens.values()
                    if any(p == o["id"] for o in pasta_chamada(modelo.ORIGINACAO) if diamante["id"] in o["parents"] for p in i["parents"]))
status, e = chamar("/api/ativo/plano", {"cliente": "GRUPO-DIAMANTE", "nome": "CTJL"})
conferir(status == 400 and "Já existe CTJL" in e["erro"], "ativo que já existe é recusado")
status, e = chamar("/api/ativo/plano", {"cliente": "GRUPO-DIAMANTE/CTJL", "nome": "Novo"})
conferir(status == 400 and "não dentro de outro ativo" in e["erro"], "ativo dentro de ativo é recusado")
status, e = chamar("/api/ativo/plano", {"cliente": "GRUPO-DIAMANTE", "nome": "Frentes"})
conferir(status == 400 and "nome de pasta do modelo" in e["erro"], "FRENTES não serve de nome de ativo")
status, e = chamar("/api/ativo/plano", {"cliente": "GRUPO-DIAMANTE", "nome": "Pecém II", "ramos": ["RO"]})
conferir(status == 400 and "RO-BI" in e["erro"], "ramo com nome antigo é recusado aqui também")
status, r = chamar("/api/ativo/plano", {"cliente": "GRUPO-DIAMANTE", "nome": "Pecém II", "ramos": ["RO-BI", "Garantia Judicial"],
                                         "frentes": [{"titulo": "Renovação RO", "competencia": "2026-09", "tipo": "RENOVACAO"}]})
conferir(status == 200 and r["plano"]["partes"][0]["linhas"][0].endswith("PECEM-II"), "o plano começa pelo ativo, na grafia da casa")
esperado = (1 + 1 + len(modelo.ACERVO_SUBPASTAS) + 1 + 2 * (1 + len(modelo.RAMO_SUBPASTAS)) + 1
            + 1 + len(modelo.TIPOS_FRENTE["RENOVACAO"]["subpastas"]))
conferir(r["plano"]["partes"][0]["total"] == esperado, f"conta ativo, acervo, dois ramos e a frente: {esperado} pastas")
conferir({i["id"] for i in falso.itens.values()} == antes, "pedir o plano não criou nada")
status, res = chamar("/api/executar", {"senha": r["senha"]})
pecem2 = [i for i in pasta_chamada("PECEM-II") if diamante["id"] in i["parents"]]
conferir(status == 200 and len(pecem2) == 1, "PECEM-II nasceu dentro de GRUPO-DIAMANTE")
conferir(pecem2[0]["appProperties"].get("vbr") == "vbr/GRUPO-DIAMANTE/PECEM-II", "etiquetado pelo caminho")
filhos = {i["name"] for i in falso.itens.values() if pecem2[0]["id"] in i["parents"]}
conferir(filhos == {modelo.ACERVO, modelo.APOLICES, modelo.FRENTES}, f"com {sorted(filhos)}")
novos = [falso.caminho_de(i["id"]) for i in falso.itens.values() if i["id"] not in antes]
conferir(all("/GRUPO-DIAMANTE/PECEM-II" in c for c in novos), "tudo que nasceu está dentro do ativo novo")
orig_depois = sorted(i["name"] for i in falso.itens.values()
                     if any(p == o["id"] for o in pasta_chamada(modelo.ORIGINACAO) if diamante["id"] in o["parents"] for p in i["parents"]))
conferir(orig_depois == orig_antes == sorted(modelo.ORIGINACAO_SUBPASTAS_ANTERIOR), "a originação de quatro do cliente ficou intacta")
status, d = chamar("/api/destinos")
conferir("GRUPO-DIAMANTE/PECEM-II" in [x["caminho"] for x in d["destinos"]], "o ativo novo aparece na lista de Clientes")
status, a = chamar("/api/auditoria?alvo=GRUPO-DIAMANTE")
conferir(not [i for g in a["gravidades"] if g["gravidade"] == "ERRO" for f in g["familias"] for i in f["itens"] if "PECEM-II" in i["caminho"]],
         "e passa sem erro na auditoria")

print("\n16. alinhar — uma frente atrás do modelo")
pecem_frentes = falso.semear("GESTAO DE RISCOS/CLIENTES/GRUPO-DIAMANTE/PECEM-I/FRENTES")
velha = falso._criar("2026-05_RENOVACAO-VELHA", pecem_frentes)
for sub in ("01-INSUMOS", "02-TRABALHOS", "03-ENTREGAS", "04-COTACOES-RECEBIDAS", "05-ANALISE-COMPARATIVA", "06-DECISAO-EMISSAO", "RASCUNHOS"):
    pid = falso._criar(sub, velha)
    if sub == "06-DECISAO-EMISSAO":
        id_da_06 = pid
        falso._criar("apolice emitida.pdf", pid, mime="application/pdf")
status, a = chamar("/api/auditoria?alvo=GRUPO-DIAMANTE")
achados = [i for g in a["gravidades"] for f in g["familias"] for i in f["itens"] if "RENOVACAO-VELHA" in i["caminho"]]
fora = [i for i in achados if "não bate" in i["mensagem"]]
conferir(len(fora) == 1 and "alinhar" in fora[0], "a auditoria oferece Alinhar na frente fora de tipo")
conferir(fora[0]["alinhar"]["tipo_proximo"] == "RENOVACAO" and "06-DECISAO-EMISSAO" in fora[0]["alinhar"]["presentes"],
         "com a forma mais próxima e o que a frente tem hoje")
caminho = fora[0]["alinhar"]["caminho"]
status, e = chamar("/api/alinhar/plano", {"caminho": "GRUPO-DIAMANTE/PECEM-I/ACERVO", "tipo": ""})
conferir(status == 400 and "FRENTES" in e["erro"], "caminho que não é de frente é recusado")
status, e = chamar("/api/alinhar/plano", {"caminho": "GRUPO-DIAMANTE/FRENTES/2026-07_RFP-CORRETORA"})
conferir(status == 400 and "já está na forma" in e["erro"], "frente já na forma: nada a fazer")
status, r = chamar("/api/alinhar/plano", {"caminho": caminho})
conferir(status == 200 and [p["rotulo"] for p in r["plano"]["partes"]] == ["RENOMEAR", "CRIAR"], "o plano tem renomear e criar")
conferir(r["plano"]["partes"][0]["linhas"] == ["06-DECISAO-EMISSAO  →  06-DECISAO-E-EMISSAO"] and r["plano"]["partes"][1]["linhas"] == ["07-COMUNICACOES"],
         "renomeia a 06 e cria a 07")
conferir(any("RASCUNHOS" in x for x in r["plano"]["avisos"]), "avisa que RASCUNHOS fica como está")
conferir(falso.itens[id_da_06]["name"] == "06-DECISAO-EMISSAO", "pedir o plano não renomeou nada")
status, res = chamar("/api/executar", {"senha": r["senha"]})
conferir(status == 200 and falso.itens[id_da_06]["name"] == "06-DECISAO-E-EMISSAO", "renomeou a 06 — mesma pasta, mesmo id")
conferir(any(i["name"] == "apolice emitida.pdf" and id_da_06 in i["parents"] for i in falso.itens.values()), "o arquivo continua dentro dela")
conferir(falso.itens[id_da_06]["appProperties"].get("vbr") == "vbr/GRUPO-DIAMANTE/PECEM-I/FRENTES/2026-05_RENOVACAO-VELHA/06-DECISAO-E-EMISSAO",
         "e ganhou a etiqueta pelo caminho novo")
nova07 = [i for i in falso.itens.values() if i["name"] == "07-COMUNICACOES" and velha in i["parents"]]
conferir(len(nova07) == 1, "criou a 07")
conferir(any(i["name"] == "RASCUNHOS" and velha in i["parents"] and not i["trashed"] for i in falso.itens.values()), "RASCUNHOS ficou")
conferir(any(p["marca"] == "~" for p in res["passos"]), "o passo de renome vem marcado com ~")
status, a = chamar("/api/auditoria?alvo=GRUPO-DIAMANTE")
depois = [i for g in a["gravidades"] for f in g["familias"] for i in f["itens"]
          if "RENOVACAO-VELHA" in i["caminho"] and "não bate" in i["mensagem"]]
conferir(len(depois) == 1 and "falta" not in depois[0]["mensagem"] and "sobra RASCUNHOS" in depois[0]["mensagem"],
         "na auditoria seguinte só sobra RASCUNHOS, que o alinhar deixa de propósito; nada falta")
status, r = chamar("/api/alinhar/plano", {"caminho": caminho, "tipo": "SINISTRO"})
conferir(status == 200 and r["plano"]["titulo"].endswith("SINISTRO"), "dá para forçar outra forma")

print("\n15. o programa de fundo, pela página — com um launchctl de mentira")
import tempfile
from pathlib import Path
from lancador import Lancador
class _Saida:
    def __init__(self, rc, stdout=""):
        self.returncode, self.stdout, self.stderr = rc, stdout, ""
_carregado = {"sim": False}
def _launchctl(cmd, **_):
    if cmd[1] == "bootstrap":
        _carregado["sim"] = True
        return _Saida(0)
    if cmd[1] == "bootout":
        rc = 0 if _carregado["sim"] else 3
        _carregado["sim"] = False
        return _Saida(rc)
    if cmd[1] == "print":
        return _Saida(0, "pid = 77") if _carregado["sim"] else _Saida(113)
    return _Saida(1)
_tmp = Path(tempfile.mkdtemp(prefix="vbr-tela-lanc-"))
(_tmp / "prog").mkdir()
tela.lancador = Lancador(porta, pasta=_tmp / "prog", casa=_tmp / "casa", executar=_launchctl, uid=501)

status, sis = chamar("/api/sistema")
conferir(status == 200 and sis["agente"]["instalado"] is False and sis["fundo"] is False, "sistema diz: não instalado, servidor aberto pelo atalho")
status, e = chamar("/api/desinstalar/plano", {})
conferir(status == 400 and "não está instalado" in e["erro"], "desinstalar sem instalar é recusado")
status, r = chamar("/api/instalar/plano", {})
conferir(status == 200 and any("LaunchAgents" in l for l in r["plano"]["partes"][0]["linhas"]), "o plano mostra onde o agente vai")
conferir(any("assume assim que" in a for a in r["plano"]["avisos"]), "avisa que o fundo assume quando o Terminal fechar")
conferir(not tela.lancador.plist.exists(), "pedir o plano não gravou nada")
status, res = chamar("/api/executar", {"senha": r["senha"]})
conferir(status == 200 and tela.lancador.plist.exists() and tela.lancador.atalho_web.exists(), "instalou: .plist e atalho gravados")
conferir("webloc" in res["mensagem"], "a mensagem diz como abrir a tela daqui em diante")
status, sis = chamar("/api/sistema")
conferir(sis["agente"]["rodando"] and sis["agente"]["pid"] == 77, "sistema diz: rodando")
status, r = chamar("/api/desinstalar/plano", {})
status, res = chamar("/api/executar", {"senha": r["senha"]})
conferir(status == 200 and not tela.lancador.plist.exists(), "desinstalou: .plist apagado")
conferir(any(p["marca"] == "-" for p in res["passos"]), "os passos marcam o que foi apagado")
import shutil as _sh; _sh.rmtree(_tmp)

srv.shutdown()
print("\n" + "=" * 60)
if FALHAS:
    print(f"{len(FALHAS)} falha(s):")
    for f in FALHAS:
        print(f"  - {f}")
    sys.exit(1)
print("tudo passou.")
