import sys, queue
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sessao
s = sessao.Servidor(0, queue.Queue())
n = s.web_oi("Ana", "")
s.enviar_dano([n], 5, "Fogo", "x")
s.enviar_dano([n], 3, "Fogo", "y")
r1 = s.web_estado(n, 0)
assert [e["seq"] for e in r1["eventos"]] == [1, 2], r1
r2 = s.web_estado(n, 0)            # resposta perdida: reenvia
assert len(r2["eventos"]) == 2
r3 = s.web_estado(n, 2)            # confirmou
assert r3["eventos"] == []
s.enviar_dano([n], 1, "", "z")
assert [e["seq"] for e in s.web_estado(n, 2)["eventos"]] == [3]
assert len(s.web_estado(n)["eventos"]) == 1   # sem ack: esvazia (página antiga)
assert s.web_estado(n)["eventos"] == []
# limpeza de quem saiu
s.ordem = [[n, 10, 0], ["Bia", 5, 0]]; s.vez = 1
s.receber_ficha(n, {"vida": 3}, web=True); s.efeitos[n] = [1]
s.enviar_dano([n], 1, "", "z")
s.web[n]["visto"] -= sessao.SAI_DA_MESA + 5
s._varrer()
assert n not in s.web and n not in s.pendentes and n not in s.efeitos and n not in s.fichas
assert [o[0] for o in s.ordem] == ["Bia"] and s.vez == 0, (s.ordem, s.vez)
print("ok")
