# -*- coding: utf-8 -*-
"""Fichas da mesa: pasta fichas/, escolha da ficha, gravação a cada mudança, conflito e atualização forçada.
Rode com:  python testes/test_fichas.py"""
import json
import os
import queue
import sys
import tempfile
import time
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import fichas_mesa  # noqa: E402
import grupo        # noqa: E402
import sessao       # noqa: E402

tmp = tempfile.mkdtemp()
grupo.Grupo.ARQ_GRUPO = os.path.join(tmp, "grupo.json")
sessao.Servidor.ARQ_SESSAO = os.path.join(tmp, "sessao.json")
sessao.PORTA_WEB, sessao.PORTA_ANUNCIO = 5795, 5796
BASE = "http://127.0.0.1:5795"
pasta = os.path.join(tmp, "fichas")


def http(caminho, corpo=None):
    dados = None if corpo is None else json.dumps(corpo).encode()
    with urllib.request.urlopen(urllib.request.Request(BASE + caminho, data=dados), timeout=10) as r:
        return json.loads(r.read().decode())


assert fichas_mesa.slug("Kauã Silva") == "kaua-silva" and fichas_mesa.slug("../x") == "x" and fichas_mesa.slug("???") == ""

srv = sessao.Servidor(5797, queue.Queue())
srv.fichas_arq = fichas_mesa.Fichas(pasta)
srv.iniciar()
time.sleep(0.3)
try:
    # os cinco arquivos nascem vazios; a lista sai em /api/sessao
    for n in ("bruno", "carol", "kaua", "enrico", "guidi"):
        assert os.path.exists(os.path.join(pasta, n + ".json")), n
    info = http("/api/sessao")
    assert [f["nome"] for f in info["fichas"]] == ["Bruno", "Carol", "Kaua", "Enrico", "Guidi"] and not any(f["tem"] for f in info["fichas"])

    # a Carol entra com a ficha dela
    # a ficha livre pede um código; quem escolhe primeiro vira o dono
    assert http("/api/oi", {"nome": "Carol", "id": "", "ficha": "carol"}) == {"erro": "ficha_codigo"}
    r = http("/api/oi", {"nome": "Carol", "id": "", "ficha": "carol", "codigo": "1234"})
    ident, chave = r["id"], r["chave"]
    assert r["ficha"] == "carol"
    b = http("/api/ficha-arq?id=%s&k=%s" % (ident, chave))
    assert b["ok"] and not b["existe"]

    # sem ficha ainda: o celular cria e devolve; vira carol.json
    ficha = {"identidade": {"nome": "Lyra", "player": "Carol", "nivel": 3}, "vida": {"atual": "20"}, "_salvo": 111}
    g = http("/api/ficha-salvar", {"id": ident, "chave": chave, "estado": ficha, "base": None})
    assert g["ok"] and g["ver"]
    em_disco = json.load(open(os.path.join(pasta, "carol.json"), encoding="utf-8"))
    assert em_disco["identidade"]["nome"] == "Lyra" and "_salvo" not in em_disco
    assert http("/api/sessao")["fichas"][1]["tem"] is True

    # cada mudança vira versão nova; quem tem a versão certa não é interrompido
    ficha["vida"]["atual"] = "12"
    g2 = http("/api/ficha-salvar", {"id": ident, "chave": chave, "estado": ficha, "base": g["ver"]})
    assert g2["ok"] and g2["ver"] != g["ver"]
    assert json.load(open(os.path.join(pasta, "carol.json"), encoding="utf-8"))["vida"]["atual"] == "12"
    est = http("/api/estado?id=%s&k=%s" % (ident, chave))
    assert est["fv"] == g2["ver"], est

    # o mestre muda o arquivo por fora: o estado do celular mostra versão nova e o celular baixa
    time.sleep(0.05)
    ficha["vida"]["atual"] = "30"
    with open(os.path.join(pasta, "carol.json"), "w", encoding="utf-8") as f:
        json.dump(ficha, f, ensure_ascii=False)
    est = http("/api/estado?id=%s&k=%s" % (ident, chave))
    assert est["fv"] != g2["ver"]
    b = http("/api/ficha-arq?id=%s&k=%s" % (ident, chave))
    assert b["existe"] and b["ficha"]["vida"]["atual"] == "30" and b["ver"] == est["fv"]

    # o celular ainda tinha a versão antiga: conflito (nada é sobrescrito sem querer)
    c = http("/api/ficha-salvar", {"id": ident, "chave": chave, "estado": ficha, "base": g2["ver"]})
    assert not c["ok"] and c.get("conflito") and c["ver"] == b["ver"]

    # "Atualizar minha ficha": força e guarda a anterior em backup
    nova = {"identidade": {"nome": "Lyra", "player": "Carol", "nivel": 4}}
    f1 = http("/api/ficha-salvar", {"id": ident, "chave": chave, "estado": nova, "base": g2["ver"], "forcar": True})
    assert f1["ok"]
    assert json.load(open(os.path.join(pasta, "carol.json"), encoding="utf-8"))["identidade"]["nivel"] == 4
    assert any(x.startswith("carol_antes_") for x in os.listdir(os.path.join(pasta, "backup")))

    # entrada sem ficha escolhida não grava nada; ficha inválida é recusada; outro jogador não mexe na ficha alheia
    r2 = http("/api/oi", {"nome": "Visita", "id": ""})
    assert http("/api/ficha-salvar", {"id": r2["id"], "chave": r2["chave"], "estado": nova})["ok"] is False
    assert http("/api/ficha-salvar", {"id": ident, "chave": chave, "estado": {"lixo": 1}})["ok"] is False
    assert http("/api/ficha-salvar", {"id": ident, "chave": "errada", "estado": nova}).get("ok") is False
    # só o mestre cria fichas: nome que não está na lista é recusado; depois de criada, entra
    assert http("/api/oi", {"nome": "Zé Maria", "id": "", "ficha": "Zé Maria"}) == {"erro": "ficha_inexistente"}
    assert srv.fichas_arq.criar("Zé Maria") == "ze-maria"
    r3 = http("/api/oi", {"nome": "Zé Maria", "id": "", "ficha": "Zé Maria", "codigo": "zzz"})
    assert r3["ficha"] == "ze-maria"
    assert http("/api/ficha-salvar", {"id": r3["id"], "chave": r3["chave"], "estado": nova})["ok"]
    assert os.path.exists(os.path.join(pasta, "ze-maria.json"))
    assert any(f["slug"] == "ze-maria" and f["tem"] for f in http("/api/sessao")["fichas"])
    # a ficha da Carol está em uso por ela; depois de sair, continua presa: só entra com o código dela
    assert http("/api/oi", {"nome": "Intruso", "id": "", "ficha": "carol", "codigo": "1234"}) == {"erro": "ficha_em_uso", "por": "Carol"}
    with srv.lock:
        srv.web["Carol"]["visto"] -= 60
    assert http("/api/oi", {"nome": "Intruso", "id": "", "ficha": "carol", "codigo": "9999"}) == {"erro": "ficha_presa"}
    volta = http("/api/oi", {"nome": "Carol", "id": "", "ficha": "carol", "codigo": "1234"})
    assert volta["ficha"] == "carol"
    lista = {f["slug"]: f for f in http("/api/sessao?id=" + urllib.parse.quote(volta["id"]))["fichas"]}
    assert lista["carol"]["presa"] and lista["carol"]["minha"] and lista["carol"]["personagem"] == "Lyra" and not lista["bruno"]["presa"]
    # o mestre libera: o próximo que escolher vira o dono; excluir manda para o backup (as de sempre só esvaziam)
    with srv.lock:
        srv.web[volta["id"]]["visto"] -= 60
    assert srv.fichas_arq.liberar("carol") and srv.fichas_arq.dono("carol") is None
    assert http("/api/oi", {"nome": "Novo", "id": "", "ficha": "carol", "codigo": "abc"})["ficha"] == "carol"
    assert srv.fichas_arq.excluir("ze-maria") and not os.path.exists(os.path.join(pasta, "ze-maria.json"))
    assert srv.fichas_arq.excluir("carol") and os.path.exists(os.path.join(pasta, "carol.json")) and srv.fichas_arq.dono("carol") is None
    # foto: sai em /api/foto e marca a lista
    foto = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    srv.fichas_arq.gravar("bruno", {"identidade": {"nome": "Brasa", "nivel": 2}, "foto": foto}, forcar=True)
    assert [f["foto"] for f in http("/api/sessao")["fichas"] if f["slug"] == "bruno"][0]
    with urllib.request.urlopen(BASE + "/api/foto?f=bruno") as resp:
        assert resp.headers["Content-Type"] == "image/png" and resp.read()[:4] == b"\x89PNG"
    # jogador do PC (conexão direta): lista, escolhe com código, salva, percebe a mudança do mestre e solta
    import socket
    c = socket.create_connection(("127.0.0.1", 5797), timeout=5)
    arq = c.makefile("r", encoding="utf-8", newline="\n")

    def pc(m=None, oi=None):
        c.sendall((json.dumps(oi or {"t": "fichas", "m": m}) + "\n").encode())
        while True:
            x = json.loads(arq.readline())
            if x.get("t") in ("ok", "fichas_resp"):
                return x.get("r", x)
    assert pc(oi={"t": "oi", "nome": "Dani"})["nome"] == "Dani"
    assert any(f["slug"] == "enrico" for f in pc({"acao": "listar"})["fichas"])
    assert pc({"acao": "escolher", "slug": "enrico"})["motivo"] == "ficha_codigo"
    e1 = pc({"acao": "escolher", "slug": "enrico", "codigo": "dd1"})
    assert e1["ok"] and not e1["existe"]
    g = pc({"acao": "salvar", "estado": {"identidade": {"nome": "Faísca", "nivel": 2}}, "base": None})
    assert g["ok"] and pc({"acao": "ver"})["ver"] == g["ver"]
    assert pc({"acao": "escolher", "slug": "bruno", "codigo": "x"})["motivo"] == "ficha_codigo"      # código curto demais
    assert srv.ficha_em_uso("enrico") == "Dani"
    srv.fichas_arq.gravar("enrico", {"identidade": {"nome": "Faísca", "nivel": 3}}, forcar=True)
    assert pc({"acao": "ver"})["ver"] != g["ver"] and pc({"acao": "baixar"})["ficha"]["identidade"]["nivel"] == 3
    assert pc({"acao": "salvar", "estado": {"identidade": {"nome": "Faísca", "nivel": 9}}, "base": g["ver"]}).get("conflito")
    assert pc({"acao": "soltar"})["ok"] and srv.ficha_em_uso("enrico") == ""
    c.close()
    print("ok")
finally:
    srv.parar()
