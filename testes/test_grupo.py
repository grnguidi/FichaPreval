# -*- coding: utf-8 -*-
"""Interação entre jogadores (grupo.py): pedidos com aceite, trocas, caixa, espólio, rolagens, teste em grupo e limites.
Rode com:  python testes/test_grupo.py   (precisa do tkinter só porque sessao.py importa a interface)."""
import os
import queue
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import grupo   # noqa: E402
import sessao  # noqa: E402

grupo.Grupo.ARQ_GRUPO = os.path.join(tempfile.mkdtemp(), "grupo.json")
s = sessao.Servidor(0, queue.Queue())
for n in ("Ana", "Beto", "Caio"):
    s.web_oi(n, "")


def ficha(vida):
    return {"personagem": "P", "nivel": 5, "vida": vida, "vida_max": 40, "condicoes": [["Veneno", 30, 100]], "portao": [1, 2],
            "iniciativa_dados": 1, "iniciativa": 2}


s.receber_ficha("Ana", ficha(40), web=True)
s.receber_ficha("Beto", ficha(0), web=True)
s.receber_ficha("Caio", ficha(20), web=True)
A = lambda n, **m: s.grupo_acao(n, m)                                   # noqa: E731
eventos = lambda n: [e for e in s.web_estado(n, 0)["eventos"]]          # noqa: E731
pedidos = lambda n: [p for p in s.grupo_estado(n)["propostas"] if p["para"] == n]   # noqa: E731

# painel e visibilidade
m = {x["nome"]: x for x in s.grupo_estado("Ana")["membros"]}
assert m["Beto"]["incapaz"] and m["Caio"]["vida"] == [20, 40]
A("Caio", acao="vis", modo="barra")
m = {x["nome"]: x for x in s.grupo_estado("Ana")["membros"]}
assert "vida" not in m["Caio"] and m["Caio"]["pct"] == 50
A("Caio", acao="vis", modo="nada")
assert "pct" not in {x["nome"]: x for x in s.grupo_estado("Ana")["membros"]}["Caio"]

# Medicina: só em quem está Incapaz, DT 15, e só vale depois do aceite
assert not A("Ana", acao="propor", tipo="medicina", para="Caio", total=20)["ok"]
assert A("Ana", acao="propor", tipo="medicina", para="Beto", total=9)["ok"] and not pedidos("Beto")
A("Ana", acao="propor", tipo="medicina", para="Beto", total=18)
p = pedidos("Beto")
assert len(p) == 1 and not any(e["tipo"] == "portao" for e in eventos("Beto"))
assert not A("Caio", acao="responder", num=p[0]["id"], aceitar=True)["ok"]      # só o destinatário responde
A("Beto", acao="responder", num=p[0]["id"], aceitar=True)
assert any(e["tipo"] == "portao" and e["sucesso"] == 1 for e in eventos("Beto"))

# item e dinheiro: sai de um, entra no outro; recusa não move nada
A("Ana", acao="propor", tipo="item", para="Caio", item={"item": "Poção", "carga": "1", "qtd": 2})
s.mestre_resolver(pedidos("Caio")[0]["id"], True)                                # o mestre pode aceitar por ele
assert any(e["tipo"] == "item" and e["acao"] == "tirar" for e in eventos("Ana"))
assert any(e["tipo"] == "item" and e["acao"] == "dar" for e in eventos("Caio"))
A("Ana", acao="propor", tipo="dinheiro", para="Caio", contos=50)
A("Caio", acao="responder", num=pedidos("Caio")[0]["id"], aceitar=False)
assert not any(e["tipo"] == "dinheiro" for e in eventos("Ana") + eventos("Caio"))

# caixa do grupo
A("Ana", acao="caixa", delta=120)
assert not A("Beto", acao="caixa", delta=-500)["ok"]
A("Beto", acao="caixa", delta=-20)
assert s.caixa["contos"] == 100

# rolagens: texto da rede é limpo
A("Ana", acao="rolagem", titulo="<i>Arco</i>", linhas=["Ataque: <b>25</b>", "<script>x</script>ok"], destaque=True)
f = s.grupo_estado("Beto")["feed"][0]
assert f["titulo"] == "Arco" and f["linhas"] == ["Ataque: 25", "xok"]
A("Beto", acao="reagir", seq=f["seq"], r="🎉")
assert s.grupo_estado("Ana")["feed"][0]["reacoes"] == {"🎉": ["Beto"]}

# teste em grupo: o resultado só aparece quando todos rolaram
s.pedir_teste("Furtividade", 15)
A("Ana", acao="teste_rolar", total=17)
assert s.grupo_estado("Beto")["teste"]["res"] == []
A("Beto", acao="teste_rolar", total=9)
A("Caio", acao="teste_rolar", total=22)
assert [r["nome"] for r in s.grupo_estado("Beto")["teste"]["res"]] == ["Caio", "Ana", "Beto"]

# sussurro: o mestre só vê que houve (padrão)
A("Ana", acao="sussurro", para="Beto", texto="psiu")
assert eventos("Beto")[-1]["texto"] == "psiu" and s.registro[0][1] == "Ana sussurrou para Beto"

# espólio: empate vai no d20; dinheiro dividido e resto na caixa
s.soltar_espolio([{"item": "Garra", "qtd": 1}], 101)
iid = s.grupo_estado("Ana")["espolio"]["itens"][0]["id"]
A("Ana", acao="espolio_quero", num=iid, quer=True)
A("Beto", acao="espolio_quero", num=iid, quer=True)
linhas = s.distribuir_espolio()
assert "disputa" in linhas[0] and s.caixa["contos"] == 102 and s.espolio is None

# o mestre desliga um recurso
s.grupo_config("ajuda", False)
assert not A("Ana", acao="propor", tipo="cura", para="Beto", valor=5)["ok"]
s.grupo_config("ajuda", True)

# quem não está na mesa, ou ação inventada, não passa
assert not A("Zé", acao="vis", modo="tudo")["ok"] and not A("Ana", acao="__init__")["ok"]

# caixa, diário e vínculos ficam guardados entre as sessões
A("Ana", acao="vinculo", com="Beto", texto="Irmãos de armas")
A("Ana", acao="nota_add", texto="Chegamos ao Andar 2")
s2 = sessao.Servidor(0, queue.Queue())
assert s2.caixa["contos"] == 102 and len(s2.notas) == 1 and s2.vinculos == {"Ana|Beto": "Irmãos de armas"}
print("ok")
