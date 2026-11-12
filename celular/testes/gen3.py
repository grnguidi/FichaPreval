"""Casos para as regras novas (dano, condições, descanso, Arcano, carga). Compara com cmp3.js."""
import json, os, random, sys
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(AQUI, ".."), os.path.join(AQUI, "..", "..")]
import regras as R  # noqa: E402
import build  # noqa: E402
from dados_prevalecentes import DADOS  # noqa: E402

open(os.path.join(AQUI, "regras_montado.js"), "w", encoding="utf-8").write(build.regras_js())
rnd = random.Random(7)
descs = [v["descricao"] for e in DADOS["encantamentos"] for v in e["versoes"]]
casos = []
for _ in range(3000):
    fila = [rnd.randint(1, 20) for _ in range(12)]
    it = iter(fila)
    rng = lambda f, it=it: (next(it) - 1) % f + 1  # noqa: E731
    d = {"rd": rnd.randint(0, 4), "resistencias": rnd.sample([x[1] for x in R.RESISTENCIAS], rnd.randint(0, 3))}
    valor, tipo = rnd.randint(-5, 80), rnd.choice(R.NOMES_DANO + [""])
    frag, louc = rnd.random() < .2, rnd.random() < .2
    dano = R.defesas_contra_dano(valor, tipo, d, rng, frag, louc)
    ac, mx, pts, suc = rnd.randint(0, 120), rnd.choice([0, 100, 60]), rnd.randint(0, 90), rnd.random() < .5
    maxs = {"vida": rnd.randint(1, 300), "mana": rnd.randint(0, 200), "vigor": rnd.randint(1, 150)}
    ats = {k: rnd.randint(0, v) for k, v in maxs.items()}
    conds = {c: rnd.randint(0, 100) for c in rnd.sample(R.CONDICOES, 3)}
    tipo_d = rnd.choice(["curto", "longo"])
    desc = rnd.choice(descs)
    arc = rnd.randint(0, 99)
    enc = [[e, c, R.escalar_arcano(e, arc, c)] for e, c in R.condicoes_do_encantamento(desc)]
    pecas = {p: ({"set": rnd.choice(["", "Predador"]), "nome": rnd.choice(["", "x"])}) for p in ("Capacete", "Peitoral", "Manopla", "Calça", "Bota", "Arma")}
    inv = [{"item": rnd.choice(["Mochila", "Tocha", "mochila", "Corda"]), "carga": rnd.choice(["1", "2,5", "", "x"]), "qtd": rnd.choice(["", "3", "0", "a"])} for _ in range(rnd.randint(0, 4))]
    casos.append({"fila": fila, "d": d, "valor": valor, "tipo": tipo, "frag": frag, "louc": louc, "dano": list(dano),
                  "cond": [ac, mx, pts, suc, list(R.receber_condicao(ac, mx, pts, suc))],
                  "desc_tipo": tipo_d, "maxs": maxs, "ats": ats, "conds": conds, "descanso": list(R.descanso(tipo_d, maxs, ats, conds)),
                  "nv": rnd.randint(1, 30), "cv": rnd.randint(0, 60), "desc": desc, "arc": arc, "enc": enc,
                  "pecas": pecas, "peso_set": R.peso_pecas_set(pecas), "inv": inv, "extra": R.carga_extra_itens(inv, DADOS["itens"]),
                  "peso_inv": R.peso_inventario(inv)})
    casos[-1]["pocao"] = R.pocao_espiritual_dados(casos[-1]["nv"], casos[-1]["cv"])
json.dump({"casos": casos, "itens": DADOS["itens"]}, open(os.path.join(AQUI, "casos3.json"), "w", encoding="utf-8"), ensure_ascii=False)
print(len(casos), "casos")
