# -*- coding: utf-8 -*-
"""Painel do mestre: números do bestiário, biblioteca de inimigos, anotações, combate (dano, Postura, condições) e a ligação com a sessão.
Rode com:  python testes/test_mestre.py"""
import json
import os
import queue
import sys
import tempfile
import threading
import time
import urllib.request
from http.server import ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import bestiario as B       # noqa: E402
import fichas_mesa          # noqa: E402
import grupo                # noqa: E402
import mestre_dados         # noqa: E402
import mestre_web           # noqa: E402
import sessao               # noqa: E402

# --- números do livro (exemplo do capítulo: Animal, 4 jogadores, NMP 10)
c = B.calcular("Animal", 10, 4)
assert (c["vida"], c["ca"], c["ataque"], c["dt"], c["dano_turno"], c["golpes"]) == (2280, 19, 10, 19, 144, 2), c
assert B.vida_de_condicao("Animal", 12, 5) == 156 and B.recarga_apos_ativar(156, 1) == 234     # Rainha do Crepúsculo
assert B.vida_de_condicao("Forte", 12, 5) == 100 and B.vida_de_condicao("Comum", 9, 4) == 55
assert B.calcular("Lacaio", 1, 4)["vida"] == 30 and B.calcular("Lacaio", 1, 4)["golpes"] == 1
assert B.calcular("Deus", 10, 8)["vida"] == 95 * 36 * 2 and B.calcular("Deus", 10, 4)["postura"] == -(-95 * 36 // 4)
assert 60 < B.calcular("Comum", 3, 4)["vida"] < 6 * 60       # entre as linhas 1 e 5

# --- iniciativa do livro: 1d20 (+1d20 a cada 20 de DES), o maior, + bônus; empate rola de novo; primeiro atacante tem vantagem
import regras as R  # noqa: E402
fila = iter([10, 4, 17, 16, 9, 15, 8, 8, 8, 8, 8, 8])
ordem, det = R.rolar_ordem_iniciativa([{"nome": "A", "dados": 2, "bonus": 3}, {"nome": "B", "dados": 1, "bonus": 0}, {"nome": "C", "dados": 1, "bonus": 1}],
                                      lambda f: next(fila))
assert det["A"]["rolos"] == [10, 4] and det["A"]["total"] == 13               # fica o maior dado e soma o bônus
assert det["B"]["rodadas"] == 2 and det["C"]["rodadas"] == 2 and det["A"]["rodadas"] == 1      # B e C empataram em 17 e rolaram de novo
assert [o[1] for o in ordem] == sorted([o[1] for o in ordem], reverse=True) and len({o[1] for o in ordem}) == 3
ordem2, det2 = R.rolar_ordem_iniciativa([{"nome": "P", "dados": 1, "bonus": 0}, {"nome": "Q", "dados": 1, "bonus": 0}], lambda f: 7, primeiro="P")
assert len(det2["P"]["rolos"]) == 2 and len(det2["Q"]["rolos"]) == 1             # vantagem: o dobro de dados
assert len({o[1] for o in ordem2}) in (1, 2) and [o[0] for o in ordem2] == ["P", "Q"]    # sem solução: desempata por bônus e nome
assert R.derivadas({k: 40 for k in R.ATRIBUTOS}, 5, {"Animado"}, 30)["iniciativa_dados"] == 4    # DES 40 -> 3d20, +1d20 do talento Animado

tmp = tempfile.mkdtemp()
grupo.Grupo.ARQ_GRUPO = os.path.join(tmp, "grupo.json")
sessao.Servidor.ARQ_SESSAO = os.path.join(tmp, "sessao.json")
sessao.PORTA_WEB, sessao.PORTA_ANUNCIO = 5805, 5806

m = mestre_dados.Mestre(os.path.join(tmp, "mestre"), rng=lambda a, b: 12)
mestre_web._unico["mestre"] = m


class _H(mestre_web._Painel):
    pass


_H.m = m
httpd = ThreadingHTTPServer(("127.0.0.1", 5807), _H)
threading.Thread(target=httpd.serve_forever, daemon=True).start()
BASE = "http://127.0.0.1:5807"


def http(caminho, corpo=None):
    dados = None if corpo is None else json.dumps(corpo).encode()
    with urllib.request.urlopen(urllib.request.Request(BASE + caminho, data=dados), timeout=10) as r:
        return json.loads(r.read().decode())


try:
    # página e configuração
    with urllib.request.urlopen(BASE + "/", timeout=10) as r:
        assert "Painel do mestre" in r.read().decode()
    cfg = http("/api/config")
    assert cfg["tiers"][0] == "Lacaio" and "Glacial" in cfg["tipos_dano"] and "Veneno" in cfg["condicoes"]
    assert http("/api/calcular?tier=Animal&nmp=10&jog=4")["vida"] == 2280

    # biblioteca: cria pelo livro e completa à mão
    base = http("/api/calcular?tier=Forte&nmp=6&jog=4")
    r = http("/api/inimigos", {"nome": "Lobo do Crepúsculo", "tier": "Forte", "nmp": 6, "jogadores": 4, "vida": base["vida"], "ca": base["ca"],
                               "ataque": base["ataque"], "dt": base["dt"], "postura": base["postura"], "vida_condicao": base["vida_condicao"],
                               "cond_por_golpe": base["cond_por_golpe"], "resistencias": ["Cortante"], "imunidades": ["Veneno"], "vulnerabilidades": ["Fogo"],
                               "afinidades": {"Loucura": "vulneravel", "Congelamento": "resistente", "Veneno": "imune", "Lixo": "x"},
                               "golpes": [{"nome": "Mordida", "tipo": "Perfurante", "bonus": base["ataque"], "dano": 40, "cond": "Sangramento", "cond_pts": 20}],
                               "habilidades": [{"nome": "Uivo", "acao": "Bônus", "texto": "Todos testam Vontade."}], "pontos_chave": [{"nome": "Garganta", "efeito": "+1 dado"}]})
    lobo = r["item"]
    assert lobo["id"] and lobo["afinidades"] == {"Loucura": "vulneravel", "Congelamento": "resistente", "Veneno": "imune"}
    assert [x["nome"] for x in http("/api/inimigos")["itens"]] == ["Lobo do Crepúsculo"]
    assert json.load(open(os.path.join(tmp, "mestre", "inimigos.json"), encoding="utf-8"))["itens"][0]["id"] == lobo["id"]

    # anotações
    n = http("/api/notas", {"titulo": "Ato 1", "etiqueta": "Enredo", "texto": "O vilão é o prefeito.", "fixa": True})["item"]
    n2 = http("/api/notas", {"id": n["id"], "titulo": "Ato 1", "texto": "mudou"})["item"]
    assert n2["id"] == n["id"] and len(http("/api/notas")["itens"]) == 1 and http("/api/notas")["itens"][0]["texto"] == "mudou"

    # combate só com inimigos (sem sessão)
    novos = http("/api/combate/adicionar", {"itens": [{"id": lobo["id"], "qtd": 2}]})["novos"]
    assert novos == ["Lobo do Crepúsculo 1", "Lobo do Crepúsculo 2"], novos
    e = http("/api/estado")
    assert e["sessao"] is False and len(e["inimigos"]) == 2
    a, b = e["inimigos"]
    vida0 = a["vida_max"]
    assert a["cond"]["Loucura"]["max"] == base["vida_condicao"] // 2 and a["cond"]["Congelamento"]["max"] == base["vida_condicao"] * 2
    # dano: resistência (metade), vulnerabilidade (+50%), imunidade (zero), Direto ignora tudo
    assert http("/api/combate/dano", {"iid": a["iid"], "valor": 20, "tipo": "Cortante"})["dano"] == 10
    assert http("/api/combate/dano", {"iid": a["iid"], "valor": 20, "tipo": "Fogo"})["dano"] == 30
    assert http("/api/combate/dano", {"iid": a["iid"], "valor": 20, "tipo": "Veneno"})["dano"] == 0
    assert http("/api/combate/dano", {"iid": a["iid"], "valor": 20, "tipo": "Cortante", "direto": True})["dano"] == 20
    # Postura: corpo a corpo reduz, quebra ao zerar (Exposto) e recarrega
    r = http("/api/combate/dano", {"iid": b["iid"], "valor": b["postura_max"], "tipo": "", "corpo": True})
    bb = next(x for x in http("/api/estado")["inimigos"] if x["iid"] == b["iid"])
    assert bb["exposto"] and bb["postura"] == bb["postura_max"] and any("POSTURA" in x for x in r["notas"]), (bb, r)
    # condições: afinidades, ativação com efeito e recarga (+50%)
    aa = lambda: next(x for x in http("/api/estado")["inimigos"] if x["iid"] == a["iid"])
    assert http("/api/combate/condicao", {"iid": a["iid"], "cond": "Veneno", "pontos": 999})["ativou"] is False     # imune
    vida_antes = aa()["vida"]
    r = http("/api/combate/condicao", {"iid": a["iid"], "cond": "Sangramento", "pontos": 999})
    assert r["ativou"] and aa()["vida"] == vida_antes - int(vida0 * 25 / 100), (aa()["vida"], vida_antes)
    assert aa()["cond"]["Sangramento"]["atual"] == int(round(base["vida_condicao"] * 1.5))
    http("/api/combate/condicao", {"iid": a["iid"], "cond": "Podridão", "pontos": 999})
    assert aa()["dots"] and aa()["dots"][0]["cond"] == "Podridão"
    # cura, ponto chave, edição
    assert http("/api/combate/cura", {"iid": a["iid"], "valor": 5})["ok"]
    assert http("/api/combate/ponto-chave", {"iid": a["iid"], "idx": 0, "revelado": True})["ok"] and aa()["pontos_chave"][0]["revelado"]
    assert http("/api/combate/editar", {"iid": a["iid"], "campos": {"nome": "Alfa", "ini": 15}})["ok"] and aa()["nome"] == "Alfa"

    # iniciativa e turnos locais (os inimigos rolam 1d20; o teste fixa o dado em 12)
    http("/api/combate/iniciativa", {})
    e = http("/api/estado")
    assert [o[0] for o in e["ordem"]] and e["vez"] == 0, e["ordem"]
    pv = aa()["vida"]
    http("/api/combate/passar", {})
    http("/api/combate/passar", {})        # o turno do Alfa chega: a Podridão tira Vida
    assert aa()["vida"] < pv or e["ordem"][0][0] != "Alfa"
    # só ações permitidas e só neste computador
    assert http("/api/jogador/dano", {"alvos": ["x"], "valor": 3})["ok"] is False
    req = urllib.request.Request(BASE + "/api/estado", headers={"Host": "meu-site.exemplo.com"})
    try:
        urllib.request.urlopen(req, timeout=5)
        raise AssertionError("aceitou Host de fora")
    except urllib.error.HTTPError as ex:
        assert ex.code == 403
    http("/api/combate/remover", {"iid": b["iid"]})
    assert len(http("/api/estado")["inimigos"]) == 1

    # ------------------------------------------------ com a sessão aberta
    srv = sessao.Servidor(5809, queue.Queue())
    srv.fichas_arq = fichas_mesa.Fichas(os.path.join(tmp, "fichas"))
    srv.iniciar()
    time.sleep(0.2)
    try:
        assert sessao.SERVIDOR_ATIVO is srv
        oi = srv.web_entrar("Carol", "", ficha="carol")
        srv.receber_ficha("Carol", {"personagem": "Lyra", "nivel": 5, "vida": 40, "vida_max": 51, "ca": 12, "iniciativa": 3, "iniciativa_dados": 1}, web=True)
        e = http("/api/estado")
        assert e["sessao"] and e["jogadores"][0]["nome"] == "Carol" and e["jogadores"][0]["ficha"]["vida"] == 40 and e["nmp"] == 5
        assert http("/api/jogador/dano", {"alvos": ["Carol"], "valor": 15, "tipo": "Glacial", "desc": "Lobo"})["ok"]
        ev = srv.web_estado("Carol", 0)["eventos"][0]
        assert ev["tipo"] == "dano" and ev["valor"] == 15 and ev["dano_tipo"] == "Glacial", ev
        assert http("/api/jogador/efeito", {"alvos": ["Carol"], "nome": "Abalado", "rodadas": 2})["ok"]
        assert http("/api/estado")["jogadores"][0]["efeitos"][0]["nome"] == "Abalado"
        assert http("/api/jogador/pontos", {"alvos": ["Carol"], "cond": "Sangramento", "pontos": 20, "dt": 15})["ok"]
        # a iniciativa junta jogadores e inimigos na ordem da sessão, e passar o turno chama o gancho dos inimigos
        http("/api/combate/adicionar", {"itens": [{"id": lobo["id"], "qtd": 1}]})
        http("/api/combate/iniciativa", {})
        nomes = [o[0] for o in srv.ordem]
        assert "Carol" in nomes and any(n.startswith("Lobo") or n == "Alfa" for n in nomes), nomes
        for _ in range(len(nomes) + 1):
            http("/api/combate/passar", {})
        assert srv.rodada >= 2
        http("/api/combate/encerrar", {})
        assert srv.ordem == [] and http("/api/estado")["inimigos"] == []
        # Iniciar combate: escolhe inimigos e quantidade, rola tudo e monta a tabela; o primeiro atacante abre o combate
        srv.receber_ficha("Carol", {"personagem": "Lyra", "nivel": 5, "vida": 40, "vida_max": 51, "ca": 12, "iniciativa": 3, "iniciativa_dados": 2}, web=True)
        r = http("/api/combate/iniciar", {"itens": [{"id": lobo["id"], "qtd": 3}], "jogadores": ["Carol"], "primeiro": "Carol"})
        assert r["ok"] and r["novos"] == ["Lobo do Crepúsculo 1", "Lobo do Crepúsculo 2", "Lobo do Crepúsculo 3"], r
        e = http("/api/estado")
        assert sorted(o[0] for o in e["ordem"]) == ["Carol", "Lobo do Crepúsculo 1", "Lobo do Crepúsculo 2", "Lobo do Crepúsculo 3"], e["ordem"]
        assert e["abertura"] == "Carol" and e["vez"] == -1 and len(e["detalhe"]["Carol"]["rolos"]) == 4      # vantagem: 2d20 × 2
        assert len({o[1] for o in e["ordem"]}) == 4 and all(x["ini"] is not None for x in e["inimigos"])        # valores únicos
        assert srv._quem_age() == "Carol"
        http("/api/combate/passar", {})
        assert http("/api/estado")["vez"] == 0           # depois da abertura, a tabela começa pelo maior
        # inimigo derrotado é pulado; quem chega com o combate rolando entra na ordem
        primeiro_inimigo = next(x for x in http("/api/estado")["inimigos"] if x["nome"] == http("/api/estado")["ordem"][1][0]) if http("/api/estado")["ordem"][1][0].startswith("Lobo") else None
        if primeiro_inimigo:
            http("/api/combate/editar", {"iid": primeiro_inimigo["iid"], "campos": {"caido": True}})
        http("/api/combate/adicionar", {"itens": [{"id": lobo["id"], "qtd": 1}]})
        assert len(srv.ordem) == 5, srv.ordem
        http("/api/combate/encerrar", {})
    finally:
        srv.parar()
    assert sessao.SERVIDOR_ATIVO is None
    print("ok")
finally:
    httpd.shutdown()